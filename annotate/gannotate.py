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

import time

import pygtk
pygtk.require("2.0")
import gobject
import gtk
import pango

from bzrlib import tsort
from bzrlib.errors import NoSuchRevision
from bzrlib.revision import NULL_REVISION, CURRENT_REVISION

from colormap import AnnotateColorMap, AnnotateColorSaturation
from logview import LogView
from spanselector import SpanSelector


(
    REVISION_ID_COL,
    LINE_NUM_COL,
    COMMITTER_COL,
    REVNO_COL,
    HIGHLIGHT_COLOR_COL,
    TEXT_LINE_COL
) = range(6)


class GAnnotateWindow(gtk.Window):
    """Annotate window."""

    def __init__(self, all=False, plain=False):
        self.all = all
        self.plain = plain
        
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        
        self.set_icon(self.render_icon(gtk.STOCK_FIND, gtk.ICON_SIZE_BUTTON))
        self.annotate_colormap = AnnotateColorSaturation()

        self._create()

    def annotate(self, tree, branch, file_id):
        self.revisions = {}
        self.annotations = []
        self.branch = branch
        self.tree = tree
        self.file_id = file_id
        self.revision_id = getattr(tree, 'get_revision_id', 
                                   lambda: CURRENT_REVISION)()
        
        # [revision id, line number, committer, revno, highlight color, line]
        self.annomodel = gtk.ListStore(gobject.TYPE_STRING,
                                       gobject.TYPE_STRING,
                                       gobject.TYPE_STRING,
                                       gobject.TYPE_STRING,
                                       gobject.TYPE_STRING,
                                       gobject.TYPE_STRING)
        
        last_seen = None
        try:
            branch.lock_read()
            branch.repository.lock_read()
            for line_no, (revision, revno, line)\
                    in enumerate(self._annotate(tree, file_id)):
                if revision.revision_id == last_seen and not self.all:
                    revno = committer = ""
                else:
                    last_seen = revision.revision_id
                    committer = revision.committer

                if revision.revision_id not in self.revisions:
                    self.revisions[revision.revision_id] = revision

                self.annomodel.append([revision.revision_id,
                                       line_no + 1,
                                       committer,
                                       revno,
                                       None,
                                       line.rstrip("\r\n")
                                      ])
                self.annotations.append(revision)

            if not self.plain:
                now = time.time()
                self.annomodel.foreach(self._highlight_annotation, now)
        finally:
            branch.repository.unlock()
            branch.unlock()

        self.annoview.set_model(self.annomodel)
        self.annoview.grab_focus()

    def jump_to_line(self, lineno):
        if lineno > len(self.annomodel) or lineno < 1:
            row = 0
            # FIXME:should really deal with this in the gui. Perhaps a status
            # bar?
            print("gannotate: Line number %d does't exist. Defaulting to "
                  "line 1." % lineno)
	    return
        else:
            row = lineno - 1

        self.annoview.set_cursor(row)
        self.annoview.scroll_to_cell(row, use_align=True)

    def _dotted_revnos(self, repository, revision_id):
        """Return a dict of revision_id -> dotted revno
        
        :param repository: The repository to get the graph from
        :param revision_id: The last revision for which this info is needed
        """
        graph = repository.get_revision_graph(revision_id)
        dotted = {}
        for n, revision_id, d, revno, e in tsort.merge_sort(graph, 
            revision_id, generate_revno=True):
            dotted[revision_id] = '.'.join(str(num) for num in revno)
        return dotted

    def _annotate(self, tree, file_id):
        current_revision = FakeRevision(CURRENT_REVISION)
        current_revision.committer = self.branch.get_config().username()
        current_revision.timestamp = time.time()
        current_revision.message = '[Not yet committed]'
        current_revno = '%d?' % (self.branch.revno() + 1)
        repository = self.branch.repository
        if self.revision_id == CURRENT_REVISION:
            revision_id = self.branch.last_revision()
        else:
            revision_id = self.revision_id
        dotted = self._dotted_revnos(repository, revision_id)
        revision_cache = RevisionCache(repository)
        for origin, text in tree.annotate_iter(file_id):
            rev_id = origin
            try:
                revision = revision_cache.get_revision(rev_id)
                revno = dotted.get(rev_id, 'merge')
                if len(revno) > 15:
                    revno = 'merge'
            except NoSuchRevision:
                committer = "?"
                if rev_id == CURRENT_REVISION:
                    revision = current_revision
                    revno = current_revno
                else:
                    revision = FakeRevision(rev_id)
                    revno = "?"

            yield revision, revno, text

    def _highlight_annotation(self, model, path, iter, now):
        revision_id, = model.get(iter, REVISION_ID_COL)
        revision = self.revisions[revision_id]
        model.set(iter, HIGHLIGHT_COLOR_COL,
                  self.annotate_colormap.get_color(revision, now))

    def _selected_revision(self):
        (path, col) = self.annoview.get_cursor()
        if path is None:
            return None
        return self.annomodel[path][REVISION_ID_COL]

    def _show_log(self, w):
        rev_id = self._selected_revision()
        if rev_id is None:
            return
        self.logview.set_revision(self.revisions[rev_id])

    def _create(self):
        self.logview = self._create_log_view()
        self.annoview = self._create_annotate_view()

        vbox = gtk.VBox(False, 12)
        vbox.set_border_width(12)
        vbox.show()

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_IN)
        sw.add(self.annoview)
        self.annoview.gwindow = self
        sw.show()
        
        self.pane = pane = gtk.VPaned()
        pane.add1(sw)
        pane.add2(self.logview)
        pane.show()
        vbox.pack_start(pane, expand=True, fill=True)
        
        hbox = gtk.HBox(True, 6)
        hbox.pack_start(self._create_prev_button(), expand=False, fill=True)
        hbox.pack_end(self._create_button_box(), expand=False, fill=True)
        hbox.show()
        vbox.pack_start(hbox, expand=False, fill=True)

        self.add(vbox)

    def row_diff(self, tv, path, tvc):
        row = path[0]
        revision = self.annotations[row]
        repository = self.branch.repository
        if revision.revision_id == CURRENT_REVISION:
            tree1 = self.tree
            tree2 = self.tree.basis_tree()
        else:
            tree1 = repository.revision_tree(revision.revision_id)
            if len(revision.parent_ids) > 0:
                tree2 = repository.revision_tree(revision.parent_ids[0])
            else:
                tree2 = repository.revision_tree(NULL_REVISION)
        from bzrlib.plugins.gtk.viz.diffwin import DiffWindow
        window = DiffWindow()
        window.set_diff("Diff for row %d" % (row+1), tree1, tree2)
        window.set_file(tree1.id2path(self.file_id))
        window.show()


    def _create_annotate_view(self):
        tv = gtk.TreeView()
        tv.set_rules_hint(False)
        tv.connect("cursor-changed", self._show_log)
        tv.show()
        tv.connect("row-activated", self.row_diff)

        cell = gtk.CellRendererText()
        cell.set_property("xalign", 1.0)
        cell.set_property("ypad", 0)
        cell.set_property("family", "Monospace")
        cell.set_property("cell-background-gdk",
                          tv.get_style().bg[gtk.STATE_NORMAL])
        col = gtk.TreeViewColumn()
        col.set_resizable(False)
        col.pack_start(cell, expand=True)
        col.add_attribute(cell, "text", LINE_NUM_COL)
        tv.append_column(col)

        cell = gtk.CellRendererText()
        cell.set_property("ypad", 0)
        cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        cell.set_property("cell-background-gdk",
                          self.get_style().bg[gtk.STATE_NORMAL])
        col = gtk.TreeViewColumn("Committer")
        col.set_resizable(True)
        col.pack_start(cell, expand=True)
        col.add_attribute(cell, "text", COMMITTER_COL)
        tv.append_column(col)

        cell = gtk.CellRendererText()
        cell.set_property("xalign", 1.0)
        cell.set_property("ypad", 0)
        cell.set_property("cell-background-gdk",
                          self.get_style().bg[gtk.STATE_NORMAL])
        col = gtk.TreeViewColumn("Revno")
        col.set_resizable(False)
        col.pack_start(cell, expand=True)
        col.add_attribute(cell, "markup", REVNO_COL)
        tv.append_column(col)

        cell = gtk.CellRendererText()
        cell.set_property("ypad", 0)
        cell.set_property("family", "Monospace")
        col = gtk.TreeViewColumn()
        col.set_resizable(False)
        col.pack_start(cell, expand=True)
