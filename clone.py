# Copyright (C) 2006 Jelmer Vernooij <jelmer@samba.org>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import pygtk
pygtk.require("2.0")
import gobject
import gtk
import pango
from bzrlib.delta import compare_trees

#FIXME: Allow specifying stop_revision
#FIXME: Allow specifying target branch format
#FIXME: Implement _Browse callback

class CloneDialog(gtk.Dialog):
    """ Branch (clone) Dialog """

    def __init__(self, dest_path=None):
        gtk.Dialog.__init__(self)

        self.set_default_size(400, 200)

        self._create()

        if dest_path:
            self.url_entry.set_text(dest_path)

    def _get_url(self):
        return self.url_entry.get_text()

    def _get_dest_path(self):
        return self.path_entry.get_text()

    dest_path = property(_get_dest_path)
    url = property(_get_url)

    def _browse_cb(self, *args):
        #FIXME
        pass

    def _create(self):
        frame = gtk.Frame(label="Branch URL")
        self.vbox.pack_start(frame, fill=True)
        self.url_entry = gtk.Entry()
        frame.add(self.url_entry)
        frame.show_all()

        frame = gtk.Frame(label="Destination Path")
        self.vbox.pack_start(frame, fill=True)
        hbox = gtk.HBox()
        self.path_entry = gtk.Entry()
        hbox.add(self.path_entry)
        hbox.add(gtk.Button(label="_Browse"))
        frame.add(hbox)
        frame.show_all()

        frame = gtk.Frame(label="Options")
        self.vbox.pack_start(frame)
        vbox = gtk.VBox()
        self.lightweight_button = gtk.CheckButton(label="Lightweight")
        vbox.add(self.lightweight_button)
        frame.add(vbox)
        frame.show_all()

        self.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, "_Get", gtk.RESPONSE_OK)
                         
