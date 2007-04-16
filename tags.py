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

from dialog import error_dialog


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
        self._button_refresh = gtk.Button(stock=gtk.STOCK_REFRESH)
        self._button_close = gtk.Button(stock=gtk.STOCK_CLOSE)
        self._model = gtk.ListStore(str, str)
        self._treeview_tags = gtk.TreeView(self._model)
        self._scrolledwindow_tags = gtk.ScrolledWindow()
        self._logview = LogView()
        self._hbox = gtk.HBox()
        self._vbox_buttons = gtk.VBox()
        self._vbox_buttons_top = gtk.VBox()
        self._vbox_buttons_bottom = gtk.VBox()
        self._vpaned = gtk.VPaned()
        
        # Set callbacks
        self._button_add.connect('clicked', self._on_add_clicked)
        self._button_close.connect('clicked', self._on_close_clicked)
        self._button_refresh.connect('clicked', self._on_refresh_clicked)
        self._button_remove.connect('clicked', self._on_remove_clicked)
        self._treeview_tags.connect('cursor-changed', self._on_treeview_changed)
        if parent is None:
            self.connect('delete-event', gtk.main_quit)
        
        # Set properties
        self.set_title(_("Tags - Olive"))
        self.set_default_size(600, 400)
        
        self._scrolledwindow_tags.set_policy(gtk.POLICY_AUTOMATIC,
                                             gtk.POLICY_AUTOMATIC)
        
        self._hbox.set_border_width(5)
        self._hbox.set_spacing(5)
        self._vbox_buttons.set_size_request(100, -1)
        
        self._vbox_buttons_top.set_spacing(3)
        
        self._vpaned.set_position(200)
        
        # Construct the dialog
        self._scrolledwindow_tags.add(self._treeview_tags)
        
        self._vbox_buttons_top.pack_start(self._button_add, False, False)
        self._vbox_buttons_top.pack_start(self._button_remove, False, False)
        self._vbox_buttons_top.pack_start(self._button_refresh, False, False)
        self._vbox_buttons_bottom.pack_start(self._button_close, False, False)
        
        self._vbox_buttons.pack_start(self._vbox_buttons_top, True, True)
        self._vbox_buttons.pack_start(self._vbox_buttons_bottom, False, False)
        
        self._vpaned.add1(self._scrolledwindow_tags)
        self._vpaned.add2(self._logview)
        
        self._hbox.pack_start(self._vpaned, True, True)
        self._hbox.pack_start(self._vbox_buttons, False, True)
        
        self.add(self._hbox)
        
        # Default to no tags
        self._no_tags = True
        
        # Load the tags
        self._load_tags()
        
        # Display everything
        self._hbox.show_all()
    
    def _load_tags(self):
        """ Load the tags into the TreeView. """
        tvcol_name = gtk.TreeViewColumn(_("Tag Name"),
                                        gtk.CellRendererText(),
                                        text=0)
        tvcol_name.set_resizable(True)
        
        tvcol_revid = gtk.TreeViewColumn(_("Revision ID"),
                                         gtk.CellRendererText(),
                                         text=1)
        tvcol_revid.set_resizable(True)
        
        self._treeview_tags.append_column(tvcol_name)
        self._treeview_tags.append_column(tvcol_revid)
        
        self._treeview_tags.set_search_column(0)
        
        self._refresh_tags()
    
    def _refresh_tags(self):
        """ Refresh the list of tags. """
        self._model.clear()
        if self.branch.supports_tags():
            tags = self.branch.tags.get_tag_dict()
            if len(tags) > 0:
                self._no_tags = False
                for name, target in tags.items():
                    self._model.append([name, target])
                
                self._button_add.set_sensitive(True)
                self._button_remove.set_sensitive(True)
            else:
                self._no_tags = True
                self._no_tags_available()
        else:
            self._no_tags = True
            self._tags_not_supported()
        
        self._treeview_tags.set_model(self._model)
    
    def _tags_not_supported(self):
        """ Tags are not supported. """
        self._model.append([_("Tags are not supported by this branch format. Please upgrade."), ""])
        self._button_add.set_sensitive(False)
        self._button_remove.set_sensitive(False)
    
    def _no_tags_available(self):
        """ No tags in the branch. """
        self._model.append([_("No tagged revisions in the branch."), ""])
        self._button_add.set_sensitive(True)
        self._button_remove.set_sensitive(False)
    
    def _on_add_clicked(self, widget):
        """ Add button event handler. """
        dialog = AddTagDialog(self.branch, self)
        response = dialog.run()
        if response != gtk.RESPONSE_NONE:
            dialog.hide()
        
            if response == gtk.RESPONSE_OK:
                self.branch.tags.set_tag(dialog.tagname, dialog.revid)
                self._refresh_tags()
            
            dialog.destroy()
    
    def _on_close_clicked(self, widget):
        """ Close button event handler. """
        self.destroy()
        if self._parent is None:
            gtk.main_quit()
    
    def _on_refresh_clicked(self, widget):
        """ Refresh button event handler. """
        self._refresh_tags()
    
    def _on_remove_clicked(self, widget):
        """ Remove button event handler. """
        (path, col) = self._treeview_tags.get_cursor()
        if path is None:
            return
        
        tag = self._model[path][0]
        
        dialog = RemoveTagDialog(tag, self)
        response = dialog.run()
        if response != gtk.RESPONSE_NONE:
            dialog.hide()
        
            if response == gtk.RESPONSE_OK:
                self.branch.tags.delete_tag(tag)
                self._refresh_tags()
            
            dialog.destroy()
    
    def _on_treeview_changed(self, *args):
        """ When a user clicks on a tag. """
        # Refresh LogView only if there are tags available
        if not self._no_tags:
            (path, col) = self._treeview_tags.get_cursor()
            revision = self._model[path][1]
            
            self._logview.set_revision(self.branch.repository.get_revision(revision))


