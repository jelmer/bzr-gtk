# Copyright (C) 2006 by Szilveszter Farkas (Phanatic) <szilveszter.farkas@gmail.com>
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

import sys

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass
import gtk
import gtk.glade
import gobject
import pango

from bzrlib.branch import Branch
import bzrlib.errors as errors

from bzrlib.plugins.gtk.viz.branchwin import BranchWindow

from dialog import error_dialog

from olive import gladefile

class OliveLog:
    """ Display Log (bzrk) window and perform the needed actions. """
    def __init__(self, comm):
        """ Initialize the Log (bzrk) window. """

        # Communication object
        self.comm = comm
        
        # Check if current location is a branch
        self.notbranch = False
        try:
            (self.branch, path) = Branch.open_containing(self.comm.get_path())
        except errors.NotBranchError:
            self.notbranch = True
            return
        
        self.revid = self.branch.last_revision()

    def display(self):
		""" Display the Log (bzrk) window. """
		window = BranchWindow()
		window.set_branch(self.branch, self.revid, None)
		window.show()
