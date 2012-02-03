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

import os
import subprocess

from bzrlib import tests
from bzrlib.plugins.gtk.notify import NotifyPopupMenu


class FakeNotifyPopupMenu(NotifyPopupMenu):

    SHOW_WIDGETS = False


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


class BzrNotifyTestCase(tests.TestCase):

    def test_smoketest(self):
        # This is a smoke test to verify the process starts.
        # The logic of the module must be moved into notify.py
        # where it can be properly tested.
        script = os.path.join(
            os.path.dirname(__file__), os.pardir, 'bzr-notify')
        bzr_notify = subprocess.Popen(
            [script, 'test'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = bzr_notify.communicate()
        self.assertEqual('', stdout)
        self.assertEqual('', stderr)
