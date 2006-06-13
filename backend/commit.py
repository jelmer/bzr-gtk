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

import codecs

import bzrlib
import bzrlib.errors as errors

from errors import (EmptyMessageError, NoMessageNoFileError,
                    NoChangesToCommitError, ConflictsInTreeError,
                    StrictCommitError, BoundBranchOutOfDate,
                    LocalRequiresBoundBranch, NotBranchError, NonExistingParent,
                    PathPrefixNotCreated, NoPushLocationKnown,
                    DivergedBranchesError)

def commit(selected_list, message=None, file=None, unchanged=False,
           strict=False, local=False):
    """ Command to commit changes into the branch.
    
    :param selected_list: list of files you want to commit (at least the top working directory has to specified)
    
    :param message: commit message
    
    :param file: the file which contains the commit message
    
    :param unchanged: force commit if nothing has changed since the last commit
    
    :param strict: refuse to commit if there are unknown files in the working tree
    
    :param local: perform a local only commit in a bound branch
    """
    from bzrlib.builtins import tree_files
    from bzrlib.commit import NullCommitReporter

    try:
        tree, selected_list = tree_files(selected_list)
    except errors.NotBranchError:
        raise NotBranchError
    
    if local and not tree.branch.get_bound_location():
        raise LocalRequiresBoundBranch()
    if message is None and not file:
        if message is None:
            raise NoMessageNoFileError
    elif message and file:
        raise NoMessageNoFileError

    if file:
        message = codecs.open(file, 'rt', bzrlib.user_encoding).read()

    if message == "":
        raise EmptyMessageError

    reporter = NullCommitReporter()

    try:
        tree.commit(message, specific_files=selected_list,
                    allow_pointless=unchanged, strict=strict, local=local,
                    reporter=reporter)
    except errors.PointlessCommit:
        raise NoChangesToCommitError
    except errors.ConflictsInTree:
        raise ConflictsInTreeError
    except errors.StrictCommitFailed:
        raise StrictCommitError
    except errors.BoundBranchOutOfDate, e:
        raise BoundBranchOutOfDate(str(e))

# FIXME - not tested yet
def push(branch, location=None, remember=False, overwrite=False,
         create_prefix=False):
    """ Update a mirror of a branch.
    
    :param branch: the source branch
    
    :param location: the location of the branch that you'd like to update
    
    :param remember: if set, the location will be stored
    
    :param overwrite: overwrite target location if it diverged
    
    :param create_prefix: create the path leading up to the branch if it doesn't exist
    
    :return: number of revisions pushed
    """
    from bzrlib.branch import Branch
    from bzrlib.transport import get_transport
        
    br_from = Branch.open_containing(branch)[0]
    stored_loc = br_from.get_push_location()
    if location is None:
        if stored_loc is None:
            raise NoPushLocationKnown
        else:
            location = stored_loc

    transport = get_transport(location)
    location_url = transport.base

    if br_from.get_push_location() is None or remember:
        br_from.set_push_location(location_url)

    old_rh = []

    try:
        dir_to = bzrlib.bzrdir.BzrDir.open(location_url)
        br_to = dir_to.open_branch()
    except errors.NotBranchError:
        # create a branch.
        transport = transport.clone('..')
        if not create_prefix:
            try:
                relurl = transport.relpath(location_url)
                transport.mkdir(relurl)
            except errors.NoSuchFile:
                raise NonExistingParent(location)
        else:
            current = transport.base
            needed = [(transport, transport.relpath(location_url))]
            while needed:
                try:
                    transport, relpath = needed[-1]
                    transport.mkdir(relpath)
                    needed.pop()
                except errors.NoSuchFile:
                    new_transport = transport.clone('..')
                    needed.append((new_transport,
                                   new_transport.relpath(transport.base)))
                    if new_transport.base == transport.base:
                        raise PathPrefixNotCreated
        dir_to = br_from.bzrdir.clone(location_url,
            revision_id=br_from.last_revision())
        br_to = dir_to.open_branch()
        count = len(br_to.revision_history())
    else:
        old_rh = br_to.revision_history()
        try:
            try:
                tree_to = dir_to.open_workingtree()
            except errors.NotLocalUrl:
                # FIXME - what to do here? how should we warn the user?
                #warning('This transport does not update the working '
                #        'tree of: %s' % (br_to.base,))
                count = br_to.pull(br_from, overwrite)
            except errors.NoWorkingTree:
                count = br_to.pull(br_from, overwrite)
            else:
                count = tree_to.pull(br_from, overwrite)
        except errors.DivergedBranches:
            raise DivergedBranchesError
    
    return count
