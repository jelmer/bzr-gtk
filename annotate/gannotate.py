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

from gi.repository import GObject
from gi.repository import Gdk
from gi.repository import Gtk
from gi.repository import Pango
import re

from bzrlib import patiencediff
from bzrlib.errors import NoSuchRevision
from bzrlib.revision import NULL_REVISION, CURRENT_REVISION

from bzrlib.plugins.gtk.annotate.colormap import AnnotateColorSaturation
from bzrlib.plugins.gtk.i18n import _i18n
from bzrlib.plugins.gtk.revisionview import RevisionView
from bzrlib.plugins.gtk.window import Window


(
    REVISION_ID_COL,
    LINE_NUM_COL,
    COMMITTER_COL,
    REVNO_COL,
    HIGHLIGHT_COLOR_COL,
    TEXT_LINE_COL
) = range(6)


class GAnnotateWindow(Window):
    """Annotate window."""

    def __init__(self, all=False, plain=False, parent=None, branch=None):
        self.all = all
        self.plain = plain
        self._branch = branch

        super(GAnnotateWindow, self).__init__(parent=parent)

        self.set_icon(
            self.render_icon_pixbuf(Gtk.STOCK_FIND, Gtk.IconSize.BUTTON))
        self.annotate_colormap = AnnotateColorSaturation()

        self._create()
        self.revisions = {}
        self.history = []
        self._no_back = set()

    def annotate(self, tree, branch, file_id):
        self.annotations = []
        self.branch = branch
        self.tree = tree
        self.file_id = file_id
        self.revisionview.set_file_id(file_id)
        self.revision_id = getattr(tree, 'get_revision_id', 
                                   lambda: CURRENT_REVISION)()

        # [revision id, line number, author, revno, highlight color, line]
        self.annomodel = Gtk.ListStore(GObject.TYPE_STRING,
                                       GObject.TYPE_INT,
                                       GObject.TYPE_STRING,
                                       GObject.TYPE_STRING,
                                       GObject.TYPE_STRING,
                                       GObject.TYPE_STRING)

        last_seen = None
        try:
            branch.lock_read()
            branch.repository.lock_read()
            self.dotted = {}
            revno_map = self.branch.get_revision_id_to_revno_map()
            for revision_id, revno in revno_map.iteritems():
                self.dotted[revision_id] = '.'.join(str(num) for num in revno)
            for line_no, (revision, revno, line)\
                in enumerate(self._annotate(tree, file_id)):
                if revision.revision_id == last_seen and not self.all:
                    revno = author = ""
                else:
                    last_seen = revision.revision_id
                    author = ", ".join(revision.get_apparent_authors())

                if revision.revision_id not in self.revisions:
                    self.revisions[revision.revision_id] = revision

                self.annomodel.append([revision.revision_id,
                                       line_no + 1,
                                       author,
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
        my_revno = self.dotted.get(self.revision_id, 'current')
        title = '%s (%s) - gannotate' % (self.tree.id2path(file_id), my_revno)
        self.set_title(title)

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

        tree_path = Gtk.TreePath(path=row)
        self.annoview.set_cursor(tree_path, None, False)
        self.annoview.scroll_to_cell(tree_path, use_align=True)

    def _annotate(self, tree, file_id):
        current_revision = FakeRevision(CURRENT_REVISION)
        current_revision.committer = self.branch.get_config().username()
        current_revision.timestamp = time.time()
        current_revision.message = '[Not yet committed]'
        current_revision.parent_ids = tree.get_parent_ids()
        current_revision.properties['branch-nick'] = self.branch._get_nick(local=True)
        current_revno = '%d?' % (self.branch.revno() + 1)
        repository = self.branch.repository
        if self.revision_id == CURRENT_REVISION:
            revision_id = self.branch.last_revision()
        else:
            revision_id = self.revision_id
        revision_cache = RevisionCache(repository, self.revisions)
        for origin, text in tree.annotate_iter(file_id):
            rev_id = origin
            if rev_id == CURRENT_REVISION:
                revision = current_revision
                revno = current_revno
            else:
                try:
                    revision = revision_cache.get_revision(rev_id)
                    revno = self.dotted.get(rev_id, 'merge')
                    if len(revno) > 15:
                        revno = 'merge'
                except NoSuchRevision:
                    revision = FakeRevision(rev_id)
                    revno = "?"

            yield revision, revno, text

    def _highlight_annotation(self, model, path, iter, now):
        revision_id, = model.get(iter, REVISION_ID_COL)
        revision = self.revisions[revision_id]
        # XXX sinzui 2011-08-12: What does get_color return?
        color = self.annotate_colormap.get_color(revision, now)
        model.set_value(iter, HIGHLIGHT_COLOR_COL, color)

    def _selected_revision(self):
        (path, col) = self.annoview.get_cursor()
        if path is None:
            return None
        return self.annomodel[path][REVISION_ID_COL]

    def _activate_selected_revision(self, w):
        rev_id = self._selected_revision()
        if not rev_id or rev_id == NULL_REVISION:
            return
        selected = self.revisions[rev_id]
        self.revisionview.set_revision(selected)
        if (len(selected.parent_ids) != 0 and selected.parent_ids[0] not in
            self._no_back):
            enable_back = True
        else:
            enable_back = False
        self.back_button.set_sensitive(enable_back)

    def _create(self):
        self.revisionview = self._create_log_view()
        self.annoview = self._create_annotate_view()

        vbox = Gtk.VBox(homogeneous=False, spacing=0)
        vbox.show()

        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.set_shadow_type(Gtk.ShadowType.IN)
        sw.add(self.annoview)
        self.annoview.gwindow = self
        sw.show()

        swbox = Gtk.VBox()
        swbox.pack_start(sw, True, True, 0)
        swbox.show()

        hbox = Gtk.HBox(homogeneous=False, spacing=6)
        self.back_button = self._create_back_button()
        hbox.pack_start(self.back_button, False, True, 0)
        self.forward_button = self._create_forward_button()
        hbox.pack_start(self.forward_button, False, True, 0)
        self.find_button = self._create_find_button()
        hbox.pack_start(self.find_button, False, True, 0)
        self.goto_button = self._create_goto_button()
        hbox.pack_start(self.goto_button, False, True, 0)
        hbox.show()
        vbox.pack_start(hbox, False, True, 0)

        self.pane = pane = Gtk.Paned.new(Gtk.Orientation.VERTICAL)
        pane.add1(swbox)
        pane.add2(self.revisionview)
        pane.show()
        vbox.pack_start(pane, True, True, 0)

        self._search = SearchBox()
        swbox.pack_start(self._search, False, True, 0)
        accels = Gtk.AccelGroup()
        accels.connect(Gdk.KEY_f, Gdk.ModifierType.CONTROL_MASK,
                             Gtk.AccelFlags.LOCKED,
                             self._search_by_text)
        accels.connect(Gdk.KEY_g, Gdk.ModifierType.CONTROL_MASK,
                             Gtk.AccelFlags.LOCKED,
                             self._search_by_line)
        self.add_accel_group(accels)

        self.add(vbox)

    def _search_by_text(self, *ignored): # (accel_group, window, key, modifiers):
        self._search.show_for('text')
        self._search.set_target(self.annoview, TEXT_LINE_COL)

    def _search_by_line(self, *ignored): # accel_group, window, key, modifiers):
        self._search.show_for('line')
        self._search.set_target(self.annoview, LINE_NUM_COL)

    def line_diff(self, tv, path, tvc):
        row = path.get_indices()[0]
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
        from bzrlib.plugins.gtk.diff import DiffWindow
        window = DiffWindow(self)
        window.set_diff("Diff for line %d" % (row+1), tree1, tree2)
        window.set_file(tree1.id2path(self.file_id))
        window.show()


    def _create_annotate_view(self):
        tv = Gtk.TreeView()
        tv.set_rules_hint(False)
        tv.connect("cursor-changed", self._activate_selected_revision)
        tv.show()
        tv.connect("row-activated", self.line_diff)

        cell = Gtk.CellRendererText()
        cell.set_property("xalign", 1.0)
        cell.set_property("ypad", 0)
        cell.set_property("family", "Monospace")
        cell.set_property(
            "cell-background-rgba",
            tv.get_style_context().get_background_color(Gtk.StateType.NORMAL))
        col = Gtk.TreeViewColumn()
        col.set_resizable(False)
        col.pack_start(cell, True)
        col.add_attribute(cell, "text", LINE_NUM_COL)
        tv.append_column(col)

        style_context = self.get_style_context()

        cell = Gtk.CellRendererText()
        cell.set_property("ypad", 0)
        cell.set_property("ellipsize", Pango.EllipsizeMode.END)
        cell.set_property(
            "cell-background-rgba",
            style_context.get_background_color(Gtk.StateType.NORMAL))
        col = Gtk.TreeViewColumn("Committer")
        col.set_resizable(True)
        col.pack_start(cell, True)
        col.add_attribute(cell, "text", COMMITTER_COL)
        tv.append_column(col)

        cell = Gtk.CellRendererText()
        cell.set_property("xalign", 1.0)
        cell.set_property("ypad", 0)
        cell.set_property(
            "cell-background-rgba",
            style_context.get_background_color(Gtk.StateType.NORMAL))
        col = Gtk.TreeViewColumn("Revno")
        col.set_resizable(False)
        col.pack_start(cell, True)
        col.add_attribute(cell, "markup", REVNO_COL)
        tv.append_column(col)

        cell = Gtk.CellRendererText()
        cell.set_property("ypad", 0)
        cell.set_property("family", "Monospace")
        col = Gtk.TreeViewColumn()
        col.set_resizable(False)
        col.pack_start(cell, True)
#        col.add_attribute(cell, "foreground", HIGHLIGHT_COLOR_COL)
        col.add_attribute(cell, "background", HIGHLIGHT_COLOR_COL)
        col.add_attribute(cell, "text", TEXT_LINE_COL)
        tv.append_column(col)

        # interactive substring search
        def search_equal_func(model, column, key, iter):
            return model.get_value(iter, TEXT_LINE_COL).lower().find(key.lower()) == -1

        tv.set_enable_search(True)
        tv.set_search_equal_func(search_equal_func, None)

        return tv

    def _create_log_view(self):
        lv = RevisionView(self._branch)
        lv.show()
        return lv

    def _create_back_button(self):
        button = Gtk.Button()
        button.set_use_stock(True)
        button.set_label("gtk-go-back")
        button.connect("clicked", lambda w: self.go_back())
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.show()
        return button

    def _create_forward_button(self):
        button = Gtk.Button()
        button.set_use_stock(True)
        button.set_label("gtk-go-forward")
        button.connect("clicked", lambda w: self.go_forward())
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.show()
        button.set_sensitive(False)
        return button

    def _create_find_button(self):
        button = Gtk.Button()
        button.set_use_stock(True)
        button.set_label("gtk-find")
        button.set_tooltip_text("Search for text (Ctrl+F)")
        button.connect("clicked", self._search_by_text)
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.show()
        button.set_sensitive(True)
        return button

    def _create_goto_button(self):
        button = Gtk.Button()
        button.set_label("Goto Line")
        button.set_tooltip_text("Scroll to a line by entering its number (Ctrl+G)")
        button.connect("clicked", self._search_by_line)
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.show()
        button.set_sensitive(True)
        return button

    def go_back(self):
        last_tree = self.tree
        rev_id = self._selected_revision()
        parent_id = self.revisions[rev_id].parent_ids[0]
        target_tree = self.branch.repository.revision_tree(parent_id)
        if self._go(target_tree):
            self.history.append(last_tree)
            self.forward_button.set_sensitive(True)
        else:
            self._no_back.add(parent_id)
            self.back_button.set_sensitive(False)

    def go_forward(self):
        if len(self.history) == 0:
            return
        target_tree = self.history.pop()
        if len(self.history) == 0:
            self.forward_button.set_sensitive(False)
        self._go(target_tree)

    def _go(self, target_tree):
        rev_id = self._selected_revision()
        if self.file_id in target_tree:
            offset = self.get_scroll_offset(target_tree)
            path, col = self.annoview.get_cursor()
            (row,) = path.get_indices()
            self.annotate(target_tree, self.branch, self.file_id)
            new_row = row+offset
            if new_row < 0:
                new_row = 0
            new_path = Gtk.TreePath(path=new_row)
            self.annoview.set_cursor(new_path, None, False)
            return True
        else:
            return False

    def get_scroll_offset(self, tree):
        old = self.tree.get_file(self.file_id)
        new = tree.get_file(self.file_id)
        path, col = self.annoview.get_cursor()
        (row,) = path.get_indices()
        matcher = patiencediff.PatienceSequenceMatcher(None, old.readlines(),
                                                       new.readlines())
        for i, j, n in matcher.get_matching_blocks():
            if i + n >= row:
                return j - i


class FakeRevision(object):
    """ A fake revision.

    For when a revision is referenced but not present.
    """

    def __init__(self, revision_id, committer='?', nick=None):
        self.revision_id = revision_id
        self.parent_ids = []
        self.committer = committer
        self.message = "?"
        self.timestamp = 0.0
        self.timezone = 0
        self.properties = {}

    def get_apparent_authors(self):
        return [self.committer]


class RevisionCache(object):
    """A caching revision source"""

    def __init__(self, real_source, seed_cache=None):
        self.__real_source = real_source
        if seed_cache is None:
            self.__cache = {}
        else:
            self.__cache = dict(seed_cache)

    def get_revision(self, revision_id):
        if revision_id not in self.__cache:
            revision = self.__real_source.get_revision(revision_id)
            self.__cache[revision_id] = revision
        return self.__cache[revision_id]


class SearchBox(Gtk.HBox):
    """A button box for searching in text or lines of annotations"""
    def __init__(self):
        super(SearchBox, self).__init__(homogeneous=False, spacing=6)

        # Close button
        button = Gtk.Button()
        image = Gtk.Image()
        image.set_from_stock('gtk-stop', Gtk.IconSize.BUTTON)
        button.set_image(image)
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.connect("clicked", lambda w: self.hide())
        self.pack_start(button, False, False, 0)

        # Search entry
        label = Gtk.Label()
        self._label = label
        self.pack_start(label, False, False, 0)

        entry = Gtk.Entry()
        self._entry = entry
        entry.connect("activate", lambda w, d: self._do_search(d),
                      'forward')
        self.pack_start(entry, False, False, 0)

        # Next/previous buttons
        button = Gtk.Button(_i18n('_Next'), use_underline=True)
        image = Gtk.Image()
        image.set_from_stock('gtk-go-forward', Gtk.IconSize.BUTTON)
        button.set_image(image)
        button.connect("clicked", lambda w, d: self._do_search(d),
                       'forward')
        self.pack_start(button, False, False, 0)

        button = Gtk.Button(_i18n('_Previous'), use_underline=True)
        image = Gtk.Image()
        image.set_from_stock('gtk-go-back', Gtk.IconSize.BUTTON)
        button.set_image(image)
        button.connect("clicked", lambda w, d: self._do_search(d),
                       'backward')
        self.pack_start(button, False, False, 0)

        # Search options
        check = Gtk.CheckButton('Match case')
        self._match_case = check
        self.pack_start(check, False, False, 0)

        check = Gtk.CheckButton('Regexp')
        check.connect("toggled", lambda w: self._set_label())
        self._regexp = check
        self.pack_start(check, False, False, 0)

        self._view = None
        self._column = None
        # Note that we stay hidden (we do not call self.show_all())


    def show_for(self, kind):
        self._kind = kind
        self.show_all()
        self._set_label()
        # Hide unrelated buttons
        if kind == 'line':
            self._match_case.hide()
            self._regexp.hide()
        # Be ready
        self._entry.grab_focus()

    def _set_label(self):
        if self._kind == 'line':
            self._label.set_text('Find Line: ')
        else:
            if self._regexp.get_active():
                self._label.set_text('Find Regexp: ')
            else:
                self._label.set_text('Find Text: ')

    def set_target(self, view,column):
        self._view = view
        self._column = column

    def _match(self, model, iterator, column):
        matching_case = self._match_case.get_active()
        cell_value, = model.get(iterator, column)
        key = self._entry.get_text()
        if column == LINE_NUM_COL:
            # FIXME: For goto-line there are faster algorithms than searching 
            # every line til we find the right one! -- mbp 2011-01-27
            return key.strip() == str(cell_value)
        elif self._regexp.get_active():
            if matching_case:
                match = re.compile(key).search(cell_value, 1)
            else:
                match = re.compile(key, re.I).search(cell_value, 1)
        else:
            if not matching_case:
                cell_value = cell_value.lower()
                key = key.lower()
            match = cell_value.find(key) != -1

        return match

    def _iterate_rows_forward(self, model, start):
        model_size = len(model)
        current = start + 1
        while model_size != 0:
            if current >= model_size: current =  0
            yield model.get_iter_from_string('%d' % current)
            if current == start: raise StopIteration
            current += 1

    def _iterate_rows_backward(self, model, start):
        model_size = len(model)
        current = start - 1
        while model_size != 0:
            if current < 0: current = model_size - 1
            yield model.get_iter_from_string('%d' % current)
            if current == start: raise StopIteration
            current -= 1

    def _do_search(self, direction):
        if direction == 'forward':
            iterate = self._iterate_rows_forward
        else:
            iterate = self._iterate_rows_backward

        model, sel = self._view.get_selection().get_selected()
        if sel is None:
            start = 0
        else:
            path = model.get_string_from_iter(sel)
            start = int(path)

        for row in iterate(model, start):
            if self._match(model, row, self._column):
                path = model.get_path(row)
                self._view.set_cursor(path, None, False)
                self._view.scroll_to_cell(path, use_align=True)
                break
