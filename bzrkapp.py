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
        self._num_windows += 1

        window = BranchWindow()
        window.set_branch(branch, start)
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
