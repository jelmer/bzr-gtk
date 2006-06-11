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
                    LocalRequiresBoundBranch, NotBranchError)

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

