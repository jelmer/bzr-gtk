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
import treemodel

from bzrlib.osutils import format_date

from linegraph import linegraph, same_branch
from graphcell import CellRendererGraph
from treemodel import TreeModel
from treeview  import TreeView

class BranchWindow(gtk.Window):
    """Branch window.

    This object represents and manages a single window containing information
    for a particular branch.
    """

    def __init__(self, parent=None):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.set_border_width(0)
        self.set_title("Revision history")

        self._parent = parent

        self.connect('key-press-event', self._on_key_pressed)
        self.connect("destroy", lambda w: self.branch.unlock())

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
        vbox.pack_start(self.construct_loading_msg(), expand=False, fill=True)
        
        paned = gtk.VPaned()
        paned.pack1(self.construct_top(), resize=True, shrink=False)
        paned.pack2(self.construct_bottom(), resize=False, shrink=True)
        paned.show()
        vbox.pack_start(paned, expand=True, fill=True)
        vbox.set_focus_child(paned)

        vbox.show()
    
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

    def construct_top(self):
        """Construct the top-half of the window."""
        self.treeview = TreeView()

        self.treeview.treeview.get_selection().connect("changed",
                self._treeselection_changed_cb)

        self.treeview.show()

        return self.treeview

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
        self.logview = LogView(None, True, [], True)
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
        self.set_title(branch.nick + " - revision history")
        self.treeview.set_branch(branch, start, maxnum)
    
    def _on_key_pressed(self, widget, event):
        """ Key press event handler. """
        keyname = gtk.gdk.keyval_name(event.keyval)
        func = getattr(self, '_on_key_press_' + keyname, None)
        if func:
            return func(event)

    def _on_key_press_w(self, event):
        if event.state & gtk.gdk.CONTROL_MASK:
            self.destroy()
            if self._parent is None:
                gtk.main_quit()

    def _on_key_press_q(self, event):
        if event.state & gtk.gdk.CONTROL_MASK:
            gtk.main_quit()
    
    def _treeselection_changed_cb(self, selection, *args):
        """callback for when the treeview changes."""
        revision = self.treeview.get_revision()
        parents  = self.treeview.get_parents()
        children = self.treeview.get_children()

        if revision is not None:
            self.back_button.set_sensitive(len(parents) > 0)
            self.fwd_button.set_sensitive(len(children) > 0)
            tags = []
            if self.branch.supports_tags():
                tagdict = self.branch.tags.get_reverse_tag_dict()
                if tagdict.has_key(revision.revision_id):
                    tags = tagdict[revision.revision_id]
            self.logview.set_revision(revision, tags, children)

    def _back_clicked_cb(self, *args):
        """Callback for when the back button is clicked."""
        self.treeview.back()
        
    def _fwd_clicked_cb(self, *args):
        """Callback for when the forward button is clicked."""
        self.treeview.forward()

    def _go_clicked_cb(self, revid):
        """Callback for when the go button for a parent is clicked."""
        self.treeview.set_cursor(self.index[revid])
        self.treeview.grab_focus()

    def show_diff(self, branch, revid, parentid):
        """Open a new window to show a diff between the given revisions."""
        from bzrlib.plugins.gtk.diff import DiffWindow
        window = DiffWindow(parent=self)
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
        return self.model[path][treemodel.REVISION]

    def selected_revisions(self):
        return [self.selected_revision(path) for path in \
                self.treeview.get_selection().get_selected_rows()[1]]

    def _treeview_row_activated_cb(self, widget, path, col):
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
