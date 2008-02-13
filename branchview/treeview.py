# -*- coding: UTF-8 -*-
"""Revision history view.

"""

__copyright__ = "Copyright © 2005 Canonical Ltd."
__author__    = "Daniel Schierbeck <daniel.schierbeck@gmail.com>"

import sys
import string
import gtk
import gobject
import pango
import re
import treemodel

from linegraph import linegraph, same_branch
from graphcell import CellRendererGraph
from treemodel import TreeModel
from bzrlib.revision import NULL_REVISION

class TreeView(gtk.VBox):

    __gproperties__ = {
        'branch': (gobject.TYPE_PYOBJECT,
                   'Branch',
                   'The Bazaar branch being visualized',
                   gobject.PARAM_CONSTRUCT_ONLY | gobject.PARAM_WRITABLE),

        'revision': (gobject.TYPE_PYOBJECT,
                     'Revision',
                     'The currently selected revision',
                     gobject.PARAM_READWRITE),

        'revision-number': (gobject.TYPE_STRING,
                            'Revision number',
                            'The number of the selected revision',
                            '',
                            gobject.PARAM_READABLE),

        'children': (gobject.TYPE_PYOBJECT,
                     'Child revisions',
                     'Children of the currently selected revision',
                     gobject.PARAM_READABLE),

        'parents': (gobject.TYPE_PYOBJECT,
                    'Parent revisions',
                    'Parents to the currently selected revision',
                    gobject.PARAM_READABLE),

        'revno-column-visible': (gobject.TYPE_BOOLEAN,
                                 'Revision number',
                                 'Show revision number column',
                                 True,
                                 gobject.PARAM_READWRITE),

        'date-column-visible': (gobject.TYPE_BOOLEAN,
                                 'Date',
                                 'Show date column',
                                 False,
                                 gobject.PARAM_READWRITE),

        'compact': (gobject.TYPE_BOOLEAN,
                    'Compact view',
                    'Break ancestry lines to save space',
                    True,
                    gobject.PARAM_CONSTRUCT | gobject.PARAM_READWRITE)

    }

    __gsignals__ = {
        'revisions-loaded': (gobject.SIGNAL_RUN_FIRST, 
                             gobject.TYPE_NONE,
                             ()),
        'revision-selected': (gobject.SIGNAL_RUN_FIRST,
                              gobject.TYPE_NONE,
                              ()),
        'tag-added': (gobject.SIGNAL_RUN_FIRST,
                              gobject.TYPE_NONE,
                              (gobject.TYPE_STRING, gobject.TYPE_STRING))
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
        gtk.VBox.__init__(self, spacing=0)

        self.pack_start(self.construct_loading_msg(), expand=False, fill=True)
        self.connect('revisions-loaded', 
                lambda x: self.loading_msg_box.hide())

        self.scrolled_window = gtk.ScrolledWindow()
        self.scrolled_window.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.scrolled_window.set_shadow_type(gtk.SHADOW_IN)
        self.scrolled_window.show()
        self.pack_start(self.scrolled_window, expand=True, fill=True)

        self.scrolled_window.add(self.construct_treeview())
        

        self.iter = None
        self.branch = branch
        self.revision = None

        self.start = start
        self.maxnum = maxnum
        self.compact = compact

        gobject.idle_add(self.populate)

        self.connect("destroy", lambda x: self.branch.unlock())

    def do_get_property(self, property):
        if property.name == 'revno-column-visible':
            return self.revno_column.get_visible()
        elif property.name == 'date-column-visible':
            return self.date_column.get_visible()
        elif property.name == 'compact':
            return self.compact
        elif property.name == 'branch':
            return self.branch
        elif property.name == 'revision':
            return self.model.get_value(self.iter, treemodel.REVISION)
        elif property.name == 'revision-number':
            return self.model.get_value(self.iter, treemodel.REVNO)
        elif property.name == 'children':
            return self.model.get_value(self.iter, treemodel.CHILDREN)
        elif property.name == 'parents':
            return self.model.get_value(self.iter, treemodel.PARENTS)
        else:
            raise AttributeError, 'unknown property %s' % property.name

    def do_set_property(self, property, value):
        if property.name == 'revno-column-visible':
            self.revno_column.set_visible(value)
        elif property.name == 'date-column-visible':
            self.date_column.set_visible(value)
        elif property.name == 'compact':
            self.compact = value
        elif property.name == 'branch':
            self.branch = value
        elif property.name == 'revision':
            self.set_revision_id(value.revision_id)
        else:
            raise AttributeError, 'unknown property %s' % property.name

    def get_revision(self):
        """Return revision id of currently selected revision, or None."""
        return self.get_property('revision')

    def set_revision(self, revision):
        self.set_property('revision', revision)

    def set_revision_id(self, revid):
        """Change the currently selected revision.

        :param revid: Revision id of revision to display.
        """
        self.treeview.set_cursor(self.index[revid])
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

        try:
            self.branch.unlock()

            try:
                self.branch.lock_write()
                self.model.add_tag(tag, revid)
            finally:
                self.branch.unlock()

        finally:
            self.branch.lock_read()

        self.emit('tag-added', tag, revid)
        
    def refresh(self):
        self.loading_msg_box.show()
        gobject.idle_add(self.populate, self.get_revision())

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
        if not len(parents):
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
        if not len(children):
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

        if self.compact:
            broken_line_length = 32
        else:
            broken_line_length = None

        self.branch.lock_read()
        (linegraphdata, index, columns_len) = linegraph(self.branch.repository,
                                                        self.start,
                                                        self.maxnum, 
                                                        broken_line_length)

        self.model = TreeModel(self.branch, linegraphdata)
        self.graph_cell.columns_len = columns_len
        width = self.graph_cell.get_size(self.treeview)[2]
        if width > 500:
            width = 500
        self.graph_column.set_fixed_width(width)
        self.graph_column.set_max_width(width)
        self.index = index
        self.treeview.set_model(self.model)

        if revision is None:
            self.treeview.set_cursor(0)
        else:
            self.set_revision(revision)

        self.emit('revisions-loaded')

        return False

    def show_diff(self, revid=None, parentid=None):
        """Open a new window to show a diff between the given revisions."""
        from bzrlib.plugins.gtk.diff import DiffWindow
        window = DiffWindow(parent=self)

        parents = self.get_parents()

        if revid is None:
            revid = self.get_revision().revision_id

            if parentid is None and len(parents) > 0:
                parentid = parents[0]

        if parentid is None:
            parentid = NULL_REVISION

        rev_tree    = self.branch.repository.revision_tree(revid)
        parent_tree = self.branch.repository.revision_tree(parentid)

        description = revid + " - " + self.branch.nick
        window.set_diff(description, rev_tree, parent_tree)
        window.show()

    def construct_treeview(self):
        self.treeview = gtk.TreeView()

        self.treeview.set_rules_hint(True)
        self.treeview.set_search_column(treemodel.REVNO)
        
        # Fix old PyGTK bug - by JAM
        set_tooltip = getattr(self.treeview, 'set_tooltip_column', None)
        if set_tooltip is not None:
            set_tooltip(treemodel.MESSAGE)

        self.treeview.connect("cursor-changed",
                self._on_selection_changed)

        self.treeview.connect("row-activated", 
                self._on_revision_activated)

        self.treeview.connect("button-release-event", 
                self._on_revision_selected)

        self.treeview.set_property('fixed-height-mode', True)

        self.treeview.show()

        cell = gtk.CellRendererText()
        cell.set_property("width-chars", 15)
        cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        self.revno_column = gtk.TreeViewColumn("Revision No")
        self.revno_column.set_resizable(True)
        self.revno_column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.revno_column.set_fixed_width(cell.get_size(self.treeview)[2])
        self.revno_column.pack_start(cell, expand=True)
        self.revno_column.add_attribute(cell, "text", treemodel.REVNO)
        self.treeview.append_column(self.revno_column)

        self.graph_cell = CellRendererGraph()
        self.graph_column = gtk.TreeViewColumn()
        self.graph_column.set_resizable(True)
        self.graph_column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.graph_column.pack_start(self.graph_cell, expand=False)
        self.graph_column.add_attribute(self.graph_cell, "node", treemodel.NODE)
        self.graph_column.add_attribute(self.graph_cell, "tags", treemodel.TAGS)
        self.graph_column.add_attribute(self.graph_cell, "in-lines", treemodel.LAST_LINES)
        self.graph_column.add_attribute(self.graph_cell, "out-lines", treemodel.LINES)
        self.treeview.append_column(self.graph_column)

        cell = gtk.CellRendererText()
        cell.set_property("width-chars", 65)
        cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        self.summary_column = gtk.TreeViewColumn("Summary")
        self.summary_column.set_resizable(True)
        self.summary_column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.summary_column.set_fixed_width(cell.get_size(self.treeview)[2])
        self.summary_column.pack_start(cell, expand=True)
        self.summary_column.add_attribute(cell, "markup", treemodel.SUMMARY)
        self.treeview.append_column(self.summary_column)

        cell = gtk.CellRendererText()
        cell.set_property("width-chars", 15)
        cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        self.committer_column = gtk.TreeViewColumn("Committer")
        self.committer_column.set_resizable(True)
        self.committer_column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.committer_column.set_fixed_width(cell.get_size(self.treeview)[2])
        self.committer_column.pack_start(cell, expand=True)
        self.committer_column.add_attribute(cell, "text", treemodel.COMMITTER)
        self.treeview.append_column(self.committer_column)

        cell = gtk.CellRendererText()
        cell.set_property("width-chars", 20)
        cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        self.date_column = gtk.TreeViewColumn("Date")
        self.date_column.set_visible(False)
        self.date_column.set_resizable(True)
        self.date_column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.date_column.set_fixed_width(cell.get_size(self.treeview)[2])
        self.date_column.pack_start(cell, expand=True)
        self.date_column.add_attribute(cell, "text", treemodel.TIMESTAMP)
        self.treeview.append_column(self.date_column)
        
        return self.treeview
    
    def construct_loading_msg(self):
        image_loading = gtk.image_new_from_stock(gtk.STOCK_REFRESH,
                                                 gtk.ICON_SIZE_BUTTON)
        image_loading.show()
        
        label_loading = gtk.Label(_("Please wait, loading ancestral graph..."))
        label_loading.set_alignment(0.0, 0.5)
        label_loading.show()
        
        self.loading_msg_box = gtk.HBox()
        self.loading_msg_box.set_spacing(5)
        self.loading_msg_box.set_border_width(5)        
        self.loading_msg_box.pack_start(image_loading, False, False)
        self.loading_msg_box.pack_start(label_loading, True, True)
        self.loading_msg_box.show()
        
        return self.loading_msg_box

    def _on_selection_changed(self, treeview):
        """callback for when the treeview changes."""
        (path, focus) = treeview.get_cursor()
        if path is not None:
            self.iter = self.model.get_iter(path)
            self.emit('revision-selected')

    def _on_revision_selected(self, widget, event):
        from bzrlib.plugins.gtk.revisionmenu import RevisionPopupMenu
        if event.button == 3:
            menu = RevisionPopupMenu(self.branch.repository, 
                [self.get_revision().revision_id],
                self.branch)
            menu.connect('tag-added', lambda w, t, r: self.add_tag(t, r))
            menu.popup(None, None, None, event.button, event.get_time())

    def _on_revision_activated(self, widget, path, col):
        # TODO: more than one parent
        """Callback for when a treeview row gets activated."""
        revision_id = self.model[path][treemodel.REVID]
        parents = self.model[path][treemodel.PARENTS]

        if len(parents) == 0:
            parent_id = None
        else:
            parent_id = parents[0]

        self.show_diff(revision_id, parent_id)
        self.treeview.grab_focus()
