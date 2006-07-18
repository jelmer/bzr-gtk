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

import errno
import os

import bzrlib
import bzrlib.bzrdir as bzrdir
import bzrlib.errors as errors

from bzrlib.branch import Branch

from errors import (AlreadyBranchError, BranchExistsWithoutWorkingTree,
                    NonExistingParent, NonExistingRevision,
                    NonExistingSource, NotBranchError, TargetAlreadyExists)

def init(location):
    """ Initialize a directory.
    
    :param location: full path to the directory you want to be versioned
    """
    from bzrlib.builtins import get_format_type

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
    """ Create a branch from a local/remote location.
    
    :param from_location: the original location of the branch
    
    :param to_location: the directory where the branch should be created
    
    :param revision: if specified, the given revision will be branched
    
    :return: number of revisions branched
    """
    from bzrlib.transport import get_transport

    try:
        br_from = Branch.open(from_location)
    except OSError, e:
        if e.errno == errno.ENOENT:
            raise NonExistingSource(from_location)
        else:
            raise
    except errors.NotBranchError:
        raise NotBranchError(from_location)

    br_from.lock_read()

    try:
        basis_dir = None
        if revision is not None:
            revision_id = br_from.get_rev_id(revision)
        else:
            revision_id = None

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

def checkout(branch_location, to_location, revision=None, lightweight=False):
    """ Create a new checkout of an existing branch.
    
    :param branch_location: the location of the branch you'd like to checkout
    
    :param to_location: the directory where the checkout should be created
    
    :param revision: the given revision will be checkout'ed (be aware!)
    
    :param lightweight: perform a lightweight checkout (be aware!)
    """
    source = Branch.open(branch_location)
    
    if revision is not None:
        revision_id = source.get_rev_id(revision)
    else:
        revision_id = None

    # if the source and to_location are the same, 
    # and there is no working tree,
    # then reconstitute a branch
    if (bzrlib.osutils.abspath(to_location) ==
        bzrlib.osutils.abspath(branch_location)):
        try:
            source.bzrdir.open_workingtree()
        except errors.NoWorkingTree:
            source.bzrdir.create_workingtree()
            return

    try:
        os.mkdir(to_location)
    except OSError, e:
        if e.errno == errno.EEXIST:
            raise TargetAlreadyExists(to_location)
        if e.errno == errno.ENOENT:
            raise NonExistingParent(to_location)
        else:
            raise

    old_format = bzrlib.bzrdir.BzrDirFormat.get_default_format()
    bzrlib.bzrdir.BzrDirFormat.set_default_format(bzrdir.BzrDirMetaFormat1())

    try:
        if lightweight:
            checkout = bzrdir.BzrDirMetaFormat1().initialize(to_location)
            bzrlib.branch.BranchReferenceFormat().initialize(checkout, source)
        else:
            checkout_branch = bzrlib.bzrdir.BzrDir.create_branch_convenience(
                to_location, force_new_tree=False)
            checkout = checkout_branch.bzrdir
            checkout_branch.bind(source)
            if revision_id is not None:
                rh = checkout_branch.revision_history()
                checkout_branch.set_revision_history(rh[:rh.index(revision_id) + 1])

        checkout.create_workingtree(revision_id)
    finally:
        bzrlib.bzrdir.BzrDirFormat.set_default_format(old_format)
