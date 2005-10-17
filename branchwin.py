#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""Branch window.

This module contains the code to manage the branch information window,
which contains both the revision graph and details panes.
"""

__copyright__ = "Copyright © 2005 Canonical Ltd."
__author__    = "Scott James Remnant <scott@ubuntu.com>"


import os

import gtk
import gobject
import pango

from bzrlib.osutils import format_date

from graph import graph
from graphcell import CellRendererGraph


class BranchWindow(gtk.Window):
    """Branch window.

    This object represents and manages a single window containing information
    for a particular branch.
    """

    def __init__(self):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.set_border_width(0)
        self.set_title("bzrk")

        # Use three-quarters of the screen by default
        screen = self.get_screen()
        width = int(screen.get_width() * 0.75)
        height = int(screen.get_height() * 0.75)
        self.set_default_size(width, height)

        # FIXME AndyFitz!
        icon = self.render_icon(gtk.STOCK_INDEX, gtk.ICON_SIZE_BUTTON)
        self.set_icon(icon)

        self.construct()

    def construct(self):
        """Construct the window contents."""
        scrollwin = gtk.ScrolledWindow()
        scrollwin.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scrollwin.set_shadow_type(gtk.SHADOW_IN)
        scrollwin.set_border_width(12)
        self.add(scrollwin)
        scrollwin.show()

        self.treeview = gtk.TreeView()
        self.treeview.set_rules_hint(True)
        self.treeview.set_search_column(4)
        scrollwin.add(self.treeview)
        self.treeview.show()

        cell = CellRendererGraph()
        column = gtk.TreeViewColumn()
        column.set_resizable(False)
        column.pack_start(cell, expand=False)
        column.add_attribute(cell, "node", 1)
        column.add_attribute(cell, "in-lines", 2)
        column.add_attribute(cell, "out-lines", 3)
        self.treeview.append_column(column)

        cell = gtk.CellRendererText()
        cell.set_property("width-chars", 40)
        cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        column = gtk.TreeViewColumn("Message")
        column.set_resizable(True)
        column.pack_start(cell, expand=True)
        column.add_attribute(cell, "text", 4)
        self.treeview.append_column(column)

        cell = gtk.CellRendererText()
        cell.set_property("width-chars", 40)
        cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        column = gtk.TreeViewColumn("Committer")
        column.set_resizable(True)
        column.pack_start(cell, expand=True)
        column.add_attribute(cell, "text", 5)
        self.treeview.append_column(column)

        cell = gtk.CellRendererText()
        cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        column = gtk.TreeViewColumn("Date")
        column.set_resizable(True)
        column.pack_start(cell, expand=True)
        column.add_attribute(cell, "text", 6)
        self.treeview.append_column(column)

    def set_branch(self, branch, start):
        """Set the branch and start position for this window.

        Creates a new TreeModel and populates it with information about
        the new branch before updating the window title and model of the
        treeview itself.
        """
        # [ revision, node, last_lines, lines, message, committer, timestamp ]
        model = gtk.ListStore(gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT,
                              gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT,
                              str, str, str)

        last_lines = []
        for revision, node, lines in graph(branch, start):
            message = revision.message.split("\n")[0]
            if revision.committer is not None:
                timestamp = format_date(revision.timestamp, revision.timezone)
            else:
                timestamp = None

            model.append([ revision, node, last_lines, lines,
                           message, revision.committer, timestamp ])
            last_lines = lines

        self.set_title(os.path.basename(branch.base) + " - bzrk")
        self.treeview.set_model(model)
