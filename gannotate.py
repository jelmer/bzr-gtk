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

from bzrlib.errors import NoSuchRevision

from colormap import AnnotateColorMap
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
        
        self.set_default_size(640, 480)
        self.set_icon(self.render_icon(gtk.STOCK_FIND, gtk.ICON_SIZE_BUTTON))
        self.annotate_colormap = AnnotateColorMap()

        self._create()

    def annotate(self, branch, file_id):
        self.revisions = {}
        
        # [revision id, line number, committer, revno, highlight color, line]
        self.model = gtk.ListStore(gobject.TYPE_STRING,
                                   gobject.TYPE_STRING,
                                   gobject.TYPE_STRING,
                                   gobject.TYPE_STRING,
                                   gobject.TYPE_STRING,
                                   gobject.TYPE_STRING)
        
        last_seen = None
        for line_no, (revision, revno, line)\
                in enumerate(self._annotate(branch, file_id)):
            if revision.revision_id == last_seen and not self.all:
                revno = committer = ""
            else:
                last_seen = revision.revision_id
                committer = revision.committer

            if revision.revision_id not in self.revisions:
                self.revisions[revision.revision_id] = revision

            self.model.append([revision.revision_id,
                               line_no + 1,
                               committer,
                               revno,
                               None,
                               line.rstrip("\r\n")
                              ])

        if not self.plain:
            self._set_oldest_newest()
            # Recall that calling activate_default will emit "span-changed",
            # so self._span_changed_cb will take care of initial highlighting
            self.span_selector.activate_default()

        self.treeview.set_model(self.model)
        self.treeview.set_cursor(0)
        self.treeview.grab_focus()

    def _annotate(self, branch, file_id):
        rev_hist = branch.revision_history()
        rev_tree = branch.revision_tree(branch.last_revision())
        rev_id = rev_tree.inventory[file_id].revision
        weave = branch.weave_store.get_weave(file_id,
                                             branch.get_transaction())
        
        for origin, text in weave.annotate_iter(rev_id):
            rev_id = weave.idx_to_name(origin)
            try:
                revision = branch.get_revision(rev_id)
                if rev_id in rev_hist:
                    revno = branch.revision_id_to_revno(rev_id)
                else:
                    revno = "merge"
            except NoSuchRevision:
                revision = NoneRevision(rev_id)
                revno = "?"

            yield revision, revno, text

    def _set_oldest_newest(self):
        rev_dates = map(lambda i: self.revisions[i].timestamp, self.revisions)
        oldest = min(rev_dates)
        newest = max(rev_dates)

        span = self._span_from_seconds(time.time() - oldest)
        self.span_selector.set_to_oldest_span(span)
        
        span = self._span_from_seconds(newest - oldest)
        self.span_selector.set_newest_to_oldest_span(span)

    def _span_from_seconds(self, seconds):
        return (seconds / (24 * 60 * 60))
    
    def _span_changed_cb(self, w, span):
        self.annotate_colormap.set_span(span)
        now = time.time()
        self.model.foreach(self._highlight_annotation, now)

    def _highlight_annotation(self, model, path, iter, now):
        revision_id, = model.get(iter, REVISION_ID_COL)
        revision = self.revisions[revision_id]
        days = self._span_from_seconds(now - revision.timestamp)
        model.set(iter, HIGHLIGHT_COLOR_COL,
                  self.annotate_colormap.get_color(days))

    def _show_log(self, w):
        (path, col) = self.treeview.get_cursor()
        rev_id = self.model[path][REVISION_ID_COL]
        self.logview.set_revision(self.revisions[rev_id])

    def _create(self):
        vbox = gtk.VBox(False, 12)
        vbox.set_border_width(12)
        vbox.show()
        
        pane = gtk.VPaned()
        pane.pack1(self._create_annotate_view(), resize=True, shrink=False)
        pane.pack2(self._create_log_view(), resize=False, shrink=True)
        pane.show()
        vbox.pack_start(pane, expand=True, fill=True)
        
        hbox = gtk.HBox(True, 6)

        if not self.plain:
            hbox.pack_start(self._create_span_selector(),
                            expand=False, fill=True)

        hbox.pack_start(self._create_button_box(), expand=False, fill=True)
        hbox.show()
        vbox.pack_start(hbox, expand=False, fill=True)

        (width, height) = self.get_size()
        pane.set_position(int(height / 1.5))

        self.add(vbox)

    def _create_annotate_view(self):
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_IN)
        sw.show()

        self.treeview = gtk.TreeView()
        self.treeview.set_rules_hint(False)
        self.treeview.connect("cursor-changed", self._show_log)
        sw.add(self.treeview)
        self.treeview.show()

        cell = gtk.CellRendererText()
        cell.set_property("xalign", 1.0)
        cell.set_property("ypad", 0)
        cell.set_property("family", "Monospace")
        cell.set_property("cell-background-gdk",
                          self.treeview.get_style().bg[gtk.STATE_NORMAL])
        col = gtk.TreeViewColumn()
        col.set_resizable(False)
        col.pack_start(cell, expand=True)
        col.add_attribute(cell, "text", LINE_NUM_COL)
        self.treeview.append_column(col)

        cell = gtk.CellRendererText()
        cell.set_property("ypad", 0)
        cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        cell.set_property("cell-background-gdk",
                          self.get_style().bg[gtk.STATE_NORMAL])
        col = gtk.TreeViewColumn("Committer")
        col.set_resizable(True)
        col.pack_start(cell, expand=True)
        col.add_attribute(cell, "text", COMMITTER_COL)
        self.treeview.append_column(col)

        cell = gtk.CellRendererText()
        cell.set_property("xalign", 1.0)
        cell.set_property("ypad", 0)
        cell.set_property("cell-background-gdk",
                          self.get_style().bg[gtk.STATE_NORMAL])
        col = gtk.TreeViewColumn("Revno")
        col.set_resizable(False)
        col.pack_start(cell, expand=True)
        col.add_attribute(cell, "markup", REVNO_COL)
        self.treeview.append_column(col)

        cell = gtk.CellRendererText()
        cell.set_property("ypad", 0)
        cell.set_property("family", "Monospace")
        col = gtk.TreeViewColumn()
        col.set_resizable(False)
        col.pack_start(cell, expand=True)
        col.add_attribute(cell, "foreground", HIGHLIGHT_COLOR_COL)
        col.add_attribute(cell, "text", TEXT_LINE_COL)
        self.treeview.append_column(col)

        self.treeview.set_search_column(LINE_NUM_COL)
        
        return sw

    def _create_span_selector(self):
        self.span_selector = SpanSelector()
        self.span_selector.connect("span-changed", self._span_changed_cb)
        self.span_selector.show()

        return self.span_selector

    def _create_log_view(self):
        self.logview = LogView()
        self.logview.show()
        return self.logview

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


class NoneRevision:
    """ A fake revision.

    For when a revision is referenced but not present.
    """

    def __init__(self, revision_id):
        self.revision_id = revision_id
        self.parent_ids = []
        self.committer = "?"
        self.message = "?"
        self.timestamp = 0.0
        self.timezone = 0