#        col.add_attribute(cell, "foreground", HIGHLIGHT_COLOR_COL)
        col.add_attribute(cell, "background", HIGHLIGHT_COLOR_COL)
        col.add_attribute(cell, "text", TEXT_LINE_COL)
        tv.append_column(col)

        tv.set_search_column(LINE_NUM_COL)
        
        return tv

    def _create_log_view(self):
        lv = LogView()
        lv.show()

        return lv

    def _create_button_box(self):
        box = gtk.HButtonBox()
        box.set_layout(gtk.BUTTONBOX_END)
        box.show()
        
        button = gtk.Button()
        button.set_use_stock(True)
        button.set_label("gtk-close")
        button.connect("clicked", lambda w: self.destroy())
        button.show()
        
        box.pack_start(button, expand=False, fill=False)

        return box

    def _create_prev_button(self):
        box = gtk.HButtonBox()
        box.set_layout(gtk.BUTTONBOX_START)
        box.show()
        
        button = gtk.Button()
        button.set_use_stock(True)
        button.set_label("gtk-go-back")
        button.connect("clicked", lambda w: self.go_back())
        button.show()
        box.pack_start(button, expand=False, fill=False)
        return box

    def go_back(self):
        rev_id = self._selected_revision()
        parent_id = self.revisions[rev_id].parent_ids[0]
        tree = self.branch.repository.revision_tree(parent_id)
        if self.file_id in tree:
            self.annotate(tree, self.branch, self.file_id)


class FakeRevision:
    """ A fake revision.

    For when a revision is referenced but not present.
    """

    def __init__(self, revision_id, committer='?'):
        self.revision_id = revision_id
        self.parent_ids = []
        self.committer = committer
        self.message = "?"
        self.timestamp = 0.0
        self.timezone = 0


class RevisionCache(object):
    """A caching revision source"""
    def __init__(self, real_source):
        self.__real_source = real_source
        self.__cache = {}

    def get_revision(self, revision_id):
        if revision_id not in self.__cache:
            revision = self.__real_source.get_revision(revision_id)
            self.__cache[revision_id] = revision
        return self.__cache[revision_id]
