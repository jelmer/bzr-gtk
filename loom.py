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
            assert self.branch.nick is not None
            loom_branch.loomify(self.branch)
        return super(LoomDialog, self).run()

    def _construct(self):
        self._threads_scroller = gtk.ScrolledWindow()
        self._threads_scroller.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self._threads_view = gtk.TreeView()
        self._threads_view.show()
        self._threads_scroller.add(self._threads_view)
        self._threads_scroller.set_shadow_type(gtk.SHADOW_IN)
        self._threads_scroller.show()
        self.vbox.pack_start(self._threads_scroller)

        self._threads_store = gtk.ListStore(
                gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_PYOBJECT)
        self._threads_view.set_model(self._threads_store)
        self._threads_view.append_column(gtk.TreeViewColumn("Name", gtk.CellRendererText(), text=0))

        # Buttons: combine-thread, export-loom, revert-loom, up-thread
        self.set_default_size(200, 350)

        self._load_threads()

    def _load_threads(self):
        self._threads_store.clear()
        
        self.branch.lock_read()
        try:
            threads = self.branch.get_loom_state().get_threads()
            for thread in reversed(threads):
                self._threads_store.append(thread)
        finally:
            self.branch.unlock()
