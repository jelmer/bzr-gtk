# Copyright (C) 2005 Dan Loda <danloda@gmail.com>

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

import os

from bzrlib.config import config_dir
import bzrlib.util.configobj.configobj as configobj
from bzrlib.util.configobj.validate import Validator


gannotate_configspec = (
    "[window]",
    "width = integer(default=750)",
    "height = integer(default=550)",
    "x = integer(default=0)",
    "y = integer(default=0)",
    "pane_position = integer(default=325)"
)

gannotate_config_filename = os.path.join(config_dir(), "gannotate.conf")


class GAnnotateConfig(configobj.ConfigObj):
    """gannotate configuration wrangler.

    Staying as far out of the way as possible, hanging about catching events
    and saving only what's necessary. Writes gannotate.conf when the gannotate
    window is destroyed. Initializes saved properties when instantiated.
    """

    def __init__(self, window):
        configobj.ConfigObj.__init__(self, gannotate_config_filename,
                                     configspec=gannotate_configspec)
        self.window = window
        self.pane = window.pane
        
        self.initial_comment = ["gannotate plugin configuration"]
        self.validate(Validator())

        self._connect_signals()
        self.apply()

    def apply(self):
        """Apply properties and such from gannotate.conf, or
        gannotate_config_spec defaults."""
        self.window.resize(self["window"]["width"], self["window"]["height"])
        self.window.move(self["window"]["x"], self["window"]["y"])
        self.pane.set_position(self["window"]["pane_position"])

    def _connect_signals(self):
        self.window.connect("destroy", self._write)
        self.window.connect("delete-event", self._save_window_props)
        self.window.connect("configure-event", self._save_window_props)
        self.pane.connect("delete-event", self._save_pane_props)
        self.pane.connect("notify", self._save_pane_props)

    def _save_window_props(self, w, *args):
        self["window"]["width"], self["window"]["height"] = w.get_size()
        self["window"]["x"], self["window"]["y"] = w.get_position()
        
        return False

    def _save_pane_props(self, w, *args):
        self["window"]["pane_position"] = w.get_position()

        return False

    def _write(self, *args):
        self.write()

        return False

