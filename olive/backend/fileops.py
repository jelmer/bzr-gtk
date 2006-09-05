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

import os

from bzrlib.errors import (BzrError, NotBranchError, NotVersionedError, 
                           PermissionDenied)


class MultipleMoveError(BzrError):
    """ Occurs when moving/renaming more than 2 files, but the last argument is not a directory
    
    May occur in:
        fileops.move()
    """


class NoMatchingFiles(BzrError):
    """ No files found which could match the criteria
    
    May occur in:
        fileops.remove()
    """


def move(names_list):
    """ Move or rename given files.
    
    :param file_list: if two elements, then rename the first to the second, if more elements then move all of them to the directory specified in the last element
    """
    from bzrlib.builtins import tree_files
    
    tree, rel_names = tree_files(names_list)
        
    if os.path.isdir(names_list[-1]):
        # move into existing directory
        for pair in tree.move(rel_names[:-1], rel_names[-1]):
            pass
    else:
        if len(names_list) != 2:
            raise MultipleMoveError
        tree.rename_one(rel_names[0], rel_names[1])


def remove(file_list, new=False):
    """ Make selected files unversioned.
    
    :param file_list: list of files/directories to be removed
    
    :param new: if True, the 'added' files will be removed
    """
    import bzrlib
    from bzrlib.builtins import tree_files
    
    tree, file_list = tree_files(file_list)
    
    if new:
        from bzrlib.delta import compare_trees
        if (bzrlib.version_info[0] == 0) and (bzrlib.version_info[1] < 9):
            added = [compare_trees(tree.basis_tree(), tree,
                                   specific_files=file_list).added]
        else:
            added = [tree.changes_from(tree.basis_tree(),
                                       specific_files=file_list).added]
        file_list = sorted([f[0] for f in added[0]], reverse=True)
        if len(file_list) == 0:
            raise NoMatchingFiles
    
    tree.remove(file_list)


def status(filename):
    """ Get the status of a file.
    
    :param filename: the full path to the file
    
    :return: renamed | added | removed | modified | unchanged | unknown
    """
    import bzrlib
    from bzrlib.delta import compare_trees
    from bzrlib.workingtree import WorkingTree
    
    try:
        tree1 = WorkingTree.open_containing(filename)[0]
    except NotBranchError:
        return 'unknown'
    
    branch = tree1.branch
    tree2 = tree1.branch.repository.revision_tree(branch.last_revision())
    
    # find the relative path to the given file (needed for proper delta)
    wtpath = tree1.basedir
    fullpath = filename
    i = 0
    wtsplit = wtpath.split('/')
    fpsplit = fullpath.split('/')
    fpcopy = fullpath.split('/')
    for item in fpsplit:
        if i is not len(wtsplit):
            if item == wtsplit[i]:
                del fpcopy[0]
            i = i + 1
    rel = '/'.join(fpcopy)
    
    delta = tree1.changes_from(tree2,
                                   want_unchanged=True,
                                   specific_files=[rel])
    
    if len(delta.renamed):
        return 'renamed'
    elif len(delta.added):
        return 'added'
    elif len(delta.removed):
        return 'removed'
    elif len(delta.modified):
        return 'modified'
    elif len(delta.unchanged):
        return 'unchanged'
    else:
        return 'unknown'
