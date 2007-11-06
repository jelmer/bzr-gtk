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

class TreeView(gtk.ScrolledWindow):

    __gproperties__ = {
        'branch': (gobject.TYPE_PYOBJECT,
                   'Branch',
                   'The Bazaar branch being visualized',
                   gobject.PARAM_CONSTRUCT_ONLY | gobject.PARAM_WRITABLE),

        'revision': (gobject.TYPE_PYOBJECT,
                     'Revision',
                     'The currently selected revision',
                     gobject.PARAM_READWRITE),

        'revno-column-visible': (gobject.TYPE_BOOLEAN,
                                 'Revision number',
                                 'Show revision number column',
                                 True,
                                 gobject.PARAM_READWRITE),

        'date-column-visible': (gobject.TYPE_BOOLEAN,
                                 'Date',
                                 'Show date column',
                                 False,
                                 gobject.PARAM_READWRITE)

    }

    __gsignals__ = {
        'revisions-loaded': (gobject.SIGNAL_RUN_FIRST, 
                             gobject.TYPE_NONE,
                             ()),
        'revision-selected': (gobject.SIGNAL_RUN_FIRST,
                              gobject.TYPE_NONE,
                              ())
    }

    def __init__(self, branch, start, maxnum, broken_line_length=None):
        """Create a new TreeView.

        :param branch: Branch object for branch to show.
        :param start: Revision id of top revision.
        :param maxnum: Maximum number of revisions to display, 
                       None for no limit.
        :param broken_line_length: After how much lines to break 
                                   branches.
        """
        gtk.ScrolledWindow.__init__(self)

        self.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.set_shadow_type(gtk.SHADOW_IN)

        self.construct_treeview()

        self.branch = branch

        gobject.idle_add(self.populate, start, maxnum, 
                         broken_line_length)

        self.revision = None
        self.children = None
        self.parents  = None

    def do_get_property(self, property):
        if property.name == 'revno-column-visible':
            return self.revno_column.get_visible()
        elif property.name == 'date-column-visible':
            return self.date_column.get_visible()
        elif property.name == 'branch':
            return self.branch
        elif property.name == 'revision':
            return self.revision
        else:
            raise AttributeError, 'unknown property %s' % property.name

    def do_set_property(self, property, value):
        if property.name == 'revno-column-visible':
            self.revno_column.set_visible(value)
        elif property.name == 'date-column-visible':
            self.date_column.set_visible(value)
        elif property.name == 'branch':
            self.branch = value
        elif property.name == 'revision':
            self.set_revision_id(value.revision_id)
        else:
            raise AttributeError, 'unknown property %s' % property.name

    def get_revision(self):
        """Return revision id of currently selected revision, or None."""
        return self.revision

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
        return self.children

    def get_parents(self):
        """Return the parents of the currently selected revision.

        :return: list of revision ids.
        """
        return self.parents
        
    def back(self):
        """Signal handler for the Back button."""
        (path, col) = self.treeview.get_cursor()
        revision = self.model[path][treemodel.REVISION]
        parents = self.model[path][treemodel.PARENTS]
        if not len(parents):
            return

        for parent_id in parents:
            parent_index = self.index[parent_id]
            parent = self.model[parent_index][treemodel.REVISION]
            if same_branch(revision, parent):
                self.treeview.set_cursor(parent_index)
                break
        else:
            self.treeview.set_cursor(self.index[parents[0]])
        self.treeview.grab_focus()

    def forward(self):
        """Signal handler for the Forward button."""
        (path, col) = self.treeview.get_cursor()
        revision = self.model[path][treemodel.REVISION]
        children = self.model[path][treemodel.CHILDREN]
        if not len(children):
            return

        for child_id in children:
            child_index = self.index[child_id]
            child = self.model[child_index][treemodel.REVISION]
            if same_branch(child, revision):
                self.treeview.set_cursor(child_index)
                break
        else:
            self.treeview.set_cursor(self.index[children[0]])
        self.treeview.grab_focus()

    def populate(self, start, maxnum, broken_line_length=None):
        """Fill the treeview with contents.

        :param start: Revision id of revision to start with.
        :param maxnum: Maximum number of revisions to display, or None 
                       for no limit.
        :param broken_line_length: After how much lines branches \
                       should be broken.
        """
        try:
            self.branch.lock_read()
            (linegraphdata, index, columns_len) = linegraph(self.branch.repository,
                                                            start,
                                                            maxnum, 
                                                            broken_line_length)

            self.model = TreeModel(self.branch.repository, linegraphdata)
            self.graph_cell.columns_len = columns_len
            width = self.graph_cell.get_size(self.treeview)[2]
            self.graph_column.set_fixed_width(width)
            self.graph_column.set_max_width(width)
            self.index = index
            self.treeview.set_model(self.model)
            self.treeview.set_cursor(0)
            self.emit('revisions-loaded')

        finally:
            self.branch.unlock()

        return False

    def show_diff(self, revid=None, parentid=None):
        """Open a new window to show a diff between the given revisions."""
        from bzrlib.plugins.gtk.diff import DiffWindow
        window = DiffWindow(parent=self)

        if revid is None:
            revid = self.revision.revision_id

            if parentid is None and len(self.parents) > 0:
                parentid = self.parents[0]

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
        self.treeview.set_tooltip_column(treemodel.MESSAGE)

        self.treeview.get_selection().connect("changed",
                self._on_selection_changed)

        self.treeview.connect("row-activated", 
                self._on_revision_activated)

        self.treeview.connect("button-release-event", 
                self._on_revision_selected)

        self.treeview.set_property('fixed-height-mode', True)

        self.add(self.treeview)
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
        self.graph_column.add_attribute(self.graph_cell, "in-lines", treemodel.LAST_LINES)
        self.graph_column.add_attribute(self.graph_cell, "out-lines", treemodel.LINES)
        self.treeview.append_column(self.graph_column)

        cell = gtk.CellRendererText()
        cell.set_property("width-chars", 65)
        cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        self.msg_column = gtk.TreeViewColumn("Message")
        self.msg_column.set_resizable(True)
        self.msg_column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.msg_column.set_fixed_width(cell.get_size(self.treeview)[2])
        self.msg_column.pack_start(cell, expand=True)
        self.msg_column.add_attribute(cell, "text", treemodel.MESSAGE)
        self.treeview.append_column(self.msg_column)

        cell = gtk.CellRendererText()
        cell.set_property("width-chars", 15)
        cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        self.committer_column = gtk.TreeViewColumn("Committer")
        self.committer_column.set_resizable(True)
        self.committer_column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.committer_column.set_fixed_width(cell.get_size(self.treeview)[2])
        self.committer_column.pack_start(cell, expand=True)
        self.committer_column.add_attribute(cell, "text", treemodel.COMMITER)
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

    def _on_selection_changed(self, selection, *args):
        """callback for when the treeview changes."""
        (model, selected_rows) = selection.get_selected_rows()
        if len(selected_rows) > 0:
            iter = self.model.get_iter(selected_rows[0])
            self.revision = self.model.get_value(iter, treemodel.REVISION)
            self.parents = self.model.get_value(iter, treemodel.PARENTS)
            self.children = self.model.get_value(iter, treemodel.CHILDREN)

            self.emit('revision-selected')

    def _on_revision_selected(self, widget, event):
        from bzrlib.plugins.gtk.revisionmenu import RevisionPopupMenu
        if event.button == 3:
            menu = RevisionPopupMenu(self.branch.repository, 
                [self.get_revision().revision_id],
                self.branch)
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
