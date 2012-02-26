# Copyright (C) 2012 Curtis Hovey <sinzui.is@verizon.net>
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

"""Test the ui functionality."""

from bzrlib import (
    tests,
    )

from bzrlib.plugins.gtk import ui


class GtkUIFactoryTestCase(tests.TestCase):

    def test__init(self):
        ui_factory = ui.GtkUIFactory()
        self.assertIs(None, ui_factory._progress_bar_widget)

    def test_set_progress_bar_widget(self):
        ui_factory = ui.GtkUIFactory()
        progress_widget = ui.ProgressPanel()
        ui_factory.set_progress_bar_widget(progress_widget)
        self.assertIs(progress_widget, ui_factory._progress_bar_widget)
