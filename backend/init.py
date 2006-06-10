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

import errno
import os

import bzrlib.errors as errors

from errors import (AlreadyBranchError, BranchExistsWithoutWorkingTree,
                    NonExistingParent, NonExistingRevision, NonExistingSource,
                    RevisionValueError, TargetAlreadyExists)

def init(location):
    from bzrlib.builtins import get_format_type
    import bzrlib.bzrdir as bzrdir

    format = get_format_type('default')
 
    if not os.path.exists(location):
        os.mkdir(location)
 
    try:
        existing_bzrdir = bzrdir.BzrDir.open(location)
    except errors.NotBranchError:
        bzrdir.BzrDir.create_branch_convenience(location, format=format)
    else:
        if existing_bzrdir.has_branch():
            if existing_bzrdir.has_workingtree():
                raise AlreadyBranchError(location)
            else:
                raise BranchExistsWithoutWorkingTree(location)
        else:
            existing_bzrdir.create_branch()
            existing_bzrdir.create_workingtree()

def branch(from_location, to_location, revision=None):
    from bzrlib.branch import Branch
    from bzrlib.transport import get_transport

    if revision is None:
        revision = [None]
    elif len(revision) > 1:
        raise RevisionValueError('bzr branch --revision takes exactly 1 revision value')

    try:
        br_from = Branch.open(from_location)
    except OSError, e:
        if e.errno == errno.ENOENT:
            raise NonExistingSource(from_location)
        else:
            raise

    br_from.lock_read()

    try:
        basis_dir = None
        if len(revision) == 1 and revision[0] is not None:
            revision_id = revision[0].in_history(br_from)[1]
        else:
            revision_id = br_from.last_revision()

        to_location = to_location + '/' + os.path.basename(from_location.rstrip("/\\"))
        name = None
        to_transport = get_transport(to_location)

        try:
            to_transport.mkdir('.')
        except errors.FileExists:
            raise TargetAlreadyExists(to_location)
        except errors.NoSuchFile:
            raise NonExistingParent(to_location)

        try:
            dir = br_from.bzrdir.sprout(to_transport.base, revision_id, basis_dir)
            branch = dir.open_branch()
        except errors.NoSuchRevision:
            to_transport.delete_tree('.')
            raise NonExistingRevision(from_location, revision[0])

        if name:
            branch.control_files.put_utf8('branch-name', name)
    finally:
        br_from.unlock()
        
    return branch.revno()

def checkout():
    """ FIXME - will be implemented later """
