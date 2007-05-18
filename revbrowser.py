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

import time

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

import gobject
import gtk

from bzrlib.osutils import format_date


class RevisionBrowser(gtk.Dialog):
    """ Revision Browser main window. """
    def __init__(self, branch, parent=None):
        gtk.Dialog.__init__(self, title="Revision Browser - Olive",
                                  parent=parent,
                                  flags=gtk.DIALOG_MODAL,
                                  buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
    
        # Get arguments
        self.branch = branch
        
        # Create the widgets
        self._hbox = gtk.HBox()
        self._image_loading = gtk.image_new_from_stock(gtk.STOCK_REFRESH, gtk.ICON_SIZE_BUTTON)
        self._label_loading = gtk.Label(_("Please wait, revisions are being loaded..."))
        self._scrolledwindow = gtk.ScrolledWindow()
        self._treeview = gtk.TreeView()
        self._button_select = gtk.Button(_("_Select"), use_underline=True)
        
        # Set callbacks
        self._button_select.connect('clicked', self._on_select_clicked)
        self._treeview.connect('row-activated', self._on_treeview_row_activated)
        
        # Set properties
        self._scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC,
                                        gtk.POLICY_AUTOMATIC)
        self.vbox.set_spacing(3)
        self.set_default_size(600, 400)
        self._label_loading.set_alignment(0.0, 0.5)
        self._hbox.set_spacing(5)
        self._hbox.set_border_width(5)
        
        # Construct the TreeView columns
        self._treeview.append_column(gtk.TreeViewColumn(_('Revno'),
                                     gtk.CellRendererText(), text=0))
        self._treeview.append_column(gtk.TreeViewColumn(_('Summary'),
                                     gtk.CellRendererText(), text=1))
        self._treeview.append_column(gtk.TreeViewColumn(_('Committer'),
                                     gtk.CellRendererText(), text=2))
        self._treeview.append_column(gtk.TreeViewColumn(_('Time'),
                                     gtk.CellRendererText(), text=3))
        self._treeview.get_column(1).get_cell_renderers()[0].set_property("width-chars", 40)
        self._treeview.get_column(2).get_cell_renderers()[0].set_property("width-chars", 40)
        self._treeview.get_column(3).get_cell_renderers()[0].set_property("width-chars", 40)
        
        # Construct the dialog
        self.action_area.pack_end(self._button_select)
        
        self._scrolledwindow.add(self._treeview)
        
        self._hbox.pack_start(self._image_loading, False, False)
        self._hbox.pack_start(self._label_loading, True, True)
        
        self.vbox.pack_start(self._hbox, False, False)
        self.vbox.pack_start(self._scrolledwindow, True, True)

        # Show the dialog
        self.show_all()
        
        # Fill up with revisions
        self._fill_revisions()

    def _fill_revisions(self):
        """ Fill up the treeview with the revisions. """
        # [ revno, message, committer, timestamp, revid ]
        self.model = gtk.ListStore(gobject.TYPE_STRING,
                                   gobject.TYPE_STRING,
                                   gobject.TYPE_STRING,
                                   gobject.TYPE_STRING,
                                   gobject.TYPE_STRING)
        self._treeview.set_model(self.model)

        repo = self.branch.repository
        revs = self.branch.revision_history()
        r = repo.get_revisions(revs)
        r.reverse()

        for rev in r:
            if rev.committer is not None:
                timestamp = format_date(rev.timestamp, rev.timezone)
            else:
                timestamp = None
            self.model.append([ self.branch.revision_id_to_revno(rev.revision_id),
                                rev.get_summary(),
                                rev.committer,
                                timestamp,
                                rev.revision_id ])
            while gtk.events_pending():
                gtk.main_iteration()
        tend = time.time()
        
        # Finished loading
        self._hbox.hide()
    
    def _get_selected_revno(self):
        """ Return the selected revision's revno. """
        treeselection = self._treeview.get_selection()
        (model, iter) = treeselection.get_selected()
        
        if iter is None:
            return None
        else:
            return model.get_value(iter, 0)
    
    def _get_selected_revid(self):
        """ Return the selected revision's revid. """
        treeselection = self._treeview.get_selection()
        (model, iter) = treeselection.get_selected()
        
        if iter is None:
            return None
        else:
            return model.get_value(iter, 4)
    
    def _on_treeview_row_activated(self, treeview, path, column):
        """ Double-click on a row should also select a revision. """
        self._on_select_clicked(treeview)
    
    def _on_select_clicked(self, widget):
        """ Select button clicked handler. """
        self.selected_revno = self._get_selected_revno()
        self.selected_revid = self._get_selected_revid()
        self.response(gtk.RESPONSE_OK)
