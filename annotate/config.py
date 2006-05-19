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

import gtk.gdk

from bzrlib.config import config_dir
import bzrlib.util.configobj.configobj as configobj
from bzrlib.util.configobj.validate import Validator


gannotate_configspec = (
    "[window]",
    "width = integer(default=750)",
    "height = integer(default=550)",
    "maximized = boolean(default=False)",
    "x = integer(default=0)",
    "y = integer(default=0)",
    "pane_position = integer(default=325)",
    "[spans]",
    "max_custom_spans = integer(default=4)",
    "custom_spans = float_list()"
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
        self.span_selector = window.span_selector
        
        self.initial_comment = ["gannotate plugin configuration"]
        self.validate(Validator())

        self.apply()
        self._connect_signals()

    def apply(self):
        """Apply properties and such from gannotate.conf, or
        gannotate_configspec defaults."""
        self.pane.set_position(self["window"]["pane_position"])
        self.window.set_default_size(self["window"]["width"],
                                     self["window"]["height"])
        self.window.move(self["window"]["x"], self["window"]["y"])

        if self["window"]["maximized"]:
            self.window.maximize()

        self.span_selector.max_custom_spans =\
                self["spans"]["max_custom_spans"]

        # XXX Don't know how to set an empty list as default in
        # gannotate_configspec.
        try:
            for span in self["spans"]["custom_spans"]:
                self.span_selector.add_custom_span(span)
        except KeyError:
            pass

    def _connect_signals(self):
        self.window.connect("destroy", self._write)
        self.window.connect("configure-event", self._save_window_props)
        self.window.connect("window-state-event", self._save_window_props)
        self.pane.connect("notify", self._save_pane_props)
        self.span_selector.connect("custom-span-added",
                                   self._save_custom_spans)

    def _save_window_props(self, w, e, *args):
        if e.window.get_state() & gtk.gdk.WINDOW_STATE_MAXIMIZED:
            maximized = True
        else:
            self["window"]["width"], self["window"]["height"] = w.get_size()
            self["window"]["x"], self["window"]["y"] = w.get_position()
            maximized = False

        self["window"]["maximized"] = maximized
        
        return False

    def _save_pane_props(self, w, gparam):
        if gparam.name == "position":
            self["window"]["pane_position"] = w.get_position()

        return False

    def _save_custom_spans(self, w, *args):
        self["spans"]["custom_spans"] = w.custom_spans

        return False

    def _write(self, *args):
        self.write()

        return False

