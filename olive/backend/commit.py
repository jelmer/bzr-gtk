# Copyright (C) 2006 by Szilveszter Farkas (Phanatic) <szilveszter.farkas@gmail.com>
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

import bzrlib
from bzrlib.errors import NoSuchFile

from errors import ( LocalRequiresBoundBranch, NotBranchError, NonExistingParent,
                    PathPrefixNotCreated, NoLocationKnown,
                    DivergedBranchesError)

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
            raise NoLocationKnown
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
    except NotBranchError:
        # create a branch.
        transport = transport.clone('..')
        if not create_prefix:
            try:
                relurl = transport.relpath(location_url)
                transport.mkdir(relurl)
            except NoSuchFile:
                raise NonExistingParent(location)
        else:
            current = transport.base
            needed = [(transport, transport.relpath(location_url))]
            while needed:
                try:
                    transport, relpath = needed[-1]
                    transport.mkdir(relpath)
                    needed.pop()
                except NoSuchFile:
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
            except NotLocalUrl:
                # FIXME - what to do here? how should we warn the user?
                #warning('This transport does not update the working '
                #        'tree of: %s' % (br_to.base,))
                count = br_to.pull(br_from, overwrite)
            except NoWorkingTree:
                count = br_to.pull(br_from, overwrite)
            else:
                count = tree_to.pull(br_from, overwrite)
        except DivergedBranches:
            raise DivergedBranchesError
    
    return count
