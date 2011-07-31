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

from gi.repository import GObject
from gi.repository import Gtk

from bzrlib.plugins.search import index as _mod_index

from bzrlib.plugins.gtk.i18n import _i18n

class SearchDialog(Gtk.Dialog):
    """Search dialog."""
    def __init__(self, index, parent=None):
        GObject.GObject.__init__(self, title="Search Revisions",
                                  parent=parent,
                                  flags=Gtk.DialogFlags.MODAL,
                                  buttons=(Gtk.STOCK_OK, Gtk.ResponseType.OK,
                                           Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))
        pixbuf = self.render_icon(Gtk.STOCK_FIND, Gtk.IconSize.MENU)
        self.set_icon(pixbuf)
        
        # Get arguments
        self.index = index

        self.searchbar = Gtk.HBox()
        searchbar_label = Gtk.Label(label=_i18n("Search for:"))
        self.searchbar.pack_start(searchbar_label, False, False, 0)
        self.searchentry = Gtk.Entry()
        self.searchentry.connect('activate', self._searchentry_activate)
        # TODO: Completion using the bzr-search suggests functionality
        self.searchbar.add(self.searchentry)
        self.vbox.pack_start(self.searchbar, expand=False, fill=False)

        self.results_model = Gtk.ListStore(GObject.TYPE_STRING, GObject.TYPE_STRING, GObject.TYPE_PYOBJECT)
        self.results_treeview = Gtk.TreeView(self.results_model)
        self.results_treeview.connect("row-activated", self._searchresult_row_activated)

        documentname_column = Gtk.TreeViewColumn(_i18n("Document"), Gtk.CellRendererText(), text=0)
        self.results_treeview.append_column(documentname_column)

        summary_column = Gtk.TreeViewColumn(_i18n("Summary"), Gtk.CellRendererText(), text=1)
        self.results_treeview.append_column(summary_column)

        results_scrolledwindow = Gtk.ScrolledWindow()
        results_scrolledwindow.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        results_scrolledwindow.add(self.results_treeview)

        self.vbox.pack_start(results_scrolledwindow, expand=True, fill=True)

        self.set_default_size(600, 400)
        # Show the dialog
        self.show_all()

    def get_revision(self):
        (path, focus) = self.results_treeview.get_cursor()
        if path is None:
            return None
        iter = self.results_model.get_iter(path)
        return self.results_model.get_value(iter, 2)

    def _searchentry_activate(self, entry):
        self.results_model.clear()
        self.index._branch.lock_read()
        try:
            query = [(query_item,) for query_item in self.searchentry.get_text().split(" ")]
            for result in self.index.search(query):
                if isinstance(result, _mod_index.FileTextHit):
                    revid = result.text_key[-1]
                elif isinstance(result, _mod_index.RevisionHit):
                    revid = result.revision_key[0]
                else:
                    raise AssertionError()
                self.results_model.append([result.document_name(), result.summary(), revid])
        finally:
            self.index._branch.unlock()
    
    def _searchresult_row_activated(self, treeview, path, view_column):
        self.response(Gtk.ResponseType.OK)
