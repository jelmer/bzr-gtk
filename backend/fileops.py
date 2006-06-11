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

import os

import bzrlib.errors as errors

from errors import (DirectoryAlreadyExists, NoFilesSpecified, NoMatchingFiles,
                    NotVersionedError)

def mkdir(directory):
    """ Create new versioned directory.
    
    :param directory: the full path to the directory to be created
    """
    from bzrlib.workingtree import WorkingTree
    
    try:
        os.mkdir(directory)
    except OSError, e:
        if e.errno == 17:
            raise DirectoryAlreadyExists(directory)
    else:
        wt, dd = WorkingTree.open_containing(directory)
        wt.add([dd])

def add(file_list):
    """ Add listed files to the branch. 
    
    :param file_list - list of files to be added (using full paths)
    
    :return: count of ignored files
    """
    import bzrlib.add
    
    added, ignored = bzrlib.add.smart_add(file_list)
    
    match_len = 0
    for glob, paths in ignored.items():
        match_len += len(paths)
    
    return match_len

def remove(file_list, new=False):
    """ Make selected files unversioned.
    
    :param file_list: list of files/directories to be removed
    
    :param new: if True, the 'added' files will be removed
    """
    from bzrlib.builtins import tree_files
    
    tree, file_list = tree_files(file_list)
    
    if new is False:
        if file_list is None:
            raise NoFilesSpecified
    else:
        from bzrlib.delta import compare_trees
        added = [compare_trees(tree.basis_tree(), tree,
                               specific_files=file_list).added]
        file_list = sorted([f[0] for f in added[0]], reverse=True)
        if len(file_list) == 0:
            raise NoMatchingFiles
    
    try:
        tree.remove(file_list)
    except errors.NotVersionedError:
        raise NotVersionedError

