# Copyright (C) 2007 by Szilveszter Farkas (Phanatic) <szilveszter.farkas@gmail.com>
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

from gi.repository import Gtk

from bzrlib.plugins.gtk.dialog import error_dialog
from bzrlib.plugins.gtk.i18n import _i18n
from bzrlib.plugins.gtk.revidbox import RevisionSelectionBox
from bzrlib.plugins.gtk.revisionview import RevisionView
from bzrlib.plugins.gtk.window import Window


class TagsWindow(Window):
    """ Tags window. Allows the user to view/add/remove tags. """
    def __init__(self, branch, parent=None):
        """ Initialize the Tags window. """
        super(TagsWindow, self).__init__(parent=parent)

        # Get arguments
        self.branch = branch

        # Create the widgets
        self._button_add = Gtk.Button(stock=Gtk.STOCK_ADD)
        self._button_remove = Gtk.Button(stock=Gtk.STOCK_REMOVE)
        self._button_refresh = Gtk.Button(stock=Gtk.STOCK_REFRESH)
        self._button_close = Gtk.Button(stock=Gtk.STOCK_CLOSE)
        self._model = Gtk.ListStore(str, str)
        self._treeview_tags = Gtk.TreeView(model=self._model)
        self._scrolledwindow_tags = Gtk.ScrolledWindow()
        self._revisionview = RevisionView()
        self._hbox = Gtk.HBox()
        self._vbox_buttons = Gtk.VBox()
        self._vbox_buttons_top = Gtk.VBox()
        self._vbox_buttons_bottom = Gtk.VBox()
        self._vpaned = Gtk.Paned.new(Gtk.Orientation.VERTICAL)

        # Set callbacks
        self._button_add.connect('clicked', self._on_add_clicked)
        self._button_close.connect('clicked', self._on_close_clicked)
        self._button_refresh.connect('clicked', self._on_refresh_clicked)
        self._button_remove.connect('clicked', self._on_remove_clicked)
        self._treeview_tags.connect('cursor-changed', self._on_treeview_changed)

        # Set properties
        self.set_title(_i18n("Tags"))
        self.set_default_size(600, 400)

        self._scrolledwindow_tags.set_policy(Gtk.PolicyType.AUTOMATIC,
                                             Gtk.PolicyType.AUTOMATIC)

        self._hbox.set_border_width(5)
        self._hbox.set_spacing(5)
        self._vbox_buttons.set_size_request(100, -1)

        self._vbox_buttons_top.set_spacing(3)

        self._vpaned.set_position(200)

        # Construct the dialog
        self._scrolledwindow_tags.add(self._treeview_tags)

        self._vbox_buttons_top.pack_start(
            self._button_add, False, False, 0)
        self._vbox_buttons_top.pack_start(
            self._button_remove, False, False, 0)
        self._vbox_buttons_top.pack_start(
            self._button_refresh, False, False, 0)
        self._vbox_buttons_bottom.pack_start(
            self._button_close, False, False, 0)

        self._vbox_buttons.pack_start(
            self._vbox_buttons_top, True, True, 0)
        self._vbox_buttons.pack_start(
            self._vbox_buttons_bottom, False, False, 0)

        self._vpaned.add1(self._scrolledwindow_tags)
        self._vpaned.add2(self._revisionview)

        self._hbox.pack_start(self._vpaned, True, True, 0)
        self._hbox.pack_start(self._vbox_buttons, False, True, 0)

        self.add(self._hbox)

        # Default to no tags
        self._no_tags = True

        # Load the tags
        self._load_tags()

        # Display everything
        self._hbox.show_all()

    def _load_tags(self):
        """ Load the tags into the TreeView. """
        tvcol_name = Gtk.TreeViewColumn(_i18n("Tag Name"),
                                        Gtk.CellRendererText(),
                                        text=0)
        tvcol_name.set_resizable(True)

        tvcol_revid = Gtk.TreeViewColumn(_i18n("Revision ID"),
                                         Gtk.CellRendererText(),
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
        self._model.append([_i18n("Tags are not supported by this branch format. Please upgrade."), ""])
        self._button_add.set_sensitive(False)
        self._button_remove.set_sensitive(False)

    def _no_tags_available(self):
        """ No tags in the branch. """
        self._model.append([_i18n("No tagged revisions in the branch."), ""])
        self._button_add.set_sensitive(True)
        self._button_remove.set_sensitive(False)

    def _on_add_clicked(self, widget):
        """ Add button event handler. """
        dialog = AddTagDialog(self.branch.repository, None,
                              self.branch, self)
        response = dialog.run()
        if response != Gtk.ResponseType.NONE:
            dialog.hide()
            if response == Gtk.ResponseType.OK:
                self.branch.tags.set_tag(dialog.tagname, dialog._revid)
                self._refresh_tags()
            dialog.destroy()

    def _on_close_clicked(self, widget):
        """ Close button event handler. """
        self.destroy()
        if self._parent is None:
            Gtk.main_quit()

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
        if response != Gtk.ResponseType.NONE:
            dialog.hide()
            if response == Gtk.ResponseType.OK:
                self.branch.tags.delete_tag(tag)
                self._refresh_tags()
            dialog.destroy()

    def _on_treeview_changed(self, *args):
        """ When a user clicks on a tag. """
        # Refresh RevisionView only if there are tags available
        if not self._no_tags:
            (path, col) = self._treeview_tags.get_cursor()
            if path is None:
                return  # The widget is being destroyed.
            revision = self._model[path][1]
            self._revisionview.set_revision(self.branch.repository.get_revision(revision))


class RemoveTagDialog(Gtk.Dialog):
    """ Confirm removal of tag. """
    def __init__(self, tagname, parent):
        super(RemoveTagDialog, self).__init__(
            title="Remove tag", parent=parent, flags=0,
            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))

        # Get the arguments
        self.tag = tagname

        # Create the widgets
        self._hbox = Gtk.HBox()
        self._vbox_question = Gtk.VBox()
        self._image_question = Gtk.Image.new_from_stock(Gtk.STOCK_DIALOG_QUESTION,
                                                        Gtk.IconSize.DIALOG)
        self._label_title = Gtk.Label()
        self._label_question = Gtk.Label()
        self._button_remove = Gtk.Button(_i18n("_Remove tag"), use_underline=True)

        # Set callbacks
        self._button_remove.connect('clicked', self._on_remove_clicked)

        # Set properties
        self._hbox.set_border_width(5)
        self._hbox.set_spacing(5)
        self._vbox_question.set_spacing(3)

        self._label_title.set_markup(_i18n("<b><big>Remove tag?</big></b>"))
        self._label_title.set_alignment(0.0, 0.5)
        self._label_question.set_markup(_i18n("Are you sure you want to remove the tag: <b>%s</b>?") % self.tag)
        self._label_question.set_alignment(0.0, 0.5)

        self._button_remove.set_image(Gtk.Image.new_from_stock(Gtk.STOCK_REMOVE,
                                                               Gtk.IconSize.BUTTON))
        self._button_remove.set_can_default(True)

        # Construct the dialog
        self._vbox_question.pack_start(self._label_title, True, True, 0)
        self._vbox_question.pack_start(self._label_question, True, True, 0)

        self._hbox.pack_start(self._image_question, True, True, 0)
        self._hbox.pack_start(self._vbox_question, True, True, 0)

        self.get_content_area().add(self._hbox)

        self.action_area.pack_end(self._button_remove, False, False, 0)

        # Display dialog
        self.get_content_area().show_all()

        # Default to Commit button
        self._button_remove.grab_default()

    def _on_remove_clicked(self, widget):
        """ Remove button event handler. """
        self.response(Gtk.ResponseType.OK)


