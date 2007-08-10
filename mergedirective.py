# Copyright (C) 2007 by Jelmer Vernooij <jelmer@samba.org>
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

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

import bzrlib
import gtk
import os

class CreateMergeDirectiveDialog(gtk.Dialog):
    def __init__(self, branch, stop_revid=None):
        super(CreateMergeDirectiveDialog, self).__init__()
        self.branch = branch
        self.stop_revid = stop_revid
        self._create()

    def _create(self):
        # TODO: Create a frame with information about the revision that will be 
        # submittted

        # TODO: Create a frame with a the ability to select a branch
        
        # TODO: Create a frame with a button for selecting a file name 
        # for the bundle
        pass


class SendMergeDirectiveDialog(gtk.Dialog):
    def __init__(self):
        super(SendMergeDirectiveDialog, self).__init__()


class ApplyMergeDirectiveDialog(gtk.Dialog):
    def __init__(self):
        super(ApplyMergeDirectiveDialog, self).__init__()
