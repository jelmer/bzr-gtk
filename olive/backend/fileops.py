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

import bzrlib.errors as errors

from errors import (DirectoryAlreadyExists, MissingArgumentError,
                    MultipleMoveError, NoFilesSpecified, NoMatchingFiles,
                    NonExistingSource, NotBranchError, NotVersionedError)

def add(file_list, recursive=False):
    """ Add listed files to the branch. 
    
    :param file_list - list of files to be added (using full paths)
    
    :param recursive - if True, all unknown files will be added
    
    :return: count of ignored files
    """
    import bzrlib.add
    
    try:
        added, ignored = bzrlib.add.smart_add(file_list, recursive)
    except errors.NotBranchError:
        raise NotBranchError
    except:
        raise
    
    match_len = 0
    for glob, paths in ignored.items():
        match_len += len(paths)
    
    return match_len

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

def move(names_list):
    """ Move or rename given files.
    
    :param file_list: if two elements, then rename the first to the second, if more elements then move all of them to the directory specified in the last element
    """
    from bzrlib.builtins import tree_files
    
    if len(names_list) < 2:
        raise MissingArgumentError
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
    
    try:
        tree, file_list = tree_files(file_list)
    except errors.NotBranchError:
        raise NotBranchError
    except:
        raise
    
    if new is False:
        if file_list is None:
            raise NoFilesSpecified
    else:
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
    
    try:
        tree.remove(file_list)
    except errors.NotVersionedError:
        raise NotVersionedError

def rename(source, target):
    """ Rename a versioned file
    
    :param source: full path to the original file
    
    :param target: full path to the new file
    """
    if os.access(source, os.F_OK) is not True:
        raise NonExistingSource(source)
    
    move([source, target])

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
    except errors.NotBranchError:
        return 'unknown'
    
    branch = tree1.branch
    tree2 = tree1.branch.repository.revision_tree(branch.last_revision())
    
    # find the relative path to the given file (needed for proper delta)
    wtpath = tree1.basedir
    #print "DEBUG: wtpath =", wtpath
    fullpath = filename
    #print "DEBUG: fullpath =", fullpath
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
    #print "DEBUG: rel =", rel
    
    if bzrlib.version_info[1] < 9:
        delta = compare_trees(old_tree=tree2,
                              new_tree=tree1,
                              want_unchanged=True,
                              specific_files=[rel])
    else:
        delta = tree1.changes_from(tree2,
                                   want_unchanged=True,
                                   specific_files=[rel])
    
    """ Debug information (could be usable in the future, so didn't cut out)
    print "DEBUG: delta.renamed:"
    for path, id, kind, text_modified, meta_modified in delta.renamed:
        print path
    print
    print "DEBUG: delta.added:"
    for path, id, kind in delta.added:
        print path
    print
    print "DEBUG: delta.removed:"
    for path, id, kind, text_modified, meta_modified in delta.removed:
        print path
    print
    print "DEBUG: delta.modified:"
    for path, id, kind, text_modified, meta_modified in delta.modified:
        print path
    print
    print "DEBUG: delta.unchanged:"
    for path, id, kind in delta.unchanged:
        print path
    """
    
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
