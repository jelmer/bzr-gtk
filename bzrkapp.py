#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""Application object.

This module contains the application object that manages the windows
on screen, and can be used to create new windows of various types.
"""

__copyright__ = "Copyright © 2005 Canonical Ltd."
__author__    = "Scott James Remnant <scott@ubuntu.com>"


import pygtk
pygtk.require("2.0")

import gtk

from branchwin import BranchWindow
from diffwin import DiffWindow


class BzrkApp(object):
    """Application manager.

    This object manages the bzrk application, creating and managing
    individual branch windows and ensuring the application exits when
    the last window is closed.
    """

    def __init__(self):
        self._num_windows = 0

    def show(self, branch, start):
        """Open a new window to show the given branch."""
        window = BranchWindow(self)
        window.set_branch(branch, start)

        self._num_windows += 1
        window.connect("destroy", self._destroy_cb)
        window.show()

    def show_diff(self, branch, revid, parentid):
        """Open a new window to show a diff between the given revisions."""
        window = DiffWindow(self)
        window.set_diff(branch, revid, parentid)

        self._num_windows += 1
        window.connect("destroy", self._destroy_cb)
        window.show()

    def _destroy_cb(self, widget):
        """Callback for when a window we manage is destroyed."""
        self._num_windows -= 1
        if self._num_windows <= 0:
            self.quit()

    def main(self):
        """Start the GTK+ main loop."""
        gtk.main()

    def quit(self):
        """Stop the GTK+ main loop."""
        gtk.main_quit()
