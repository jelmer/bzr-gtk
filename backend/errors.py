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

class OliveError(Exception):
    """ Parent class for Olive exceptions/errors """
    pass

class AlreadyBranchError(OliveError):
    """ The specified directory is already a branch
    
    May occur in:
        init.init()
    """

class BoundBranchOutOfDate(OliveError):
    """ Occurs if the bound branch is out of date
    
    May occur in:
        commit.commit()
    """

class BranchExistsWithoutWorkingTree(OliveError):
    """ The specified directory is a branch, however it doesn't contain a working tree
    
    May occur in:
        init.init()
    """

class ConflictsInTreeError(OliveError):
    """ Occurs if non-resolved conflicts remained in the tree
    
    May occur in:
        commit.commit()
    """

class DirectoryAlreadyExists(OliveError):
    """ The specified directory already exists
    
    May occur in:
        fileops.mkdir()
    """

class DivergedBranchesError(OliveError):
    """ The branches have been diverged
    
    May occur in:
        commit.push()
    """

class EmptyMessageError(OliveError):
    """ Occurs if no commit message specified
    
    May occur in:
        commit.commit()
    """

class LocalRequiresBoundBranch(OliveError):
    """ Occurs when the local branch needs a bound branch
    
    May occur in:
        commit.commit()
    """

class MissingArgumentError(OliveError):
    """ Occurs when not enough parameters are given.
    
    May occur in:
        fileops.move()
    """

class MultipleMoveError(OliveError):
    """ Occurs when moving/renaming more than 2 files, but the last argument is not a directory
    
    May occur in:
        fileops.move()
    """

class NoChangesToCommitError(OliveError):
    """ Occurs if there are no changes to commit
    
    May occur in:
        commit.commit()
    """

class NoFilesSpecified(OliveError):
    """ No files were specified as an argument to a function
    
    May occur in:
        fileops.remove()
    """

class NoLocationKnown(OliveError):
    """ No location known or specified
    
    May occur in:
        commit.push()
        init.pull()
    """

class NoMatchingFiles(OliveError):
    """ No files found which could match the criteria
    
    May occur in:
        fileops.remove()
    """

class NoMessageNoFileError(OliveError):
    """ No message and no file given (for commit)
    
    May occur in:
        commit.commit()
    """

class NonExistingParent(OliveError):
    """ Parent directory doesn't exist
    
    May occur in:
        init.branch()
        init.checkout()
        commit.push()
    """

class NonExistingRevision(OliveError):
    """ The specified revision doesn't exist in the branch
    
    May occur in:
        init.branch()
    """

class NonExistingSource(OliveError):
    """ The source provided doesn't exist
    
    May occur in:
        init.branch()
    """

class NotBranchError(OliveError):
    """ Specified directory is not a branch
    
    May occur in:
        commit.commit()
    """

class NotVersionedError(OliveError):
    """ Occurs if the specified file/directory is not in the branch
    
    May occur in:
        fileops.remove()
    """

class PathPrefixNotCreated(OliveError):
    """ The path prefix couldn't be created
    
    May occur in:
        commit.push()
    """

class RevisionValueError(OliveError):
    """ Invalid revision value provided
    
    May occur in:
    """

class StrictCommitError(OliveError):
    """ Occurs if strict commit fails
    
    May occur in:
        commit.commit()
    """

class TargetAlreadyExists(OliveError):
    """ Target directory already exists
    
    May occur in:
        init.branch()
        init.checkout()
    """
