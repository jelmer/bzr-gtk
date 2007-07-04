#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""Difference window.

This module contains the code to manage the diff window which shows
the changes made between two revisions on a branch.
"""

__copyright__ = "Copyright © 2005 Canonical Ltd."
__author__    = "Scott James Remnant <scott@ubuntu.com>"


from cStringIO import StringIO

import gtk
import pango
import os
import re
import sys

try:
    import gtksourceview
    have_gtksourceview = True
except ImportError:
    have_gtksourceview = False

import bzrlib

from bzrlib.diff import show_diff_trees
from bzrlib.errors import NoSuchFile
from bzrlib.trace import warning


class DiffWindow(gtk.Window):
    """Diff window.

    This object represents and manages a single window containing the
    differences between two revisions on a branch.
    """

    def __init__(self):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.set_border_width(0)
        self.set_title("bzrk diff")

        # Use two thirds of the screen by default
        screen = self.get_screen()
        monitor = screen.get_monitor_geometry(0)
        width = int(monitor.width * 0.66)
        height = int(monitor.height * 0.66)
        self.set_default_size(width, height)

        self.construct()

    def construct(self):
        """Construct the window contents."""
        # The   window  consists  of   a  pane   containing:  the
        # hierarchical list  of files on  the left, and  the diff
        # for the currently selected file on the right.
        pane = gtk.HPaned()
        self.add(pane)
        pane.show()

        # The file hierarchy: a scrollable treeview
        scrollwin = gtk.ScrolledWindow()
        scrollwin.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scrollwin.set_shadow_type(gtk.SHADOW_IN)
        pane.pack1(scrollwin)
        scrollwin.show()

        self.model = gtk.TreeStore(str, str)
        self.treeview = gtk.TreeView(self.model)
        self.treeview.set_headers_visible(False)
        self.treeview.set_search_column(1)
        self.treeview.connect("cursor-changed", self._treeview_cursor_cb)
        scrollwin.add(self.treeview)
        self.treeview.show()

        cell = gtk.CellRendererText()
        cell.set_property("width-chars", 20)
        column = gtk.TreeViewColumn()
        column.pack_start(cell, expand=True)
        column.add_attribute(cell, "text", 0)
        self.treeview.append_column(column)

        # The diffs of the  selected file: a scrollable source or
        # text view
        scrollwin = gtk.ScrolledWindow()
        scrollwin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrollwin.set_shadow_type(gtk.SHADOW_IN)
        pane.pack2(scrollwin)
        scrollwin.show()

        if have_gtksourceview:
            self.buffer = gtksourceview.SourceBuffer()
            slm = gtksourceview.SourceLanguagesManager()
            gsl = slm.get_language_from_mime_type("text/x-patch")
            self.apply_colordiffrc(gsl)
            self.buffer.set_language(gsl)
            self.buffer.set_highlight(True)

            sourceview = gtksourceview.SourceView(self.buffer)
        else:
            self.buffer = gtk.TextBuffer()
            sourceview = gtk.TextView(self.buffer)

        sourceview.set_editable(False)
        sourceview.modify_font(pango.FontDescription("Monospace"))
        scrollwin.add(sourceview)
        sourceview.show()

    def set_diff(self, description, rev_tree, parent_tree):
        """Set the differences showed by this window.

        Compares the two trees and populates the window with the
        differences.
        """
        self.rev_tree = rev_tree
        self.parent_tree = parent_tree

        self.model.clear()
        delta = self.rev_tree.changes_from(self.parent_tree)

        self.model.append(None, [ "Complete Diff", "" ])

        if len(delta.added):
            titer = self.model.append(None, [ "Added", None ])
            for path, id, kind in delta.added:
                self.model.append(titer, [ path, path ])

        if len(delta.removed):
            titer = self.model.append(None, [ "Removed", None ])
            for path, id, kind in delta.removed:
                self.model.append(titer, [ path, path ])

        if len(delta.renamed):
            titer = self.model.append(None, [ "Renamed", None ])
            for oldpath, newpath, id, kind, text_modified, meta_modified \
                    in delta.renamed:
                self.model.append(titer, [ oldpath, newpath ])

        if len(delta.modified):
            titer = self.model.append(None, [ "Modified", None ])
            for path, id, kind, text_modified, meta_modified in delta.modified:
                self.model.append(titer, [ path, path ])

        self.treeview.expand_all()
        self.set_title(description + " - bzrk diff")

    def set_file(self, file_path):
        tv_path = None
        for data in self.model:
            for child in data.iterchildren():
                if child[0] == file_path or child[1] == file_path:
                    tv_path = child.path
                    break
        if tv_path is None:
            raise NoSuchFile(file_path)
        self.treeview.set_cursor(tv_path)
        self.treeview.scroll_to_cell(tv_path)

    def _treeview_cursor_cb(self, *args):
        """Callback for when the treeview cursor changes."""
        (path, col) = self.treeview.get_cursor()
        specific_files = [ self.model[path][1] ]
        if specific_files == [ None ]:
            return
        elif specific_files == [ "" ]:
            specific_files = []

        s = StringIO()
        show_diff_trees(self.parent_tree, self.rev_tree, s, specific_files)
        self.buffer.set_text(s.getvalue().decode(sys.getdefaultencoding(), 'replace'))

    @staticmethod
    def apply_colordiffrc(lang):
        """Set style colors in lang to that specified in colordiff config file.

        Both ~/.colordiffrc and ~/.colordiffrc.bzr-gtk are read.

        :param lang: a gtksourceview.SourceLanguage object.
        """
        def parse_colordiffrc(fileobj):
            """Parse fileobj as a colordiff configuration file.
            
            :return: A dict with the key -> value pairs.
            """
            colors = {}
            for line in fileobj:
                if re.match(r'^\s*#', line):
                    continue
                key, val = line.split('=')
                colors[key.strip()] = val.strip()
            return colors

        colors = {}

        for f in ('~/.colordiffrc', '~/.colordiffrc.bzr-gtk'):
            f = os.path.expanduser(f)
            if os.path.exists(f):
                try:
                    f = file(f)
                except IOError, e:
                    warning('could not open file %s: %s' % (f, str(e)))
                else:
                    colors.update(parse_colordiffrc(f))
                    f.close()

        if not colors:
            # ~/.colordiffrc does not exist
            return

        mapping = {
                # map GtkSourceView tags to colordiff names
                # since GSV is richer, accept new names for extra bits,
                # defaulting to old names if they're not present
                'Added@32@line': ['newtext'],
                'Removed@32@line': ['oldtext'],
                'Location': ['location', 'diffstuff'],
                'Diff@32@file': ['file', 'diffstuff'],
                'Special@32@case': ['specialcase', 'diffstuff'],
        }

        for tag in lang.get_tags():
            tag_id = tag.get_id()
            keys = mapping.get(tag_id, [])
            color = None

            for key in keys:
                color = colors.get(key, None)
                if color is not None:
                    break

            if color is None:
                continue

            style = gtksourceview.SourceTagStyle()
            try:
                style.foreground = gtk.gdk.color_parse(color)
            except ValueError:
                warning('not a valid color: %s' % color)
            else:
                lang.set_tag_style(tag_id, style)
