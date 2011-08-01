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

from gi.repository import GObject
from gi.repository import Gtk

import os

from bzrlib import (
    bzrdir,
    errors,
    transport,
    )

from bzrlib.plugins.gtk.dialog import error_dialog
from bzrlib.plugins.gtk.errors import show_bzr_error
from bzrlib.plugins.gtk.i18n import _i18n


class InitDialog(Gtk.Dialog):
    """ Initialize dialog. """

    def __init__(self, path, parent=None):
        """ Initialize the Initialize dialog. """
        GObject.GObject.__init__(self, title="Initialize - Olive",
                                  parent=parent,
                                  flags=0,
                                  buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))
        
        # Get arguments
        self.path = path
        
        # Create the widgets
        self._button_init = Gtk.Button(_i18n("_Initialize"), use_underline=True)
        self._label_question = Gtk.Label(label=_i18n("Which directory do you want to initialize?"))
        self._radio_current = Gtk.RadioButton(None, _i18n("Current directory"))
        self._radio_custom = Gtk.RadioButton(self._radio_current, _i18n("Create a new directory with the name:"))
        self._entry_custom = Gtk.Entry()
        self._hbox_custom = Gtk.HBox()
        
        # Set callbacks
        self._button_init.connect('clicked', self._on_init_clicked)
        self._radio_custom.connect('toggled', self._on_custom_toggled)
        
        # Set properties
        self._entry_custom.set_sensitive(False)
        
        # Construct the dialog
        self.action_area.pack_end(self._button_init)
        
        self._hbox_custom.pack_start(self._radio_custom, False, False)
        self._hbox_custom.pack_start(self._entry_custom, True, True)
        
        self.vbox.pack_start(self._label_question, True, True, 0)
        self.vbox.pack_start(self._radio_current, True, True, 0)
        self.vbox.pack_start(self._hbox_custom, True, True, 0)
        
        # Display the dialog
        self.vbox.show_all()
    
    def _on_custom_toggled(self, widget):
        """ Occurs if the Custom radiobutton is toggled. """
        if self._radio_custom.get_active():
            self._entry_custom.set_sensitive(True)
            self._entry_custom.grab_focus()
        else:
            self._entry_custom.set_sensitive(False)
    
    @show_bzr_error
    def _on_init_clicked(self, widget):
        if self._radio_custom.get_active() and len(self._entry_custom.get_text()) == 0:
            error_dialog(_i18n("Directory name not specified"),
                         _i18n("You should specify a new directory name."))
            return
        
        if self._radio_current.get_active():
            location = self.path
        else:
            location = self.path + os.sep + self._entry_custom.get_text()
        
        format = bzrdir.format_registry.make_bzrdir('default')        
        to_transport = transport.get_transport(location)
        
        try:
            to_transport.mkdir('.')
        except errors.FileExists:
            pass
                    
        try:
            existing_bzrdir = bzrdir.BzrDir.open(location)
        except errors.NotBranchError:
            branch = bzrdir.BzrDir.create_branch_convenience(to_transport.base,
                                                             format=format)
        else:
            from bzrlib.transport.local import LocalTransport
            if existing_bzrdir.has_branch():
                if (isinstance(to_transport, LocalTransport)
                    and not existing_bzrdir.has_workingtree()):
                        raise errors.BranchExistsWithoutWorkingTree(location)
                raise errors.AlreadyBranchError(location)
            else:
                branch = existing_bzrdir.create_branch()
                existing_bzrdir.create_workingtree()
        
        self.response(Gtk.ResponseType.OK)
