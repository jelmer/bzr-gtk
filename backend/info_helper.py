# Copyright (C) 2006 by Szilveszter Farkas (Phanatic)
# Some parts of the code are:
# Copyright (C) 2005, 2006 by Canonical Ltd

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import time

import bzrlib.diff as diff
import bzrlib.osutils as osutils

from bzrlib.info import _repo_relpath
from bzrlib.missing import find_unmerged

def get_location_info(repository, branch=None, working=None):
    """ Get known locations for working, branch and repository.
    
    :return: a dictionary containing the needed infos
    """
    ret = {}
    repository_path = repository.bzrdir.root_transport.base
    if working and branch:
        working_path = working.bzrdir.root_transport.base
        branch_path = branch.bzrdir.root_transport.base
        if working_path != branch_path:
            # lightweight checkout
            ret['lightcoroot'] = working_path
            if repository.is_shared():
                # lightweight checkout of branch in shared repository
                ret['sharedrepo'] = repository_path
                ret['repobranch'] = _repo_relpath(repository_path, branch_path)
            else:
                # lightweight checkout of standalone branch
                ret['cobranch'] = branch_path
        elif repository.is_shared():
            # branch with tree inside shared repository
            ret['sharedrepo'] = repository_path
            ret['repoco'] = _repo_relpath(repository_path, branch_path)
        elif branch.get_bound_location():
            # normal checkout
            ret['coroot'] = working_path
            ret['cobranch'] = branch.get_bound_location()
        else:
            # standalone
            ret['branchroot'] = working_path
    elif branch:
        branch_path = branch.bzrdir.root_transport.base
        if repository.is_shared():
            # branch is part of shared repository
            ret['sharedrepo'] = repository_path
            ret['repobranch'] = _repo_relpath(repository_path, branch_path)
        else:
            # standalone branch
            ret['branchroot'] = branch_path
    else:
        # shared repository
        assert repository.is_shared()
        ret['sharedrepo'] = repository_path
    
    return ret

def get_related_info(branch):
    """ Get parent and push location of branch.
    
    :return: a dictionary containing the needed infos
    """
    ret = {}
    if branch.get_parent() or branch.get_push_location():
        if branch.get_parent():
            ret['parentbranch'] = branch.get_parent()
        if branch.get_push_location():
            ret['publishbranch'] = branch.get_push_location()
    
    return ret


def get_format_info(control=None, repository=None, branch=None, working=None):
    """ Get known formats for control, working, branch and repository.
    
    :return: a dictionary containing the needed infos
    """
    ret = {}
    if control:
        ret['control'] = control._format.get_format_description()
    if working:
        ret['workingtree'] = working._format.get_format_description()
    if branch:
        ret['branch'] = branch._format.get_format_description()
    if repository:
        ret['repository'] = repository._format.get_format_description()
    
    return ret


def get_locking_info(repository, branch=None, working=None):
    """ Get locking status of working, branch and repository.
    
    :return: a dictionary containing the needed infos
    """
    ret = {}
    if (repository.get_physical_lock_status() or
        (branch and branch.get_physical_lock_status()) or
        (working and working.get_physical_lock_status())):
        if working:
            if working.get_physical_lock_status():
                status = 'locked'
            else:
                status = 'unlocked'
            ret['workingtree'] = status
        if branch:
            if branch.get_physical_lock_status():
                status = 'locked'
            else:
                status = 'unlocked'
            ret['branch'] = status
        if repository:
            if repository.get_physical_lock_status():
                status = 'locked'
            else:
                status = 'unlocked'
            ret['repository'] = status
    
    return ret

def get_missing_revisions_branch(branch):
    """ Get missing master revisions in branch.
    
    :return: a dictionary containing the needed infos
    """
    ret = {}
    # Try with inaccessible branch ?
    master = branch.get_master_branch()
    if master:
        local_extra, remote_extra = find_unmerged(branch, master)
        if remote_extra:
            ret['missing'] = len(remote_extra)
    
    return ret


def get_missing_revisions_working(working):
    """ Get missing revisions in working tree.
    
    :return: a dictionary containing the needed infos
    """
    ret = {}
    branch = working.branch
    basis = working.basis_tree()
    work_inv = working.inventory
    delta = diff.compare_trees(basis, working, want_unchanged=True)
    history = branch.revision_history()
    tree_last_id = working.last_revision()

    if len(history) and tree_last_id != history[-1]:
        tree_last_revno = branch.revision_id_to_revno(tree_last_id)
        missing_count = len(history) - tree_last_revno
        ret['missing'] = missing_count
    
    return ret


def get_working_stats(working):
    """ Get statistics about a working tree.
    
    :return: a dictionary containing the needed infos
    """
    ret = {}
    basis = working.basis_tree()
    work_inv = working.inventory
    delta = diff.compare_trees(basis, working, want_unchanged=True)

    ret['unchanged'] = len(delta.unchanged)
    ret['modified'] = len(delta.modified)
    ret['added'] = len(delta.added)
    ret['removed'] = len(delta.removed)
    ret['renamed'] = len(delta.renamed)

    ignore_cnt = unknown_cnt = 0
    for path in working.extras():
        if working.is_ignored(path):
            ignore_cnt += 1
        else:
            unknown_cnt += 1
    ret['unknown'] = unknown_cnt
    ret['ignored'] = ignore_cnt

    dir_cnt = 0
    for file_id in work_inv:
        if work_inv.get_file_kind(file_id) == 'directory':
            dir_cnt += 1
    ret['subdirs'] = dir_cnt

    return ret

def get_branch_stats(branch):
    """ Get statistics about a branch.
    
    :return: a dictionary containing the needed infos
    """
    ret = {}
    repository = branch.repository
    history = branch.revision_history()

    revno = len(history)
    ret['revno'] = revno 
    committers = {}
    for rev in history:
        committers[repository.get_revision(rev).committer] = True
    ret['commiters'] = len(committers)
    if revno > 0:
        firstrev = repository.get_revision(history[0])
        age = int((time.time() - firstrev.timestamp) / 3600 / 24)
        ret['age'] = age
        ret['firstrev'] = osutils.format_date(firstrev.timestamp,
                                              firstrev.timezone)

        lastrev = repository.get_revision(history[-1])
        ret['lastrev'] = osutils.format_date(lastrev.timestamp,
                                             lastrev.timezone)

    return ret

def get_repository_stats(repository):
    """ Get statistics about a repository.
    
    :return: a dictionary containing the needed infos
    """
    ret = {}
    if repository.bzrdir.root_transport.listable():
        c, t = repository._revision_store.total_size(repository.get_transaction())
        ret['revisions'] = c
        ret['size'] = t

    return ret