class RemoveTagDialog(gtk.Dialog):
    """ Confirm removal of tag. """
    def __init__(self, tagname, parent):
        gtk.Dialog.__init__(self, title="Remove tag - Olive",
                                  parent=parent,
                                  flags=0,
                                  buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        
        # Get the arguments
        self.tag = tagname
        
        # Create the widgets
        self._hbox = gtk.HBox()
        self._vbox_question = gtk.VBox()
        self._image_question = gtk.image_new_from_stock(gtk.STOCK_DIALOG_QUESTION,
                                                        gtk.ICON_SIZE_DIALOG)
        self._label_title = gtk.Label()
        self._label_question = gtk.Label()
        self._button_remove = gtk.Button(_("_Remove tag"), use_underline=True)
        
        # Set callbacks
        self._button_remove.connect('clicked', self._on_remove_clicked)
        
        # Set properties
        self._hbox.set_border_width(5)
        self._hbox.set_spacing(5)
        self._vbox_question.set_spacing(3)
        
        self._label_title.set_markup(_("<b><big>Remove tag?</big></b>"))
        self._label_title.set_alignment(0.0, 0.5)
        self._label_question.set_markup(_("Are you sure you want to remove the tag: <b>%s</b>?") % self.tag)
        self._label_question.set_alignment(0.0, 0.5)
        
        self._button_remove.set_image(gtk.image_new_from_stock(gtk.STOCK_REMOVE,
                                                               gtk.ICON_SIZE_BUTTON))
        self._button_remove.set_flags(gtk.CAN_DEFAULT)
        
        # Construct the dialog
        self._vbox_question.pack_start(self._label_title)
        self._vbox_question.pack_start(self._label_question)
        
        self._hbox.pack_start(self._image_question)
        self._hbox.pack_start(self._vbox_question)
        
        self.vbox.add(self._hbox)
        
        self.action_area.pack_end(self._button_remove)
        
        # Display dialog
        self.vbox.show_all()
        
        # Default to Commit button
        self._button_remove.grab_default()
    
    def _on_remove_clicked(self, widget):
        """ Remove button event handler. """
        self.response(gtk.RESPONSE_OK)


class AddTagDialog(gtk.Dialog):
    """ Add tag dialog. """
    def __init__(self, branch, parent):
        """ Initialize Add tag dialog. """
        gtk.Dialog.__init__(self, title="Add tag - Olive",
                                  parent=parent,
                                  flags=0,
                                  buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        
        # Get arguments
        self._branch = branch
        
        # Create the widgets
        self._button_add = gtk.Button(_("_Add tag"), use_underline=True)
        self._button_revid = gtk.Button('')
        self._table = gtk.Table(2, 2)
        self._label_name = gtk.Label(_("Tag Name:"))
        self._label_revid = gtk.Label(_("Revision ID:"))
        self._entry_name = gtk.Entry()
        self._entry_revid = gtk.Entry()
        self._hbox_revid = gtk.HBox()
        
        # Set callbacks
        self._button_add.connect('clicked', self._on_add_clicked)
        self._button_revid.connect('clicked', self._on_revid_clicked)
        
        # Set properties
        self._label_name.set_alignment(0, 0.5)
        self._label_revid.set_alignment(0, 0.5)
        self._button_add.set_image(gtk.image_new_from_stock(gtk.STOCK_ADD,
                                                            gtk.ICON_SIZE_BUTTON))
        self._button_revid.set_image(gtk.image_new_from_stock(gtk.STOCK_OPEN,
                                                               gtk.ICON_SIZE_BUTTON))
        self._button_add.set_flags(gtk.CAN_DEFAULT)
        
        # Construct the dialog
        self._hbox_revid.pack_start(self._entry_revid, True, True)
        self._hbox_revid.pack_start(self._button_revid, False, False) 
        self._table.attach(self._label_name, 0, 1, 0, 1)
        self._table.attach(self._label_revid, 0, 1, 1, 2)
        self._table.attach(self._entry_name, 1, 2, 0, 1)
        self._table.attach(self._hbox_revid, 1, 2, 1, 2)
        self.vbox.add(self._table)
        self.action_area.pack_end(self._button_add)
        
        # Show the dialog
        self.vbox.show_all()
    
    def _on_revid_clicked(self, widget):
        """ Browse for revision button clicked handler. """
        from revbrowser import RevisionBrowser
        
        revb = RevisionBrowser(self._branch, self)
        response = revb.run()
        if response != gtk.RESPONSE_NONE:
            revb.hide()
        
            if response == gtk.RESPONSE_OK:
                if revb.selected_revno is not None:
                    self._entry_revid.set_text(revb.selected_revid)
            
            revb.destroy()
    
    def _on_add_clicked(self, widget):
        """ Add button clicked handler. """
        if len(self._entry_name.get_text()) == 0:
            error_dialog(_("No tag name specified"),
                         _("You have to specify the tag's desired name."))
            return
        
        if len(self._entry_revid.get_text()) == 0:
            self.revid = self._branch.last_revision()
        else:
            self.revid = self._entry_revid.get_text()
        
        self.tagname = self._entry_name.get_text()
        
        self.response(gtk.RESPONSE_OK)
