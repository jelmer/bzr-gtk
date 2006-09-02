# Copyright (C) 2006 by Szilveszter Farkas (Phanatic) <szilveszter.farkas@gmail.com>
# Some parts of the code are:
# Copyright (C) 2005, 2006 by Canonical Ltd
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import bzrlib.errors as errors

from bzrlib.workingtree import WorkingTree

from errors import ConnectionError, NoLocationKnown, NotBranchError

def missing(branch, other_branch=None, reverse=False):
    """ Get the number of missing or extra revisions of local branch.
    
    :param branch: path to local branch
    
    :param other_branch: location of the other branch
    
    :param reverse: reverse the order of revisions
    
    :return: number of missing revisions (if < 0, then extra revisions * -1)
    """
    import bzrlib
    from bzrlib.missing import find_unmerged
    
    try:
        local_branch = bzrlib.branch.Branch.open_containing(branch)[0]
    except errors.NotBranchError:
        raise NotBranchError(branch)
    except:
        raise
    
    parent = local_branch.get_parent()
    if other_branch is None:
        other_branch = parent
        if other_branch is None:
            raise NoLocationKnown
    
    try:
        remote_branch = bzrlib.branch.Branch.open(other_branch)
    except errors.NotBranchError:
        raise NotBranchError(other_branch)
    except errors.ConnectionError:
        raise ConnectionError(other_branch)
    except:
        raise
    
    if remote_branch.base == local_branch.base:
        remote_branch = local_branch
    local_branch.lock_read()

    ret = 0

    try:
        remote_branch.lock_read()
        try:
            local_extra, remote_extra = find_unmerged(local_branch, remote_branch)

            if reverse is False:
                local_extra.reverse()
                remote_extra.reverse()

            if local_extra:
                ret = len(local_extra) * -1

            if remote_extra:
                ret = len(remote_extra)

            if not remote_extra and not local_extra:
                ret = 0

        finally:
            remote_branch.unlock()
    finally:
        local_branch.unlock()

    if not ret and parent is None and other_branch is not None:
        local_branch.lock_write()
        try:
            # handle race conditions - a parent might be set while we run.
            if local_branch.get_parent() is None:
                local_branch.set_parent(remote_branch.base)
        finally:
            local_branch.unlock()
    
    return ret


def pull(branch, location=None, remember=False, overwrite=False, revision=None):
    """ Pull revisions from another branch.
    
    :param branch: the local branch where you want to pull
    
    :param location: location of branch you'd like to pull from (can be a bundle, too)
    
    :param remeber: if True, the location will be stored
    
    :param overwrite: if True, forget local changes, and update the branch to match the remote one
    
    :param revision: if specified, only the given revision will be pulled (revno)
    
    :return: number of revisions pulled
    """
    nobundle = False
    
    from bzrlib.branch import Branch
    try:
        from bzrlib.bundle import read_bundle_from_url
        from bzrlib.bundle.apply_bundle import install_bundle
    except ImportError:
        # no bundle support
        nobundle = True
    
    try:
        tree_to = WorkingTree.open_containing(branch)[0]
        branch_to = tree_to.branch
    except errors.NoWorkingTree:
        tree_to = None
        try:
            branch_to = Branch.open_containing(branch)[0]
        except errors.NotBranchError:
            raise NotBranchError(location)
    except errors.NotBranchError:
        raise NotBranchError(location)

    reader = None
    if location is not None and not nobundle:
        try:
            reader = read_bundle_from_url(location)
        except errors.NotABundle:
            pass # Continue on considering this url a Branch

    stored_loc = branch_to.get_parent()
    if location is None:
        if stored_loc is None:
            raise NoLocationKnown
        else:
            location = stored_loc

    if reader is not None and not nobundle:
        install_bundle(branch_to.repository, reader)
        branch_from = branch_to
    else:
        branch_from = Branch.open(location)

        if branch_to.get_parent() is None or remember:
            branch_to.set_parent(branch_from.base)

    rev_id = None
    
    if revision is not None:
        rev_id = branch_from.get_rev_id(revision)
    else:
        if reader is not None:
            rev_id = reader.info.target
        
    old_rh = branch_to.revision_history()
    if tree_to is not None:
        count = tree_to.pull(branch_from, overwrite, rev_id)
    else:
        count = branch_to.pull(branch_from, overwrite, rev_id)
    
    return count

def update(location):
    """ Update a tree to have the latest code committed to its branch.
    
    :param location: the path to the branch/working tree
    
    :return: None if tree is up to date, 1 if there are conflicts, 0 if updated without having conflicts
    """
    tree = WorkingTree.open_containing(location)[0]
    tree.lock_write()
    try:
        if tree.last_revision() == tree.branch.last_revision():
            # may be up to date, check master too.
            master = tree.branch.get_master_branch()
            if master is None or master.last_revision == tree.last_revision():
                # tree is up to date.
                return None
        conflicts = tree.update()
        if conflicts != 0:
            return 1
        else:
            return 0
    finally:
        tree.unlock()
