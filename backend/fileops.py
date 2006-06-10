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
from errors import DirectoryAlreadyExists

def mkdir(directory):
    """ Create new versioned directory """
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
    """ Add listed files to the branch 
    
    file_list must contain full paths
    
    Returns the ignored files.
    """
    import bzrlib.add
    
    #action = bzrlib.add.AddAction()
    added, ignored = bzrlib.add.smart_add(file_list)
    
    match_len = 0
    for glob, paths in ignored.items():
        match_len += len(paths)
    
    return match_len
