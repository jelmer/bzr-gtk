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

import bzrlib.errors as errors

from bzrlib.branch import Branch

from errors import (NotBranchError)

def nick(branch, nickname=None):
    """ Get or set nickname.
    
    :param branch: path to the branch
    
    :param nickname: if specified, the nickname will be set
    
    :return: nickname
    """
    try:
        branch = Branch.open_containing(branch)[0]
    except errors.NotBranchError:
        raise NotBranchError
    
    if nickname is not None:
        branch.nick = nickname

    return branch.nick    

def revno(branch):
    """ Get current revision number for specified branch
    
    :param branch: path to the branch
    
    :return: revision number
    """
    try:
        revno = Branch.open_containing(branch)[0].revno()
    except errors.NotBranchError:
        raise NotBranchError
    else:
        return revno


