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

from bzrlib.branch import Branch
from bzrlib.errors import NoSuchRevision

from colormap import ColorMap, GrannyColorMap
from logview import LogView


(
    REVISION_ID_COL,
    LINE_NUM_COL,
    COMMITTER_COL,
    REVNO_COL,
    HIGHLIGHT_COLOR_COL,
    TEXT_LINE_COL
) = range(6)

(
    SPAN_DAYS_COL,
    SPAN_STR_COL,
    SPAN_IS_SEPARATOR_COL,
    SPAN_IS_CUSTOM_COL
) = range(4)


class GAnnotateWindow(gtk.Window):
    """Annotate window."""

    def __init__(self):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.set_default_size(640, 480)
        self.set_icon(self.render_icon(gtk.STOCK_FIND, gtk.ICON_SIZE_BUTTON))
        self.color_map = GrannyColorMap()
        self.num_custom_spans = 0

        self._create()

    def annotate(self, branch, file_id, all=False):
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
            if revision.revision_id == last_seen and not all:
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

        self._set_default_span()
        self.treeview.set_model(self.model)
        self.treeview.set_cursor(0)
        self.treeview.grab_focus()

    def _annotate(self, branch, file_id):
        rev_hist = branch.revision_history()
        rev_tree = branch.revision_tree(branch.last_revision())
        rev_id = rev_tree.inventory[file_id].revision
        weave = branch.weave_store.get_weave(file_id, branch.get_transaction())
        
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

    def _set_default_span(self):
        rev_dates = map(lambda i: self.revisions[i].timestamp, self.revisions)
        oldest = min(rev_dates)
        newest = max(rev_dates)

        span = ((newest - oldest) / (24 * 60 * 60))
        self.span_model.set_value(self.newest_iter, SPAN_DAYS_COL, span)
        
        span = ((time.time() - oldest) / (24 * 60 * 60))
        self.span_model.set_value(self.oldest_iter, SPAN_DAYS_COL, span)
        
        index = int(self.span_model.get_string_from_iter(self.oldest_iter))
        self.span_combo.set_active(index)
        self.set_span(span)
    
    def _set_span_cb(self, w):
        model = w.get_model()
        iter = w.get_active_iter()

        if model.get_value(iter, SPAN_IS_CUSTOM_COL):
            self._request_custom_span()
        else:
            span = model.get_value(iter, SPAN_DAYS_COL)
            self.set_span(span)

    def _request_custom_span(self):
        self.span_combo.hide()
        self.span_entry.show_all()

    def _set_custom_span_cb(self, w):
        days = float(w.get_text())
        self.span_entry.hide_all()
        self.span_combo.show()

        if self.num_custom_spans == 0:
            self.custom_iter = self.span_model.insert_after(self.custom_iter,
                                                            self.separator)
            self.citer_top = self.custom_iter.copy()

        if self.num_custom_spans == 4:
            self.num_custom_spans -= 1
            self.span_model.remove(self.span_model.iter_next(self.citer_top))
            
        self.num_custom_spans += 1
        self.custom_iter = self.span_model.insert_after(
            self.custom_iter, [days, "%.2f Days" % days, False, False])
        
        index = int(self.span_model.get_string_from_iter(self.custom_iter))
        self.span_combo.set_active(index)
        self.set_span(days)
        
    def set_span(self, span):
        self.color_map.set_span(span)
        now = time.time()
        self.model.foreach(self._highlight_annotation, now)

    def _highlight_annotation(self, model, path, iter, now):
        revision_id, = model.get(iter, REVISION_ID_COL)
        revision = self.revisions[revision_id]
        days = ((now - revision.timestamp) / (24 * 60 * 60))
        model.set(iter, HIGHLIGHT_COLOR_COL, self.color_map.get_color(days))

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
        hbox.pack_start(self._create_toolbar(), expand=False, fill=True)
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

    def _create_toolbar(self):
        toolbar = gtk.HBox(False, 6)
        toolbar.show()

        label = gtk.Label("Highlighting spans:")
        label.show()
        toolbar.pack_start(label, expand=False, fill=True)

        # [span in days, span as string, row is seperator?, row is select
        # default?]
        self.span_model = gtk.ListStore(gobject.TYPE_FLOAT,
                                        gobject.TYPE_STRING,
                                        gobject.TYPE_BOOLEAN,
                                        gobject.TYPE_BOOLEAN)

        self.separator = [0., "", True, False]
        
        self.oldest_iter =\
                self.span_model.append([0., "to Oldest Revision", False, False])
        self.newest_iter =\
                self.span_model.append([0., "Newest to Oldest",
                                        False, False])
        self.span_model.append(self.separator)
        self.span_model.append([1., "1 Day", False, False])
        self.span_model.append([7., "1 Week", False, False])
        self.span_model.append([30., "1 Month", False, False])
        self.custom_iter =\
                self.span_model.append([365., "1 Year", False, False])
        self.span_model.append(self.separator)
        self.span_model.append([0., "Custom...", False, True])
        
        self.span_combo = gtk.ComboBox(self.span_model)
        self.span_combo.set_row_separator_func(
            lambda m, i: m.get_value(i, SPAN_IS_SEPARATOR_COL))
        cell = gtk.CellRendererText()
        self.span_combo.pack_start(cell, False)
        self.span_combo.add_attribute(cell, "text", 1)
        self.span_combo.connect("changed", self._set_span_cb)
        self.span_combo.show()
        toolbar.pack_start(self.span_combo, expand=False, fill=False)

        self.span_entry = gtk.HBox(False, 6)
        spin = gtk.SpinButton(digits=2)
        spin.set_numeric(True)
        spin.set_increments(1.0, 10.0)
        spin.set_range(0.0, 100 * 365)
        spin.connect('activate', self._set_custom_span_cb)
        spin.connect('show', lambda w: w.grab_focus())
        self.span_entry.pack_start(spin, expand=False, fill=False)
        self.span_entry.pack_start(gtk.Label("Days"),
                                   expand=False, fill=False)

        toolbar.pack_start(self.span_entry, expand=False, fill=False)

        return toolbar

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

