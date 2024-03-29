# -*- coding: UTF-8 -*-
"""Revision history view.

"""

__copyright__ = "Copyright © 2005 Canonical Ltd."
__author__    = "Daniel Schierbeck <daniel.schierbeck@gmail.com>"

from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import Pango

from bzrlib import ui
from bzrlib.revision import NULL_REVISION

from bzrlib.plugins.gtk import lock
from bzrlib.plugins.gtk.ui import ProgressPanel
from bzrlib.plugins.gtk.branchview import treemodel
from bzrlib.plugins.gtk.branchview.linegraph import linegraph, same_branch
from bzrlib.plugins.gtk.branchview.graphcell import CellRendererGraph


class TreeView(Gtk.VBox):

    __gproperties__ = {
        'branch': (GObject.TYPE_PYOBJECT,
                   'Branch',
                   'The Bazaar branch being visualized',
                   GObject.PARAM_CONSTRUCT_ONLY | GObject.PARAM_WRITABLE),

        'revision': (GObject.TYPE_PYOBJECT,
                     'Revision',
                     'The currently selected revision',
                     GObject.PARAM_READWRITE),

        'revision-number': (GObject.TYPE_STRING,
                            'Revision number',
                            'The number of the selected revision',
                            '',
                            GObject.PARAM_READABLE),

        'children': (GObject.TYPE_PYOBJECT,
                     'Child revisions',
                     'Children of the currently selected revision',
                     GObject.PARAM_READABLE),

        'parents': (GObject.TYPE_PYOBJECT,
                    'Parent revisions',
                    'Parents to the currently selected revision',
                    GObject.PARAM_READABLE),

        'revno-column-visible': (GObject.TYPE_BOOLEAN,
                                 'Revision number column',
                                 'Show revision number column',
                                 True,
                                 GObject.PARAM_READWRITE),

        'graph-column-visible': (GObject.TYPE_BOOLEAN,
                                 'Graph column',
                                 'Show graph column',
                                 True,
                                 GObject.PARAM_READWRITE),

        'date-column-visible': (GObject.TYPE_BOOLEAN,
                                 'Date',
                                 'Show date column',
                                 False,
                                 GObject.PARAM_READWRITE),

        'compact': (GObject.TYPE_BOOLEAN,
                    'Compact view',
                    'Break ancestry lines to save space',
                    True,
                    GObject.PARAM_CONSTRUCT | GObject.PARAM_READWRITE),

        'mainline-only': (GObject.TYPE_BOOLEAN,
                    'Mainline only',
                    'Only show the mainline history.',
                    False,
                    GObject.PARAM_CONSTRUCT | GObject.PARAM_READWRITE),

    }

    __gsignals__ = {
        'revision-selected': (GObject.SignalFlags.RUN_FIRST,
                              None,
                              ()),
        'revision-activated': (GObject.SignalFlags.RUN_FIRST,
                              None,
                              (GObject.TYPE_PYOBJECT, GObject.TYPE_PYOBJECT)),
        'tag-added': (GObject.SignalFlags.RUN_FIRST,
                              None,
                              (GObject.TYPE_STRING, GObject.TYPE_STRING)),
        'refreshed': (GObject.SignalFlags.RUN_FIRST, None,
                              ())
    }

    def __init__(self, branch, start, maxnum, compact=True):
        """Create a new TreeView.

        :param branch: Branch object for branch to show.
        :param start: Revision id of top revision.
        :param maxnum: Maximum number of revisions to display, 
                       None for no limit.
        :param broken_line_length: After how much lines to break 
                                   branches.
        """
        super(TreeView, self).__init__(homogeneous=False, spacing=0)

        self.progress_widget = ProgressPanel()
        self.pack_start(self.progress_widget, False, True, 0)
        if getattr(ui.ui_factory, "set_progress_bar_widget", None) is not None:
            # We'are using our own ui, let's tell it to use our widget.
            ui.ui_factory.set_progress_bar_widget(self.progress_widget)

        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC,
                                        Gtk.PolicyType.AUTOMATIC)
        self.scrolled_window.set_shadow_type(Gtk.ShadowType.IN)
        self.scrolled_window.show()
        self.pack_start(self.scrolled_window, True, True, 0)

        self.scrolled_window.add(self.construct_treeview())

        self.path = None
        self.branch = branch
        self.revision = None
        self.index = {}

        self.start = start
        self.maxnum = maxnum
        self.compact = compact

        self.model = treemodel.BranchTreeModel(self.branch, [])
        GObject.idle_add(self.populate)

        self.connect("destroy", self._on_destroy)

    def _on_destroy(self, *ignored):
        self.branch.unlock()
        if getattr(ui.ui_factory, "set_progress_bar_widget", None) is not None:
            # We'are using our own ui, let's tell it to stop using our widget.
            ui.ui_factory.set_progress_bar_widget(None)

    def do_get_property(self, property):
        if property.name == 'revno-column-visible':
            return self.revno_column.get_visible()
        elif property.name == 'graph-column-visible':
            return self.graph_column.get_visible()
        elif property.name == 'date-column-visible':
            return self.date_column.get_visible()
        elif property.name == 'compact':
            return self.compact
        elif property.name == 'mainline-only':
            return self.mainline_only
        elif property.name == 'branch':
            return self.branch
        elif property.name == 'revision':
            if self.path is None:
                return None
            return self.model.get_value(self.model.get_iter(self.path),
                                        treemodel.REVISION)
        elif property.name == 'revision-number':
            if self.path is None:
                return None
            return self.model.get_value(self.model.get_iter(self.path),
                                        treemodel.REVNO)
        elif property.name == 'children':
            if self.path is None:
                return None
            return self.model.get_value(self.model.get_iter(self.path),
                                        treemodel.CHILDREN)
        elif property.name == 'parents':
            if self.path is None:
                return None
            return self.model.get_value(self.model.get_iter(self.path),
                                        treemodel.PARENTS)
        else:
            raise AttributeError, 'unknown property %s' % property.name

    def do_set_property(self, property, value):
        if property.name == 'revno-column-visible':
            self.revno_column.set_visible(value)
        elif property.name == 'graph-column-visible':
            self.graph_column.set_visible(value)
        elif property.name == 'date-column-visible':
            self.date_column.set_visible(value)
        elif property.name == 'compact':
            self.compact = value
        elif property.name == 'mainline-only':
            self.mainline_only = value
        elif property.name == 'branch':
            self.branch = value
        elif property.name == 'revision':
            self.set_revision_id(value.revision_id)
        else:
            raise AttributeError, 'unknown property %s' % property.name

    def get_revision(self):
        """Return revision id of currently selected revision, or None."""
        return self.get_property('revision')

    def has_revision_id(self, revision_id):
        return (revision_id in self.index)

    def set_revision(self, revision):
        self.set_property('revision', revision)

    def set_revision_id(self, revid):
        """Change the currently selected revision.

        :param revid: Revision id of revision to display.
        """
        self.treeview.set_cursor(
            Gtk.TreePath(path=self.index[revid]), None, False)
        self.treeview.grab_focus()

    def get_children(self):
        """Return the children of the currently selected revision.

        :return: list of revision ids.
        """
        return self.get_property('children')

    def get_parents(self):
        """Return the parents of the currently selected revision.

        :return: list of revision ids.
        """
        return self.get_property('parents')

    def add_tag(self, tag, revid=None):
        if revid is None: revid = self.revision.revision_id

        if lock.release(self.branch):
            try:
                lock.acquire(self.branch, lock.WRITE)
                self.model.add_tag(tag, revid)
            finally:
                lock.release(self.branch)

            lock.acquire(self.branch, lock.READ)

            self.emit('tag-added', tag, revid)

    def refresh(self):
        GObject.idle_add(self.populate, self.get_revision())

    def update(self):
        try:
            self.branch.unlock()
            try:
                self.branch.lock_write()
                self.branch.update()
            finally:
                self.branch.unlock()
        finally:
            self.branch.lock_read()

    def back(self):
        """Signal handler for the Back button."""
        parents = self.get_parents()
        if not parents:
            return

        for parent_id in parents:
            parent_index = self.index[parent_id]
            parent = self.model[parent_index][treemodel.REVISION]
            if same_branch(self.get_revision(), parent):
                self.set_revision(parent)
                break
        else:
            self.set_revision_id(parents[0])

    def forward(self):
        """Signal handler for the Forward button."""
        children = self.get_children()
        if not children:
            return

        for child_id in children:
            child_index = self.index[child_id]
            child = self.model[child_index][treemodel.REVISION]
            if same_branch(child, self.get_revision()):
                self.set_revision(child)
                break
        else:
            self.set_revision_id(children[0])

    def populate(self, revision=None):
        """Fill the treeview with contents.

        :param start: Revision id of revision to start with.
        :param maxnum: Maximum number of revisions to display, or None 
                       for no limit.
        :param broken_line_length: After how much lines branches \
                       should be broken.
        """

        if getattr(ui.ui_factory, "set_progress_bar_widget", None) is not None:
            # We'are using our own ui, let's tell it to use our widget.
            ui.ui_factory.set_progress_bar_widget(self.progress_widget)
        self.progress_bar = ui.ui_factory.nested_progress_bar()
        self.progress_bar.update("Loading ancestry graph", 0, 5)

        try:
            if self.compact:
                broken_line_length = 32
            else:
                broken_line_length = None

            show_graph = self.graph_column.get_visible()

            self.branch.lock_read()
            (linegraphdata, index, columns_len) = linegraph(
                self.branch.repository.get_graph(),
                self.start,
                self.maxnum, 
                broken_line_length,
                show_graph,
                self.mainline_only,
                self.progress_bar)

            self.model.set_line_graph_data(linegraphdata)
            self.graph_cell.columns_len = columns_len
            width = self.graph_cell.get_preferred_width(self.treeview)[1]
            if width > 500:
                width = 500
            elif width == 0:
                # The get_preferred_width() call got an insane value.
                width = 200
            self.graph_column.set_fixed_width(width)
            self.graph_column.set_max_width(width)
            self.index = index
            self.treeview.set_model(self.model)

            if not revision or revision == NULL_REVISION:
                self.treeview.set_cursor(Gtk.TreePath(path=0), None, False)
            else:
                self.set_revision(revision)

            self.emit('refreshed')
            return False
        finally:
            self.progress_bar.finished()

    def construct_treeview(self):
        self.treeview = Gtk.TreeView()

        self.treeview.set_rules_hint(True)
        # combined revno/summary interactive search
        #
        # the row in a treemodel is considered "matched" if a REVNO *starts*
        # from the key (that is the key is found in a REVNO at the offset 0)
        # or if a MESSAGE *contains* the key anywhere (that is, the key is
        # found case insensitively in a MESSAGE at any offset)
        def search_equal_func(model, column, key, iter, ignored):
            return (model.get_value(iter, treemodel.REVNO).find(key) != 0
                and model.get_value(iter, treemodel.MESSAGE).lower().find(key.lower()) == -1)

        self.treeview.set_search_equal_func(search_equal_func, None)
        self.treeview.set_enable_search(True)

        self.treeview.set_tooltip_column(treemodel.MESSAGE)
        self.treeview.set_headers_visible(True)

        self._prev_cursor_path = None
        self.treeview.connect("cursor-changed",
                self._on_selection_changed)

        self.treeview.connect("row-activated", 
                self._on_revision_activated)

        self.treeview.connect("button-release-event", 
                self._on_revision_selected)

        self.treeview.set_property('fixed-height-mode', True)

        self.treeview.show()

        cell = Gtk.CellRendererText()
        cell.set_property("width-chars", 15)
        cell.set_property("ellipsize", Pango.EllipsizeMode.END)
        self.revno_column = Gtk.TreeViewColumn("Revision No")
        self.revno_column.set_resizable(True)
        self.revno_column.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        self.revno_column.set_fixed_width(
            cell.get_preferred_width(self.treeview)[1])
        self.revno_column.pack_start(cell, True)
        self.revno_column.add_attribute(cell, "text", treemodel.REVNO)
        self.treeview.append_column(self.revno_column)

        self.graph_cell = CellRendererGraph()
        self.graph_column = Gtk.TreeViewColumn()
        self.graph_column.set_resizable(True)
        self.graph_column.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        self.graph_column.pack_start(self.graph_cell, True)
        self.graph_column.add_attribute(
            self.graph_cell, "node", treemodel.NODE)
        self.graph_column.add_attribute(
            self.graph_cell, "tags", treemodel.TAGS)
        self.graph_column.add_attribute(
            self.graph_cell, "in-lines", treemodel.LAST_LINES)
        self.graph_column.add_attribute(
            self.graph_cell, "out-lines", treemodel.LINES)
        self.treeview.append_column(self.graph_column)

        cell = Gtk.CellRendererText()
        cell.set_property("width-chars", 65)
        cell.set_property("ellipsize", Pango.EllipsizeMode.END)
        self.summary_column = Gtk.TreeViewColumn("Summary")
        self.summary_column.set_resizable(True)
        self.summary_column.set_expand(True)
        self.summary_column.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        self.summary_column.set_fixed_width(
            cell.get_preferred_width(self.treeview)[1])
        self.summary_column.pack_start(cell, True)
        self.summary_column.add_attribute(cell, "markup", treemodel.SUMMARY)
        self.treeview.append_column(self.summary_column)

        cell = Gtk.CellRendererText()
        cell.set_property("width-chars", 15)
        cell.set_property("ellipsize", Pango.EllipsizeMode.END)
        self.authors_column = Gtk.TreeViewColumn("Author(s)")
        self.authors_column.set_resizable(False)
        self.authors_column.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        self.authors_column.set_fixed_width(200)
        self.authors_column.pack_start(cell, True)
        self.authors_column.add_attribute(cell, "text", treemodel.AUTHORS)
        self.treeview.append_column(self.authors_column)

        cell = Gtk.CellRendererText()
        cell.set_property("width-chars", 20)
        cell.set_property("ellipsize", Pango.EllipsizeMode.END)
        self.date_column = Gtk.TreeViewColumn("Date")
        self.date_column.set_visible(False)
        self.date_column.set_resizable(True)
        self.date_column.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        self.date_column.set_fixed_width(130)
        self.date_column.pack_start(cell, True)
        self.date_column.add_attribute(cell, "text", treemodel.TIMESTAMP)
        self.treeview.append_column(self.date_column)

        return self.treeview

    def _on_selection_changed(self, treeview):
        """callback for when the treeview changes."""
        (path, focus) = treeview.get_cursor()
        if (path is not None) and (path != self._prev_cursor_path):
            self._prev_cursor_path = path # avoid emitting twice per click
            self.path = path
            self.emit('revision-selected')

    def _on_revision_selected(self, widget, event):
        from bzrlib.plugins.gtk.revisionmenu import RevisionMenu
        if event.button == 3:
            revs = []
            rev = self.get_revision()
            if rev is not None:
                revs.append(rev.revision_id)
            menu = RevisionMenu(self.branch.repository, revs, self.branch)
            menu.connect('tag-added', lambda w, t, r: self.add_tag(t, r))
            menu.popup(None, None, None, None, event.button, event.get_time())

    def _on_revision_activated(self, widget, path, col):
        self.emit('revision-activated', path, col)
