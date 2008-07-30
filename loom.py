# Copyright (C) 2008 Jelmer Vernooij <jelmer@samba.org>
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

import gtk
import gobject

from bzrlib.plugins.gtk import _i18n
from bzrlib.plugins.gtk.dialog import question_dialog
from bzrlib.plugins.loom import branch as loom_branch

class LoomDialog(gtk.Dialog):
    """Simple Loom browse dialog."""

    def __init__(self, branch, parent=None):
        gtk.Dialog.__init__(self, title="Threads",
                                  parent=parent,
                                  flags=0,
                                  buttons=(gtk.STOCK_CLOSE,gtk.RESPONSE_OK))
        self.branch = branch

        self._construct()

    def run(self):
        try:
            loom_branch.require_loom_branch(self.branch)
        except loom_branch.NotALoom:
            response = question_dialog(
                _i18n("Upgrade to Loom branch?"),
                _i18n("Branch is not a loom branch. Upgrade to Loom format?"),
                parent=self)
                # Doesn't set a parent for the dialog..
            if response == gtk.RESPONSE_NO:
                return
            loom_branch.loomify(self.branch)
        return super(LoomDialog, self).run()

    def _construct(self):
        self._threads_view = gtk.TreeView()
        self._threads_view.show()
        self.vbox.pack_start(self._threads_view)

        # Buttons: combine-thread, export-loom, revert-loom, up-thread

