# Copyright (C) 2008 by Jelmer Vernooij <jelmer@samba.org>
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

import gobject, gtk
from bzrlib.plugins.search import index as _mod_index


class SearchCompletion(gtk.EntryCompletion):
    def __init__(self, index):
        super(SearchCompletion, self).__init__()


class SearchDialog(gtk.Dialog):
    """Search dialog."""
    def __init__(self, branch, parent=None):
        gtk.Dialog.__init__(self, title="Search Revisions",
                                  parent=parent,
                                  flags=gtk.DIALOG_MODAL,
                                  buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
    
        # Get arguments
        self.branch = branch

        self.index = _mod_index.open_index_url(branch.base)

        self.searchbar = gtk.HBox()
        self.searchentry = gtk.Entry()
        self.searchentry.connect('activate', self._searchentry_activate)
        self.searchentry.set_completion(SearchCompletion(self.index))
        self.searchbar.add(self.searchentry)
        self.vbox.pack_start(self.searchbar, expand=False, fill=False)

        self.results_model = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
        self.results_treeview = gtk.TreeView(self.results_model)

        documentname_column = gtk.TreeViewColumn("Document", gtk.CellRendererText(), text=0)
        self.results_treeview.append_column(documentname_column)

        summary_column = gtk.TreeViewColumn("Summary", gtk.CellRendererText(), text=1)
        self.results_treeview.append_column(summary_column)

        results_scrolledwindow = gtk.ScrolledWindow()
        results_scrolledwindow.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        results_scrolledwindow.add(self.results_treeview)

        self.vbox.pack_start(results_scrolledwindow, expand=True, fill=True)

        self.set_default_size(600, 400)
        # Show the dialog
        self.show_all()

    def _searchentry_activate(self, entry):
        self.results_model.clear()
        self.index._branch.lock_read()
        try:
            query = [(query_item,) for query_item in self.searchentry.get_text().split(" ")]
            for result in self.index.search(query):
                self.results_model.append([result.document_name(), result.summary()])
        finally:
            self.index._branch.unlock()
