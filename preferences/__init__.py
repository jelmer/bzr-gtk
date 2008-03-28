# Copyright (C) 2007 Jelmer Vernooij <jelmer@samba.org>
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

from bzrlib.config import GlobalConfig
from plugins import PluginsPage

class PreferencesWindow(gtk.Dialog):
    """Displays global preferences windows."""
    # Note that we don't allow configuration of aliases or 
    # default log formats. This is because doing so wouldn't make 
    # a lot of sense to pure GUI users. Users that need these settings 
    # will already be familiar with the configuration file.

    def __init__(self, config=None):
        """ Initialize the Status window. """
        super(PreferencesWindow, self).__init__(flags=gtk.DIALOG_MODAL)
        self.set_title("Bazaar Preferences")
        self.config = config
        if self.config is None:
            self.config = GlobalConfig()
        self._create()

    def _create_mainpage(self):
        table = gtk.Table(rows=4, columns=2)
        table.set_row_spacings(6)
        table.set_col_spacings(6)

        align = gtk.Alignment(1.0, 0.5)
        label = gtk.Label()
        label.set_markup("<b>User Id:</b>")
        align.add(label)
        table.attach(align, 0, 1, 0, 1, gtk.FILL, gtk.FILL)

        self.username = gtk.Entry()
        self.username.set_text(self.config.username())
        table.attach(self.username, 1, 2, 0, 1, gtk.EXPAND | gtk.FILL, gtk.FILL)

        align = gtk.Alignment(1.0, 0.5)
        label = gtk.Label()
        label.set_markup("<b>GPG signing command:</b>")
        align.add(label)
        table.attach(align, 0, 1, 1, 2, gtk.FILL, gtk.FILL)

        self.email = gtk.Entry()
        self.email.set_text(self.config.gpg_signing_command())
        table.attach(self.email, 1, 2, 1, 2, gtk.EXPAND | gtk.FILL, gtk.FILL)

        align = gtk.Alignment(1.0, 0.5)
        label = gtk.Label()
        label.set_markup("<b>Check GPG Signatures:</b>")
        align.add(label)
        table.attach(align, 0, 1, 2, 3, gtk.FILL, gtk.FILL)

        sigvals = gtk.VBox()
        self.check_sigs_if_possible = gtk.RadioButton(None, 
                                                      "_Check if possible")
        sigvals.pack_start(self.check_sigs_if_possible)
        self.check_sigs_always = gtk.RadioButton(self.check_sigs_if_possible, 
                                                 "Check _always")
        sigvals.pack_start(self.check_sigs_always)
        self.check_sigs_never = gtk.RadioButton(self.check_sigs_if_possible,
                                                "Check _never")
        sigvals.pack_start(self.check_sigs_never)
        # FIXME: Set default
        table.attach(sigvals, 1, 2, 2, 3, gtk.EXPAND | gtk.FILL, gtk.FILL)

        align = gtk.Alignment(1.0, 0.5)
        label = gtk.Label()
        label.set_markup("<b>Create GPG Signatures:</b>")
        align.add(label)
        table.attach(align, 0, 1, 3, 4, gtk.FILL, gtk.FILL)

        create_sigs = gtk.VBox()
        self.create_sigs_when_required = gtk.RadioButton(None, 
                                                         "Sign When _Required")
        create_sigs.pack_start(self.create_sigs_when_required)
        self.create_sigs_always = gtk.RadioButton(
            self.create_sigs_when_required, "Sign _Always")
        create_sigs.pack_start(self.create_sigs_always)
        self.create_sigs_never = gtk.RadioButton(
            self.create_sigs_when_required, "Sign _Never")
        create_sigs.pack_start(self.create_sigs_never)
        # FIXME: Set default
        table.attach(create_sigs, 1, 2, 3, 4, gtk.EXPAND | gtk.FILL, gtk.FILL)

        return table

    def _create(self):
        self.set_default_size(600, 600)
        notebook = gtk.Notebook()
        notebook.insert_page(self._create_mainpage(), gtk.Label("Main"))
        notebook.insert_page(PluginsPage(), gtk.Label("Plugins"))
        self.vbox.pack_start(notebook, True, True)
        self.vbox.show_all()

    def display(self):
        self.window.show_all()

    def close(self, widget=None):
        self.window.destroy()

class BranchPreferencesWindow(gtk.Dialog):
    """Displays global preferences windows."""
    def __init__(self, config=None):
        super(BranchPreferencesWindow, self).__init__(config)

