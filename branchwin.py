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

    def __init__(self, app=None):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.set_border_width(0)
        self.set_title("bzrk")

        self.app = app

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
        paned.pack2(self.construct_bottom(), resize=False, shrink=True)
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
        vbox = gtk.VBox(False, spacing=6)
        vbox.set_border_width(12)
        (width, height) = self.get_size()
        vbox.set_size_request(width, int(height / 2.5))
        vbox.show()

        self.table = gtk.Table(rows=5, columns=2)
        self.table.set_row_spacings(6)
        self.table.set_col_spacings(6)
        vbox.pack_start(self.table, expand=False, fill=True)
        self.table.show()

        align = gtk.Alignment(0.0, 0.5)
        label = gtk.Label()
        label.set_markup("<b>Revision:</b>")
        align.add(label)
        self.table.attach(align, 0, 1, 0, 1, gtk.FILL, gtk.FILL)
        label.show()
        align.show()

        align = gtk.Alignment(0.0, 0.5)
        self.revid_label = gtk.Label()
        self.revid_label.set_selectable(True)
        align.add(self.revid_label)
        self.table.attach(align, 1, 2, 0, 1, gtk.EXPAND | gtk.FILL, gtk.FILL)
        self.revid_label.show()
        align.show()

        align = gtk.Alignment(0.0, 0.5)
        label = gtk.Label()
        label.set_markup("<b>Committer:</b>")
        align.add(label)
        self.table.attach(align, 0, 1, 1, 2, gtk.FILL, gtk.FILL)
        label.show()
        align.show()

        align = gtk.Alignment(0.0, 0.5)
        self.committer_label = gtk.Label()
        self.committer_label.set_selectable(True)
        align.add(self.committer_label)
        self.table.attach(align, 1, 2, 1, 2, gtk.EXPAND | gtk.FILL, gtk.FILL)
        self.committer_label.show()
        align.show()

        align = gtk.Alignment(0.0, 0.5)
        label = gtk.Label()
        label.set_markup("<b>Branch nick:</b>")
        align.add(label)
        self.table.attach(align, 0, 1, 2, 3, gtk.FILL, gtk.FILL)
        label.show()
        align.show()

        align = gtk.Alignment(0.0, 0.5)
        self.branchnick_label = gtk.Label()
        self.branchnick_label.set_selectable(True)
        align.add(self.branchnick_label)
        self.table.attach(align, 1, 2, 2, 3, gtk.EXPAND | gtk.FILL, gtk.FILL)
        self.branchnick_label.show()
        align.show()

        align = gtk.Alignment(0.0, 0.5)
        label = gtk.Label()
        label.set_markup("<b>Timestamp:</b>")
        align.add(label)
        self.table.attach(align, 0, 1, 3, 4, gtk.FILL, gtk.FILL)
        label.show()
        align.show()

        align = gtk.Alignment(0.0, 0.5)
        self.timestamp_label = gtk.Label()
        self.timestamp_label.set_selectable(True)
        align.add(self.timestamp_label)
        self.table.attach(align, 1, 2, 3, 4, gtk.EXPAND | gtk.FILL, gtk.FILL)
        self.timestamp_label.show()
        align.show()

        align = gtk.Alignment(0.0, 0.5)
        label = gtk.Label()
        label.set_markup("<b>Parents:</b>")
        align.add(label)
        self.table.attach(align, 0, 1, 4, 5, gtk.FILL, gtk.FILL)
        label.show()
        align.show()

        self.parents_widgets = []

        scrollwin = gtk.ScrolledWindow()
        scrollwin.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scrollwin.set_shadow_type(gtk.SHADOW_IN)
        vbox.pack_start(scrollwin, expand=True, fill=True)
        scrollwin.show()

        self.message_buffer = gtk.TextBuffer()
        textview = gtk.TextView(self.message_buffer)
        textview.set_editable(False)
        textview.set_wrap_mode(gtk.WRAP_WORD)
        textview.modify_font(pango.FontDescription("Monospace"))
        scrollwin.add(textview)
        textview.show()

        return vbox

    def set_branch(self, branch, start, robust, maxnum):
        """Set the branch and start position for this window.

        Creates a new TreeModel and populates it with information about
        the new branch before updating the window title and model of the
        treeview itself.
        """
        self.branch = branch

        # [ revision, node, last_lines, lines, message, committer, timestamp ]
        self.model = gtk.ListStore(gobject.TYPE_PYOBJECT,
                                   gobject.TYPE_PYOBJECT,
                                   gobject.TYPE_PYOBJECT,
                                   gobject.TYPE_PYOBJECT,
                                   str, str, str)
        self.index = {}
        index = 0

        last_lines = []
        (self.revisions, colours, self.children, self.parent_ids, merge_sorted) \
                 = distances(branch, start, robust, maxnum)
        for revision, node, lines in graph(
                self.revisions, colours, self.parent_ids, merge_sorted):
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

        self.set_title(branch.nick + " - bzrk")
        self.treeview.set_model(self.model)

    def _treeview_cursor_cb(self, *args):
        """Callback for when the treeview cursor changes."""
        (path, col) = self.treeview.get_cursor()
        revision = self.model[path][0]

        self.back_button.set_sensitive(len(self.parent_ids[revision]) > 0)
        self.fwd_button.set_sensitive(len(self.children[revision]) > 0)

        if revision.committer is not None:
            branchnick = ""
            committer = revision.committer
            timestamp = format_date(revision.timestamp, revision.timezone)
            message = revision.message
            try:
                branchnick = revision.properties['branch-nick']
            except KeyError:
                pass

        else:
            committer = ""
            timestamp = ""
            message = ""
            branchnick = ""

        self.revid_label.set_text(revision.revision_id)
        self.branchnick_label.set_text(branchnick)

        self.committer_label.set_text(committer)
        self.timestamp_label.set_text(timestamp)
        self.message_buffer.set_text(message)

        for widget in self.parents_widgets:
            self.table.remove(widget)

        self.parents_widgets = []
        self.table.resize(5 + len(self.parent_ids[revision]) - 1, 2)
        for idx, parent_id in enumerate(self.parent_ids[revision]):
            self.table.set_row_spacing(idx + 3, 0)

            align = gtk.Alignment(0.0, 0.0)
            self.parents_widgets.append(align)
            self.table.attach(align, 1, 2, idx + 4, idx + 5,
                              gtk.EXPAND | gtk.FILL, gtk.FILL)
            align.show()

            hbox = gtk.HBox(False, 0)
            align.add(hbox)
            hbox.show()

            label = gtk.Label(parent_id)
            label.set_selectable(True)
            hbox.pack_start(label, expand=False, fill=True)
            label.show()

            image = gtk.Image()
            image.set_from_stock(gtk.STOCK_JUMP_TO, gtk.ICON_SIZE_MENU)
            image.show()

            button = gtk.Button()
            button.add(image)
            button.set_relief(gtk.RELIEF_NONE)
            button.connect("clicked", self._go_clicked_cb, parent_id)
            hbox.pack_start(button, expand=False, fill=True)
            button.show()

            image = gtk.Image()
            image.set_from_stock(gtk.STOCK_FIND, gtk.ICON_SIZE_MENU)
            image.show()

            button = gtk.Button()
            button.add(image)
            button.set_relief(gtk.RELIEF_NONE)
            button.set_sensitive(self.app is not None)
            button.connect("clicked", self._show_clicked_cb,
                           revision.revision_id, parent_id)
            hbox.pack_start(button, expand=False, fill=True)
            button.show()

    def _back_clicked_cb(self, *args):
        """Callback for when the back button is clicked."""
        (path, col) = self.treeview.get_cursor()
        revision = self.model[path][0]
        if not len(self.parent_ids[revision]):
            return

        for parent_id in self.parent_ids[revision]:
            parent = self.revisions[parent_id]
            if same_branch(revision, parent):
                self.treeview.set_cursor(self.index[parent])
                break
        else:
            next = self.revisions[self.parent_ids[revision][0]]
            self.treeview.set_cursor(self.index[next])
        self.treeview.grab_focus()

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
        self.treeview.grab_focus()

    def _go_clicked_cb(self, widget, revid):
        """Callback for when the go button for a parent is clicked."""
        self.treeview.set_cursor(self.index[self.revisions[revid]])
        self.treeview.grab_focus()

    def _show_clicked_cb(self, widget, revid, parentid):
        """Callback for when the show button for a parent is clicked."""
        if self.app is not None:
            self.app.show_diff(self.branch, revid, parentid)
        self.treeview.grab_focus()
