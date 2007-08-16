# -*- coding: UTF-8 -*-
"""Branch window.

This module contains the code to manage the branch information window,
which contains both the revision graph and details panes.
"""

__copyright__ = "Copyright © 2005 Canonical Ltd."
__author__    = "Scott James Remnant <scott@ubuntu.com>"


import gtk
import gobject
import pango

from bzrlib.osutils import format_date

from linegraph import linegraph, same_branch
from graphcell import CellRendererGraph


class BranchWindow(gtk.Window):
    """Branch window.

    This object represents and manages a single window containing information
    for a particular branch.
    """

    def __init__(self):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.set_border_width(0)
        self.set_title("bzrk")

        # Use three-quarters of the screen by default
        screen = self.get_screen()
        monitor = screen.get_monitor_geometry(0)
        width = int(monitor.width * 0.75)
        height = int(monitor.height * 0.75)
        self.set_default_size(width, height)

        # FIXME AndyFitz!
        icon = self.render_icon(gtk.STOCK_INDEX, gtk.ICON_SIZE_BUTTON)
        self.set_icon(icon)

        self.accel_group = gtk.AccelGroup()
        self.add_accel_group(self.accel_group)

        self.construct()

    def construct(self):
        """Construct the window contents."""
        vbox = gtk.VBox(spacing=0)
        self.add(vbox)

        vbox.pack_start(self.construct_navigation(), expand=False, fill=True)

        paned = gtk.VPaned()
        paned.pack1(self.construct_top(), resize=True, shrink=False)
        paned.pack2(self.construct_bottom(), resize=False, shrink=True)
        paned.show()
        vbox.pack_start(paned, expand=True, fill=True)
        vbox.set_focus_child(paned)

        vbox.show()

    def construct_top(self):
        """Construct the top-half of the window."""
        scrollwin = gtk.ScrolledWindow()
        scrollwin.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scrollwin.set_shadow_type(gtk.SHADOW_IN)
        scrollwin.show()

        self.treeview = gtk.TreeView()
        self.treeview.set_rules_hint(True)
        self.treeview.set_search_column(4)
        self.treeview.connect("cursor-changed", self._treeview_cursor_cb)
        self.treeview.connect("row-activated", self._treeview_row_activated_cb)
        self.treeview.connect("button-release-event", 
                self._treeview_row_mouseclick)
        scrollwin.add(self.treeview)
        self.treeview.show()

        cell = CellRendererGraph()
        column = gtk.TreeViewColumn()
        column.set_resizable(True)
        column.pack_start(cell, expand=False)
        column.add_attribute(cell, "node", 1)
        column.add_attribute(cell, "in-lines", 2)
        column.add_attribute(cell, "out-lines", 3)
        self.treeview.append_column(column)

        cell = gtk.CellRendererText()
        cell.set_property("width-chars", 40)
        cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        column = gtk.TreeViewColumn("Message")
        column.set_resizable(True)
        column.pack_start(cell, expand=True)
        column.add_attribute(cell, "text", 6)
        self.treeview.append_column(column)

        cell = gtk.CellRendererText()
        cell.set_property("width-chars", 40)
        cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        column = gtk.TreeViewColumn("Committer")
        column.set_resizable(True)
        column.pack_start(cell, expand=True)
        column.add_attribute(cell, "text", 7)
        self.treeview.append_column(column)

        cell = gtk.CellRendererText()
        cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        column = gtk.TreeViewColumn("Date")
        column.set_resizable(True)
        column.pack_start(cell, expand=True)
        column.add_attribute(cell, "text", 8)
        self.treeview.append_column(column)

        return scrollwin

    def construct_navigation(self):
        """Construct the navigation buttons."""
        frame = gtk.Frame()
        frame.set_shadow_type(gtk.SHADOW_OUT)
        frame.show()
        
        hbox = gtk.HBox(spacing=12)
        frame.add(hbox)
        hbox.show()

        self.back_button = gtk.Button(stock=gtk.STOCK_GO_BACK)
        self.back_button.set_relief(gtk.RELIEF_NONE)
        self.back_button.add_accelerator("clicked", self.accel_group, ord('['),
                                         0, 0)
        self.back_button.connect("clicked", self._back_clicked_cb)
        hbox.pack_start(self.back_button, expand=False, fill=True)
        self.back_button.show()

        self.fwd_button = gtk.Button(stock=gtk.STOCK_GO_FORWARD)
        self.fwd_button.set_relief(gtk.RELIEF_NONE)
        self.fwd_button.add_accelerator("clicked", self.accel_group, ord(']'),
                                        0, 0)
        self.fwd_button.connect("clicked", self._fwd_clicked_cb)
        hbox.pack_start(self.fwd_button, expand=False, fill=True)
        self.fwd_button.show()

        return frame

    def construct_bottom(self):
        """Construct the bottom half of the window."""
        from bzrlib.plugins.gtk.logview import LogView
        self.logview = LogView()
        (width, height) = self.get_size()
        self.logview.set_size_request(width, int(height / 2.5))
        self.logview.show()
        self.logview.set_show_callback(self._show_clicked_cb)
        self.logview.set_go_callback(self._go_clicked_cb)
        return self.logview

    def set_branch(self, branch, start, maxnum):
        """Set the branch and start position for this window.
        
        Creates a new TreeModel and populates it with information about
        the new branch before updating the window title and model of the
        treeview itself.
        """
        self.branch = branch
        
        # [ revision, node, last_lines, lines, message, committer, timestamp ]
        self.model = gtk.ListStore(gobject.TYPE_PYOBJECT,
                                   gobject.TYPE_PYOBJECT,
                                   gobject.TYPE_PYOBJECT,
                                   gobject.TYPE_PYOBJECT,
                                   gobject.TYPE_PYOBJECT,
                                   gobject.TYPE_PYOBJECT,
                                   str, str, str)
        self.index = {}
        revids = []
        for (index, revid) in enumerate(reversed( \
                branch.repository.get_ancestry(branch.last_revision()))):
            if revid is not None:
                revids.append(revid)
                self.index[revid] = index
            if maxnum is not None and index > maxnum:
                break
        
        
        self.revisions = branch.repository.get_revisions(revids)
        revisionparents = branch.repository.get_graph().get_parents(revids)
        
        
        last_lines = []
        for (index,(revision, node, lines, parents, children)) in enumerate( \
                linegraph(self.revisions, revisionparents, self.index)):
            # FIXME: at this point we should be able to show the graph order
            # and lines with no message or commit data - and then incrementally
            # fill the timestamp, committer etc data as desired.
            
            message = revision.message.split("\n")[0]
            
            if revision.committer is not None:
                timestamp = format_date(revision.timestamp, revision.timezone)
            else:
                timestamp = None
            self.model.append([revision, node, last_lines, lines,
                               parents, children, 
                               message, revision.committer, timestamp])
            last_lines = lines
        
        self.set_title(branch.nick + " - bzrk")
        self.treeview.set_model(self.model)
    def _treeview_cursor_cb(self, *args):
        """Callback for when the treeview cursor changes."""
        (path, col) = self.treeview.get_cursor()
        revision = self.model[path][0]
        parents = self.model[path][4]
        children = self.model[path][5]

        self.back_button.set_sensitive(len(parents) > 0)
        self.fwd_button.set_sensitive(len(children) > 0)
        tags = []
        if self.branch.supports_tags():
            tagdict = self.branch.tags.get_reverse_tag_dict()
            if tagdict.has_key(revision.revision_id):
                tags = tagdict[revision.revision_id]
        self.logview.set_revision(revision, tags)

    def _back_clicked_cb(self, *args):
        """Callback for when the back button is clicked."""
        (path, col) = self.treeview.get_cursor()
        revision = self.model[path][0]
        parents = self.model[path][4]
        if not len(parents):
            return

        for parent_id in parents:
            parent = self.revisions[self.index[parent_id]]
            if same_branch(revision, parent):
                self.treeview.set_cursor(self.index[parent_id])
                break
        else:
            self.treeview.set_cursor(self.index[parents[0]])
        self.treeview.grab_focus()

    def _fwd_clicked_cb(self, *args):
        """Callback for when the forward button is clicked."""
        (path, col) = self.treeview.get_cursor()
        revision = self.model[path][0]
        children = self.model[path][5]
        if not len(children):
            return

        for child_id in children:
            child = self.revisions[self.index[child_id]]
            if same_branch(child, revision):
                self.treeview.set_cursor(self.index[child_id])
                break
        else:
            self.treeview.set_cursor(self.index[children[0]])
        self.treeview.grab_focus()

    def _go_clicked_cb(self, revid):
        """Callback for when the go button for a parent is clicked."""
        self.treeview.set_cursor(self.index[revid])
        self.treeview.grab_focus()

    def show_diff(self, branch, revid, parentid):
        """Open a new window to show a diff between the given revisions."""
        from bzrlib.plugins.gtk.diff import DiffWindow
        window = DiffWindow()
        (parent_tree, rev_tree) = branch.repository.revision_trees([parentid, 
                                                                   revid])
        description = revid + " - " + branch.nick
        window.set_diff(description, rev_tree, parent_tree)
        window.show()

    def _show_clicked_cb(self, revid, parentid):
        """Callback for when the show button for a parent is clicked."""
        self.show_diff(self.branch, revid, parentid)
        self.treeview.grab_focus()

    def _treeview_row_mouseclick(self, widget, event):
        from bzrlib.plugins.gtk.revisionmenu import RevisionPopupMenu
        if event.button == 3:
            menu = RevisionPopupMenu(self.branch.repository, 
                [x.revision_id for x in self.selected_revisions()],
                self.branch)
            menu.popup(None, None, None, event.button, event.get_time())

    def selected_revision(self, path):
        return self.model[path][0]

    def selected_revisions(self):
        return [self.selected_revision(path) for path in \
                self.treeview.get_selection().get_selected_rows()[1]]

    def _treeview_row_activated_cb(self, widget, path, col):
        # TODO: more than one parent
        """Callback for when a treeview row gets activated."""
        revision = self.selected_revision(path)
        if len(self.parent_ids[revision]) == 0:
            # Ignore revisions without parent
            return
        parent_id = self.parent_ids[revision][0]
        self.show_diff(self.branch, revision.revision_id, parent_id)
        self.treeview.grab_focus()



