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

from graph import distances, graph, same_branch
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
        monitor = screen.get_monitor_geometry(0)
        width = int(monitor.width * 0.75)
        height = int(monitor.height * 0.75)
        self.set_default_size(width, height)

        # FIXME AndyFitz!
        icon = self.render_icon(gtk.STOCK_INDEX, gtk.ICON_SIZE_BUTTON)
        self.set_icon(icon)

        self.accel_group = gtk.AccelGroup()
        self.add_accel_group(self.accel_group)

        self.construct()

    def construct(self):
        """Construct the window contents."""
        paned = gtk.VPaned()
        paned.pack1(self.construct_top(), resize=True, shrink=False)
        paned.pack2(self.construct_bottom(), resize=True, shrink=True)
        self.add(paned)
        paned.show()

    def construct_top(self):
        """Construct the top-half of the window."""
        vbox = gtk.VBox(spacing=6)
        vbox.set_border_width(12)
        vbox.show()

        scrollwin = gtk.ScrolledWindow()
        scrollwin.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scrollwin.set_shadow_type(gtk.SHADOW_IN)
        vbox.pack_start(scrollwin, expand=True, fill=True)
        scrollwin.show()

        self.treeview = gtk.TreeView()
        self.treeview.set_rules_hint(True)
        self.treeview.set_search_column(4)
        self.treeview.connect("cursor-changed", self._treeview_cursor_cb)
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

        hbox = gtk.HBox(False, spacing=6)
        vbox.pack_start(hbox, expand=False, fill=False)
        hbox.show()

        self.back_button = gtk.Button(stock=gtk.STOCK_GO_BACK)
        self.back_button.add_accelerator("clicked", self.accel_group, ord('['),
                                         0, 0)
        self.back_button.connect("clicked", self._back_clicked_cb)
        hbox.pack_start(self.back_button, expand=False, fill=True)
        self.back_button.show()

        self.fwd_button = gtk.Button(stock=gtk.STOCK_GO_FORWARD)
        self.fwd_button.add_accelerator("clicked", self.accel_group, ord(']'),
                                        0, 0)
        self.fwd_button.connect("clicked", self._fwd_clicked_cb)
        hbox.pack_start(self.fwd_button, expand=False, fill=True)
        self.fwd_button.show()

        return vbox

    def construct_bottom(self):
        """Construct the bottom half of the window."""
        label = gtk.Label("test")
        label.show()

        return label

    def set_branch(self, branch, start):
        """Set the branch and start position for this window.

        Creates a new TreeModel and populates it with information about
        the new branch before updating the window title and model of the
        treeview itself.
        """
        # [ revision, node, last_lines, lines, message, committer, timestamp ]
        self.model = gtk.ListStore(gobject.TYPE_PYOBJECT,
                                   gobject.TYPE_PYOBJECT,
                                   gobject.TYPE_PYOBJECT,
                                   gobject.TYPE_PYOBJECT,
                                   str, str, str)
        self.index = {}
        index = 0

        last_lines = []
        (revids, self.revisions, colours, self.children) \
                 = distances(branch, start)
        for revision, node, lines in graph(revids, self.revisions, colours):
            message = revision.message.split("\n")[0]
            if revision.committer is not None:
                timestamp = format_date(revision.timestamp, revision.timezone)
            else:
                timestamp = None

            self.model.append([ revision, node, last_lines, lines,
                                message, revision.committer, timestamp ])
            self.index[revision] = index
            index += 1

            last_lines = lines

        self.set_title(os.path.basename(branch.base) + " - bzrk")
        self.treeview.set_model(self.model)

    def _treeview_cursor_cb(self, *args):
        """Callback for when the treeview cursor changes."""
        (path, col) = self.treeview.get_cursor()
        revision = self.model[path][0]

        self.back_button.set_sensitive(len(revision.parent_ids) > 0)
        self.fwd_button.set_sensitive(len(self.children[revision]) > 0)

    def _back_clicked_cb(self, *args):
        """Callback for when the back button is clicked."""
        (path, col) = self.treeview.get_cursor()
        revision = self.model[path][0]
        if not len(revision.parent_ids):
            return

        for parent_id in revision.parent_ids:
            parent = self.revisions[parent_id]
            if same_branch(revision, parent):
                self.treeview.set_cursor(self.index[parent])
                break
        else:
            next = self.revisions[revision.parent_ids[0]]
            self.treeview.set_cursor(self.index[next])

    def _fwd_clicked_cb(self, *args):
        """Callback for when the forward button is clicked."""
        (path, col) = self.treeview.get_cursor()
        revision = self.model[path][0]
        if not len(self.children[revision]):
            return

        for child in self.children[revision]:
            if same_branch(child, revision):
                self.treeview.set_cursor(self.index[child])
                break
        else:
            prev = list(self.children[revision])[0]
            self.treeview.set_cursor(self.index[prev])
