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

from gi.repository import Gtk

from bzrlib.config import GlobalConfig
from bzrlib.plugins.gtk.preferences.identity import IdentityPage
from bzrlib.plugins.gtk.preferences.plugins import PluginsPage

class PreferencesWindow(Gtk.Dialog):
    """Displays global preferences windows."""
    # Note that we don't allow configuration of aliases or
    # default log formats. This is because doing so wouldn't make
    # a lot of sense to pure GUI users. Users that need these settings
    # will already be familiar with the configuration file.

    def __init__(self, config=None):
        """ Initialize the Status window. """
        super(PreferencesWindow, self).__init__(flags=Gtk.DialogFlags.MODAL)
        self.set_title("Bazaar Preferences")
        self.config = config
        if self.config is None:
            self.config = GlobalConfig()
        self._create()

    def _create(self):
        self.set_default_size(320, 480)
        self.set_border_width(0)

        notebook = Gtk.Notebook()
        notebook.set_border_width(12)
        for (label, page) in self._create_pages():
            notebook.append_page(page, Gtk.Label(label=label))

        notebook.set_current_page(0)
        content_area = self.get_content_area()
        content_area.set_border_width(0)
        content_area.pack_start(notebook, True, True, 0)
        content_area.show_all()
        self.get_action_area().set_border_width(12)

    def _create_pages(self):
        return [("Identity", IdentityPage(self.config)),
                ("Plugins", PluginsPage())]

    def display(self):
        self.window.show_all()

    def close(self, widget=None):
        self.window.destroy()


class BranchPreferencesWindow(Gtk.Dialog):
    """Displays global preferences windows."""
    def __init__(self, config=None):
        super(BranchPreferencesWindow, self).__init__(config)

