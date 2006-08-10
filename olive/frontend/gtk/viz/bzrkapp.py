# Modified for use with Olive:
# Copyright (C) 2006 by Szilveszter Farkas (Phanatic) <szilveszter.farkas@gmail.com>
# Original copyright holder:
# Copyright (C) 2005 by Canonical Ltd. (Scott James Remnant <scott@ubuntu.com>)
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

"""Application object.

This module contains the application object that manages the windows
on screen, and can be used to create new windows of various types.
"""

__copyright__ = "Copyright © 2005 Canonical Ltd."
__author__    = "Scott James Remnant <scott@ubuntu.com>"


import pygtk
pygtk.require("2.0")

import gtk

from branchwin import BranchWindow
from diffwin import DiffWindow


class BzrkApp(object):
    """Application manager.

    This object manages the bzrk application, creating and managing
    individual branch windows and ensuring the application exits when
    the last window is closed.
    """

    def show(self, branch, start, maxnum):
        """Open a new window to show the given branch."""
        window = BranchWindow(self)
        window.set_branch(branch, start, maxnum)
        window.show()

    def show_diff(self, branch, revid, parentid):
        """Open a new window to show a diff between the given revisions."""
        window = DiffWindow()
        rev_tree = branch.repository.revision_tree(revid)
        parent_tree = branch.repository.revision_tree(parentid)
        description = revid + " - " + branch.nick
        window.set_diff(description, rev_tree, parent_tree)
        window.show()
