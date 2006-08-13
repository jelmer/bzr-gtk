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
try:
    import gtk
    import gtk.glade
    import gobject
    import pango
except:
    sys.exit(1)

from bzrlib.branch import Branch
import bzrlib.errors as errors

from viz.bzrkapp import BzrkApp

class OliveLog:
    """ Display Log (bzrk) window and perform the needed actions. """
    def __init__(self, gladefile, comm, dialog):
        """ Initialize the Log (bzrk) window. """
        self.gladefile = gladefile

        # Communication object
        self.comm = comm
        # Dialog object
        self.dialog = dialog
        
        # Check if current location is a branch
        self.notbranch = False
        try:
            (self.branch, path) = Branch.open_containing(self.comm.get_path())
        except errors.NotBranchError:
            self.notbranch = True
            return
        except:
            raise
        
        self.revid = self.branch.last_revision()

    def display(self):
        """ Display the Log (bzrk) window. """
        if self.notbranch:
            self.dialog.error_dialog('Directory is not a branch',
                                     'You can perform this action only in a branch.')
        else:
            self.app = BzrkApp()
            self.app.show(self.branch, self.revid, None)