class AddTagDialog(Gtk.Dialog):
    """ Add tag dialog. """

    def __init__(self, repository, revid=None, branch=None, parent=None):
        """ Initialize Add tag dialog. """
        super(AddTagDialog, self).__init__(
            title="Add tag", parent=parent, flags=0,
            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))

        # Get arguments
        self._repository = repository
        self._revid = revid
        self._branch = branch

        # Create the widgets
        self._button_add = Gtk.Button(_i18n("_Add tag"), use_underline=True)
        self._table = Gtk.Table(2, 2)
        self._label_name = Gtk.Label(label=_i18n("Tag Name:"))
        self._label_revid = Gtk.Label(label=_i18n("Revision ID:"))
        self._entry_name = Gtk.Entry()
        if self._revid is not None:
            self._hbox_revid = Gtk.Label(label=self._revid)
        else:
            self._hbox_revid = RevisionSelectionBox(self._branch)

        # Set callbacks
        self._button_add.connect('clicked', self._on_add_clicked)

        # Set properties
        self._label_name.set_alignment(0, 0.5)
        self._label_revid.set_alignment(0, 0.5)
        self._button_add.set_image(Gtk.Image.new_from_stock(Gtk.STOCK_ADD,
                                                            Gtk.IconSize.BUTTON))
        self._button_add.set_can_default(True)

        # Construct the dialog
        self._table.attach(self._label_name, 0, 1, 0, 1)
        self._table.attach(self._label_revid, 0, 1, 1, 2)
        self._table.attach(self._entry_name, 1, 2, 0, 1)
        self._table.attach(self._hbox_revid, 1, 2, 1, 2)
        self.get_content_area().add(self._table)
        self.action_area.pack_end(self._button_add, False, False, 0)

        # Show the dialog
        self.get_content_area().show_all()

    def _on_add_clicked(self, widget):
        """ Add button clicked handler. """
        if len(self._entry_name.get_text()) == 0:
            error_dialog(_i18n("No tag name specified"),
                         _i18n("You have to specify the tag's desired name."))
            return

        if self._revid is None:
            if self._hbox_revid.get_revision_id() is None:
                self._revid = self._branch.last_revision()
            else:
                self._revid = self._hbox_revid.get_revision_id()

        self.tagname = self._entry_name.get_text()

        self.response(Gtk.ResponseType.OK)
