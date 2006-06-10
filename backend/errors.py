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
    """ The specified directory is already a branch """

class BranchExistsWithoutWorkingTree(OliveError):
    """ The specified directory is a branch, however it doesn't contain a working tree """

class DirectoryAlreadyExists(OliveError):
    """ The specified directory already exists """

class NonExistingParent(OliveError):
    """ Parent directory doesn't exist """

class NonExistingRevision(OliveError):
    """ The specified revision doesn't exist in the branch """

class NonExistingSource(OliveError):
    """ The source provided doesn't exist """

class RevisionValueError(OliveError):
    """ Invalid revision value provided """

class TargetAlreadyExists(OliveError):
    """ Target directory already exists """
