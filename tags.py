# Copyright (C) 2007 by Szilveszter Farkas (Phanatic) <szilveszter.farkas@gmail.com>
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

from bzrlib.plugins.gtk.logview import LogView

class TagsWindow(gtk.Window):
    """ Tags window. Allows the user to view/add/remove tags. """
    def __init__(self, branch, parent=None):
        """ Initialize the Tags window. """
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        
        # Get arguments
        self.branch = branch
        self._parent = parent
        
        # Create the widgets
        self._button_add = gtk.Button(stock=gtk.STOCK_ADD)
        self._button_remove = gtk.Button(stock=gtk.STOCK_REMOVE)
        self._button_close = gtk.Button(stock=gtk.STOCK_CLOSE)
        self._model = gtk.ListStore(str, str)
        self._treeview_tags = gtk.TreeView(self._model)
        self._scrolledwindow_tags = gtk.ScrolledWindow()
        self._logview = LogView()
        self._hbox = gtk.HBox()
        self._vbox_buttons = gtk.VBox()
        self._vpaned = gtk.VPaned()
        
        # Set callbacks
        self._button_add.connect('clicked', self._on_add_clicked)
        self._button_close.connect('clicked', self._on_close_clicked)
        self._button_remove.connect('clicked', self._on_remove_clicked)
        self._treeview_tags.connect('cursor-changed', self._on_treeview_changed)
        if parent is None:
            self.connect('delete-event', gtk.main_quit)
        
        # Set properties
        self.set_title(_("Tags - Olive"))
        
        self._scrolledwindow_tags.set_policy(gtk.POLICY_AUTOMATIC,
                                             gtk.POLICY_AUTOMATIC)
        
        # Construct the dialog
        self._scrolledwindow_tags.add(self._treeview_tags)
        
        self._vbox_buttons.pack_start(self._button_add)
        self._vbox_buttons.pack_start(self._button_remove)
        self._vbox_buttons.pack_start(self._button_close)
        
        self._vpaned.add1(self._scrolledwindow_tags)
        self._vpaned.add2(self._logview)
        
        self._hbox.pack_start(self._vpaned)
        self._hbox.pack_start(self._vbox_buttons)
        
        self.add(self._hbox)
        
        # Load the tags
        self._load_tags()
        
        # Display everything
        self._hbox.show_all()
    
    def _load_tags(self):
        """ Load the tags into the TreeView. """
        self._treeview_tags.append_column(gtk.TreeViewColumn(_("Tag Name"),
                                                             gtk.CellRendererText(),
                                                             text=0))
        self._treeview_tags.append_column(gtk.TreeViewColumn(_("Revision ID"),
                                                             gtk.CellRendererText(),
                                                             text=1))
        
        self._refresh_tags()
    
    def _refresh_tags(self):
        """ Refresh the list of tags. """
        self._model.clear()
        if self.branch.supports_tags():
            tags = self.branch.tags.get_tag_dict()
            if len(tags) > 0:
                for name, target in tags.items():
                    self._model.append([name, target])
            else:
                self._no_tags()
        else:
            self._tags_not_supported()
        
        self._treeview_tags.set_model(self._model)
    
    def _tags_not_supported(self):
        """ Tags are not supported. """
        self._model.append([_("Tags are not supported by this branch format. Please upgrade."), ""])
        self._button_add.set_sensitive(False)
        self._button_remove.set_sensitive(False)
    
    def _no_tags(self):
        """ No tags in the branch. """
        self._model.append([_("No tagged revisions in the branch."), ""])
        self._button_remove.set_sensitive(False)
    
    def _on_add_clicked(self, widget):
        """ Add button event handler. """
        return
    
    def _on_close_clicked(self, widget):
        """ Close button event handler. """
        self.destroy()
        if self._parent is None:
            gtk.main_quit()
    
    def _on_remove_clicked(self, widget):
        """ Remove button event handler. """
        (path, col) = self._treeview_tags.get_cursor()
        tag = self._model[path][0]
        
        self.branch.tags.delete_tag(tag)
        self._refresh_tags()
    
    def _on_treeview_changed(self, *args):
        """ When a user clicks on a tag. """
        (path, col) = self._treeview_tags.get_cursor()
        revision = self._model[path][1]
        
        self._logview.set_revision(self.branch.repository.get_revision(revision))
