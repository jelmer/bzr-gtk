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
try:
    import gconf
    have_gconf = True
except ImportError:
    have_gconf = False

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
            if have_gconf:
                self.apply_gedit_colors(gsl)
            self.apply_colordiff_colors(gsl)
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
    def apply_gedit_colors(lang):
        """Set style for lang to that specified in gedit configuration.

        This method needs the gconf module.
        
        :param lang: a gtksourceview.SourceLanguage object.
        """
        GEDIT_SYNTAX_PATH = '/apps/gedit-2/preferences/syntax_highlighting'
        GEDIT_LANG_PATH = GEDIT_SYNTAX_PATH + '/' + lang.get_id()

        client = gconf.client_get_default()
        client.add_dir(GEDIT_LANG_PATH, gconf.CLIENT_PRELOAD_NONE)

        for tag in lang.get_tags():
            tag_id = tag.get_id()
            gconf_key = GEDIT_LANG_PATH + '/' + tag_id
            style_string = client.get_string(gconf_key)

            if style_string is None:
                continue

            # function to get a bool from a string that's either '0' or '1'
            string_bool = lambda x: bool(int(x))

            # style_string is a string like "2/#FFCCAA/#000000/0/1/0/0"
            # values are: mask, fg, bg, italic, bold, underline, strike
            # this packs them into (str_value, attr_name, conv_func) tuples
            items = zip(style_string.split('/'), ['mask', 'foreground',
                'background', 'italic', 'bold', 'underline', 'strikethrough' ],
                [ int, gtk.gdk.color_parse, gtk.gdk.color_parse, string_bool,
                    string_bool, string_bool, string_bool ]
            )

            style = gtksourceview.SourceTagStyle()

            # XXX The mask attribute controls whether the present values of
            # foreground and background color should in fact be used. Ideally
            # (and that's what gedit does), one could set all three attributes,
            # and let the TagStyle object figure out which colors to use.
            # However, in the GtkSourceview python bindings, the mask attribute
            # is read-only, and it's derived instead from the colors being
            # set or not. This means that we have to sometimes refrain from
            # setting fg or bg colors, depending on the value of the mask.
            # This code could go away if mask were writable.
            mask = int(items[0][0])
            if not (mask & 1): # GTK_SOURCE_TAG_STYLE_USE_BACKGROUND
                items[2:3] = []
            if not (mask & 2): # GTK_SOURCE_TAG_STYLE_USE_FOREGROUND
                items[1:2] = []
            items[0:1] = [] # skip the mask unconditionally

            for value, attr, func in items:
                try:
                    value = func(value)
                except ValueError:
                    warning('gconf key %s contains an invalid value: %s'
                            % gconf_key, value)
                else:
                    setattr(style, attr, value)

            lang.set_tag_style(tag_id, style)

    @staticmethod
    def apply_colordiff_colors(lang):
        """Set style colors for lang using the colordiff configuration file.

        Both ~/.colordiffrc and ~/.colordiffrc.bzr-gtk are read.

        :param lang: a "Diff" gtksourceview.SourceLanguage object.
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
