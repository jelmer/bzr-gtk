# Copyright (C) 2008 Jelmer Vernooij <jelmer@samba.org>
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

from gi.repository import Gtk

import bzrlib.plugins.gtk
from bzrlib.plugins.gtk.notify import (
    has_avahi,
    has_dbus,
    )


def has_email():
    return (getattr(bzrlib.plugins, "email", None) is not None)

def has_cia():
    return (getattr(bzrlib.plugins, "cia", None) is not None)


class NotificationsPage(Gtk.VBox):

    def __init__(self, config, homogeneous=False, spacing=6):
        self.config = config
        GObject.GObject.__init__(self, homogeneous=homogeneous, spacing=spacing)
        self.set_spacing(spacing) # The vertical one

        lan_frame = Gtk.Frame("LAN Notifications")

        lan_vbox = Gtk.VBox()
        lan_frame.add(lan_vbox)

        self.gateway_to_lan = Gtk.CheckButton("_Gateway to LAN")
        lan_vbox.pack_start(self.gateway_to_lan, True, True, 0)
        self.gateway_to_lan.set_sensitive(has_dbus())

        self.announce_on_lan = Gtk.CheckButton("_Announce on LAN")
        lan_vbox.pack_start(self.announce_on_lan, True, True, 0)
        self.announce_on_lan.set_sensitive(has_avahi())

        self.pack_start(lan_frame, True, True, 0)

        email_frame = Gtk.Frame("E-mail notifications")

        email_hbox = Gtk.HBox()
        self.send_email = Gtk.CheckButton("Send _E-Mail to")
        email_hbox.pack_start(self.send_email, True, True, 0)
        self.send_email_to = Gtk.Entry()
        email_hbox.pack_start(self.send_email_to, True, True, 0)

        email_frame.add(email_hbox)
        email_frame.set_sensitive(has_email())

        self.pack_start(email_frame, True, True, 0)

        cia_frame = Gtk.Frame("CIA notifications")

        cia_user_hbox = Gtk.HBox()
        cia_user_hbox.pack_start(Gtk.Label("Author name", True, True, 0))
        self.cia_user = Gtk.Entry()
        cia_user_hbox.pack_start(self.cia_user, True, True, 0)

        cia_frame.add(cia_user_hbox)
        cia_frame.set_sensitive(has_cia())

        self.pack_start(cia_frame, True, True, 0)
