# -*- coding: UTF-8 -*-
"""Revision history view.

"""

__copyright__ = "Copyright © 2005 Canonical Ltd."
__author__    = "Daniel Schierbeck <daniel.schierbeck@gmail.com>"

import gtk
import gobject
import pango
import re
import treemodel

from linegraph import linegraph, same_branch
from graphcell import CellRendererGraph
from treemodel import TreeModel

class TreeView(gtk.ScrolledWindow):

    def __init__(self):
        gtk.ScrolledWindow.__init__(self)

        self.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.set_shadow_type(gtk.SHADOW_IN)

        self.construct_treeview()

        self.revision = None
        self.children = None
        self.parents  = None

    def get_revision(self):
        return self.revision

    def get_children(self):
        return self.children

    def get_parents(self):
        return self.parents

    def construct_treeview(self):
        self.treeview = gtk.TreeView()

        self.treeview.set_rules_hint(True)
        self.treeview.set_search_column(4)

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
        column = gtk.TreeViewColumn("Revision No")
        column.set_resizable(True)
        column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        column.set_fixed_width(cell.get_size(self.treeview)[2])
        column.pack_start(cell, expand=True)
        column.add_attribute(cell, "text", treemodel.REVNO)
        self.treeview.append_column(column)

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
        column = gtk.TreeViewColumn("Message")
        column.set_resizable(True)
        column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        column.set_fixed_width(cell.get_size(self.treeview)[2])
        column.pack_start(cell, expand=True)
        column.add_attribute(cell, "text", treemodel.MESSAGE)
        self.treeview.append_column(column)

        cell = gtk.CellRendererText()
        cell.set_property("width-chars", 15)
        cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        column = gtk.TreeViewColumn("Committer")
        column.set_resizable(True)
        column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        column.set_fixed_width(cell.get_size(self.treeview)[2])
        column.pack_start(cell, expand=True)
        column.add_attribute(cell, "text", treemodel.COMMITER)
        self.treeview.append_column(column)

    def set_branch(self, branch, start, maxnum):
        self.branch = branch

        gobject.idle_add(self.populate, start, maxnum)

    def populate(self, start, maxnum):
        self.branch.lock_read()

        (linegraphdata, index, columns_len) = linegraph(self.branch,
                                                        start,
                                                        maxnum)

        self.model = TreeModel(self.branch, linegraphdata)
        self.graph_cell.columns_len = columns_len
        width = self.graph_cell.get_size(self.treeview)[2]
        self.graph_column.set_fixed_width(width)
        self.graph_column.set_max_width(width)
        self.index = index
        self.treeview.set_model(self.model)
        self.treeview.get_selection().select_path(0)

        return False
    
    def _on_selection_changed(self, selection, *args):
        """callback for when the treeview changes."""
        (model, selected_rows) = selection.get_selected_rows()
        if len(selected_rows) > 0:
            iter = self.model.get_iter(selected_rows[0])
            self.revision = self.model.get_value(iter, treemodel.REVISION)
            self.parents = self.model.get_value(iter, treemodel.PARENTS)
            self.children = self.model.get_value(iter, treemodel.CHILDREN)

    def _on_revision_selected(self, widget, event):
        from bzrlib.plugins.gtk.revisionmenu import RevisionPopupMenu
        if event.button == 3:
            menu = RevisionPopupMenu(self.branch.repository, 
                [x.revision_id for x in self.selected_revisions()],
                self.branch)
            menu.popup(None, None, None, event.button, event.get_time())

    def _on_revision_activated(self, widget, path, col):
        # TODO: more than one parent
        """Callback for when a treeview row gets activated."""
        revision_id = self.model[path][treemodel.REVID]
        parents = self.model[path][treemodel.PARENTS]
        if len(parents) == 0:
            # Ignore revisions without parent
            return
        parent_id = parents[0]
        self.show_diff(self.branch, revision_id, parent_id)
        self.treeview.grab_focus()
