# Modified for use with Olive:
# Copyright (C) 2006 by Szilveszter Farkas (Phanatic) <szilveszter.farkas@gmail.com>
# Original copyright holder:
# Copyright (C) 2005 by Canonical Ltd. (Scott James Remnant <scott@ubuntu.com>)
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

"""Difference window.

This module contains the code to manage the diff window which shows
the changes made between two revisions on a branch.
"""

__copyright__ = "Copyright © 2005 Canonical Ltd."
__author__    = "Scott James Remnant <scott@ubuntu.com>"


from cStringIO import StringIO

import gtk
import pango

try:
    import gtksourceview
    have_gtksourceview = True
except ImportError:
    have_gtksourceview = False

import bzrlib
if (bzrlib.version_info[0] == 0) and (bzrlib.version_info[1] < 9):
    # function deprecated after 0.9
    from bzrlib.delta import compare_trees

from bzrlib.diff import show_diff_trees
from bzrlib.errors import NoSuchFile


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
        hbox = gtk.HBox(spacing=6)
        hbox.set_border_width(0)
        self.add(hbox)
        hbox.show()

        scrollwin = gtk.ScrolledWindow()
        scrollwin.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scrollwin.set_shadow_type(gtk.SHADOW_IN)
        hbox.pack_start(scrollwin, expand=False, fill=True)
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


        scrollwin = gtk.ScrolledWindow()
        scrollwin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrollwin.set_shadow_type(gtk.SHADOW_IN)
        hbox.pack_start(scrollwin, expand=True, fill=True)
        scrollwin.show()

        if have_gtksourceview:
            self.buffer = gtksourceview.SourceBuffer()
            slm = gtksourceview.SourceLanguagesManager()
            gsl = slm.get_language_from_mime_type("text/x-patch")
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

        if (bzrlib.version_info[0] == 0) and (bzrlib.version_info[1] < 9):
            delta = compare_trees(self.parent_tree, self.rev_tree)
        else:
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
        self.buffer.set_text(s.getvalue())
