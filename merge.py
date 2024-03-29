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

import os

from gi.repository import Gtk

from bzrlib.branch import Branch
import bzrlib.errors as errors

from bzrlib.plugins.gtk import icon_path
from bzrlib.plugins.gtk.dialog import (
    error_dialog,
    info_dialog,
    warning_dialog,
    )
from bzrlib.plugins.gtk.errors import show_bzr_error
from bzrlib.plugins.gtk.i18n import _i18n


class MergeDialog(Gtk.Dialog):
    """ Display the Merge dialog and perform the needed actions. """
    
    def __init__(self, wt, wtpath, default_branch_path=None, parent=None):
        """ Initialize the Merge dialog. """
        super(MergeDialog, self).__init__(
            title="Merge changes", parent=parent, flags=0,
            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))
        self.set_icon_from_file(icon_path("bzr-icon-64.png"))
        # Get arguments
        self.wt = wt
        self.wtpath = wtpath
        self.default_branch_path = default_branch_path
        self.parent_window = parent
        
        # Create widgets
        self._hbox = Gtk.HBox()
        self._source = Gtk.HBox()
        self._label_merge_from = Gtk.Label(label=_i18n("Merge from"))
        self._combo_source = Gtk.ComboBoxText()
        for entry in [_i18n("Folder"),_i18n("Custom Location")]:
            self._combo_source.append_text(entry)
        self._combo_source.connect("changed", self._on_combo_changed)
        self._button_merge = Gtk.Button(_i18n("_Merge"), use_underline=True)
        self._button_merge_icon = Gtk.Image()
        self._button_merge_icon.set_from_stock(Gtk.STOCK_APPLY, Gtk.IconSize.BUTTON)
        self._button_merge.set_image(self._button_merge_icon)
        self._button_merge.connect('clicked', self._on_merge_clicked)
        
        # Add widgets to dialog
        self.get_content_area().pack_start(self._hbox, False, False, 0)
        self._hbox.add(self._label_merge_from)
        self._hbox.add(self._combo_source)
        self._hbox.set_spacing(5)
        self.action_area.pack_end(self._button_merge, False, False, 0)
        
        if self.default_branch_path and os.path.isdir(
                            self.default_branch_path.partition('file://')[2]):
            self.directory = self.default_branch_path.partition('file://')[2]
            self._combo_source.set_active(0)
        elif self.default_branch_path:
            self._combo_source.set_active(1)
        else:
            # If no default_branch_path give, default to folder source with current folder
            self._combo_source.set_active(0)
        self.get_content_area().show_all()
    
    def _on_folder_source(self):
        """ Merge from folder, create a filechooser dialog and button """
        self._source = Gtk.HBox()
        self._filechooser_dialog = Gtk.FileChooserDialog(title="Please select a folder",
                                    parent=self.parent_window,
                                    action=Gtk.FileChooserAction.SELECT_FOLDER,
                                    buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        self._filechooser_dialog.set_default_response(Gtk.ResponseType.OK)
        self._filechooser = Gtk.FileChooserButton(self._filechooser_dialog)
        self._filechooser.show()
        directory = getattr(self, 'directory', None)
        if not directory:
            directory = os.path.dirname(self.wt.abspath(self.wtpath))
        self._filechooser_dialog.set_current_folder(directory)
        self._source.pack_start(self._filechooser, True, True, 0)
        self.get_content_area().pack_start(self._source, True, True, 5)
        self._source.show()
    
    def _on_custom_source(self):
        """ Merge from a custom source (can be folder, remote, etc), create entry """
        self._source = Gtk.HBox()
        self._custom_entry = Gtk.Entry()
        if self.default_branch_path:
            self._custom_entry.set_text(self.default_branch_path)
        self._custom_entry.connect("activate", self._on_merge_clicked)
        self._custom_entry.show()
        self._source.pack_start(self._custom_entry, True, True, 0)
        self.get_content_area().pack_start(self._source, True, True, 5)
        self._source.show()
    
    def _on_combo_changed(self, widget):
        merge_source = self._combo_source.get_active()
        self._source.destroy()
        if merge_source == 0:
            # Merge from folder
            self._on_folder_source()
        elif merge_source == 1:
            # Merge from custom
            self._on_custom_source()
    
    @show_bzr_error
    def _on_merge_clicked(self, widget):
        merge_source = self._combo_source.get_active()
        if merge_source == 0:
            branch = self._filechooser.get_filename()
        elif merge_source == 1:
            branch = self._custom_entry.get_text()
        if branch == "":
            error_dialog(_i18n('Branch not given'),
                         _i18n('Please specify a branch to merge from.'))
            return

        other_branch = Branch.open_containing(branch)[0]

        try:
            conflicts = self.wt.merge_from_branch(other_branch)
        except errors.BzrCommandError, errmsg:
            error_dialog(_i18n('Bazaar command error'), str(errmsg))
            return
        
        if conflicts == 0:
            # No conflicts found.
            info_dialog(_i18n('Merge successful'),
                        _i18n('All changes applied successfully.'))
        else:
            # There are conflicts to be resolved.
            warning_dialog(_i18n('Conflicts encountered'),
                           _i18n('Please resolve the conflicts manually before committing.'))
        
        self.response(Gtk.ResponseType.OK)
