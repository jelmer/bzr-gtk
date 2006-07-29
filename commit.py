# Copyright (C) 2006 Jelmer Vernooij <jelmer@samba.org>

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

import pygtk
pygtk.require("2.0")
import gobject
import gtk
import pango
from bzrlib.delta import compare_trees

class GCommitDialog(gtk.Dialog):
    """ Commit Dialog """

    def __init__(self, tree):
        gtk.Dialog.__init__(self)

        self.set_default_size(400, 400)

        self.old_tree = tree.branch.repository.revision_tree(tree.branch.last_revision())
        self.pending_merges = tree.pending_merges()
        self.delta = compare_trees(self.old_tree, tree)

        self._create()

    def _create_file_view(self):
        self.file_store = gtk.ListStore(gobject.TYPE_BOOLEAN, gobject.TYPE_STRING, gobject.TYPE_STRING)
        self.file_view = gtk.TreeView(self.file_store)
        crt = gtk.CellRendererToggle()
        crt.set_property("activatable", True)
        crt.connect("toggled", self._toggle_commit, self.file_store)
        self.file_view.append_column(gtk.TreeViewColumn("Commit", 
                                     crt, active=0))
        self.file_view.append_column(gtk.TreeViewColumn("Path", 
                                     gtk.CellRendererText(), text=1))
        self.file_view.append_column(gtk.TreeViewColumn("Type", 
                                     gtk.CellRendererText(), text=2))

        for path, _, _ in self.delta.added:
            self.file_store.append([ True, path, "Added" ])

        for path, _, _ in self.delta.removed:
            self.file_store.append([ True, path, "Removed" ])

        for oldpath, _, _, _, _, _ in self.delta.renamed:
            self.file_store.append([ True, oldpath, "Renamed"])

        for path, _, _, _, _ in self.delta.modified:
            self.file_store.append([ True, path, "Modified"])

        self.file_view.show()

    def _toggle_commit(self, cell, path, model):
        model[path][0] = not model[path][0]
        return
    
    def _get_specific_files(self):
        ret = []
        it = self.file_store.get_iter_first()
        while it:
            if self.file_store.get_value(it, 0):
                ret.append(self.file_store.get_value(it, 1))
            it = self.file_store.iter_next(it)

        return ret

    specific_files = property(_get_specific_files)

    def _create_pending_merge_view(self, merges):
        self.pending_merge_store = gtk.ListStore(gobject.TYPE_STRING)
        for revid in merges:
            self.pending_merge_store.append([revid])
        self.pending_merge_view = gtk.TreeView(self.pending_merge_store)
        self.pending_merge_view.show()

    def _create_message_box(self):
        self.message_entry = gtk.TextView()
        self.message_entry.show()
        return self.message_entry

    def _get_message(self):
        buffer = self.message_entry.get_buffer()
        return buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter())

    message = property(_get_message)

    def _create(self):
        # Show list of changed files with checkboxes
        self._create_file_view()
        self.vbox.set_spacing(2)
        self.vbox.pack_start(self.file_view, expand=True, fill=True)

        # If_ there are any pending merges, show list of pending merges
        if self.pending_merges:
            self._create_pending_merge_view(self.pending_merges)
            self.vbox.pack_start(self.pending_merge_view, expand=True, fill=True)

        # Show box where user can add comments
        self._create_message_box()
        self.vbox.pack_start(self.message_entry, expand=True, fill=True)

        # Commit, Cancel buttons
        self.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, "_Commit", gtk.RESPONSE_OK)
                         
