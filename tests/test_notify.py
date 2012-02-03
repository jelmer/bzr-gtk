# -*- coding: utf-8 -*-
# Copyright (C) 2012 Curtis C. Hovey <sinzui.is@verizon.net>
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

from bzrlib import tests
from bzrlib.plugins.gtk.notify import NotifyPopupMenu


class FakeNotifyPopupMenu(NotifyPopupMenu):

    SHOW_WIDGETS = False


# ['_Gateway to LAN', '', 'Announce _branches on LAN', '', 'gtk-preferences', 'gtk-about', '', 'gtk-quit']

class NotifyPopupMenuTestCase(tests.TestCase):

    def test_init(self):
        menu = FakeNotifyPopupMenu()
        items = menu.get_children()
        self.assertEqual(8, len(items))
        self.assertEqual('_Gateway to LAN', items[0].props.label)
        self.assertEqual('Announce _branches on LAN', items[2].props.label)
        self.assertEqual('gtk-preferences', items[4].props.label)
        self.assertEqual('gtk-about', items[5].props.label)
        self.assertEqual('gtk-quit', items[7].props.label)
