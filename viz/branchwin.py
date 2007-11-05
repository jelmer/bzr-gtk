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

from bzrlib.plugins.gtk.window import Window
from bzrlib.plugins.gtk.preferences import PreferencesWindow
from bzrlib.revision import Revision
from treeview import TreeView

class BranchWindow(Window):
    """Branch window.

    This object represents and manages a single window containing information
    for a particular branch.
    """

    def __init__(self, branch, start, maxnum, parent=None):
        """Create a new BranchWindow.

        :param branch: Branch object for branch to show.
        :param start: Revision id of top revision.
        :param maxnum: Maximum number of revisions to display, 
                       None for no limit.
        """

        Window.__init__(self, parent=parent)
        self.set_border_width(0)

        self.branch = branch
        self.start  = start
        self.maxnum = maxnum

        self.set_title(branch.nick + " - revision history")

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

        top = self.construct_top()

        vbox.pack_start(self.construct_menubar(), expand=False, fill=True)
        vbox.pack_start(self.construct_navigation(), expand=False, fill=True)
        vbox.pack_start(self.construct_loading_msg(), expand=False, fill=True)
        
        paned = gtk.VPaned()
        paned.pack1(top, resize=True, shrink=False)
        paned.pack2(self.construct_bottom(), resize=False, shrink=True)
        paned.show()
        vbox.pack_start(paned, expand=True, fill=True)
        vbox.set_focus_child(paned)

        vbox.show()

    def construct_menubar(self):
        menubar = gtk.MenuBar()

        file_menu = gtk.Menu()
        file_menuitem = gtk.MenuItem("_File")
        file_menuitem.set_submenu(file_menu)

        file_menu_close = gtk.ImageMenuItem(gtk.STOCK_CLOSE)
        file_menu_close.connect('activate', lambda x: self.destroy())
        
        file_menu.add(file_menu_close)

        edit_menu = gtk.Menu()
        edit_menuitem = gtk.MenuItem("_Edit")
        edit_menuitem.set_submenu(edit_menu)

        edit_menu_find = gtk.ImageMenuItem(gtk.STOCK_FIND)

        edit_menu_prefs = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
        edit_menu_prefs.connect('activate', lambda x: PreferencesWindow(self.branch.get_config()).show())

        edit_menu.add(edit_menu_find)
        edit_menu.add(edit_menu_prefs)

        view_menu = gtk.Menu()
        view_menuitem = gtk.MenuItem("_View")
        view_menuitem.set_submenu(view_menu)

        view_menu_toolbar = gtk.CheckMenuItem("Show Toolbar")
        view_menu_toolbar.set_active(True)
        view_menu_toolbar.connect('toggled', self._toolbar_visibility_changed)

        view_menu.add(view_menu_toolbar)
        view_menu.add(gtk.SeparatorMenuItem())

        for (label, name) in [("Revision _Number", "revno"), ("_Date", "date")]:
            col = gtk.CheckMenuItem("Show " + label + " Column")
            col.set_active(self.treeview.get_property(name + "-column-visible"))
            col.connect('toggled', self._col_visibility_changed, name)
            view_menu.add(col)

        go_menu = gtk.Menu()
        go_menuitem = gtk.MenuItem("_Go")
        go_menuitem.set_submenu(go_menu)
        
        go_menu_back = gtk.ImageMenuItem(gtk.STOCK_GO_DOWN)
        go_menu_back.connect("activate", self._back_clicked_cb)

        go_menu_forward = gtk.ImageMenuItem(gtk.STOCK_GO_UP)
        go_menu_forward.connect("activate", self._fwd_clicked_cb)

        tags_menu = gtk.Menu()
        go_menu_tags = gtk.MenuItem("_Tags")
        go_menu_tags.set_submenu(tags_menu)

        for (tag, revid) in self.branch.tags.get_tag_dict().items():
            tag_item = gtk.MenuItem(tag)
            tag_item.connect('activate', self._tag_selected_cb, revid)
            tags_menu.add(tag_item)

        go_menu.add(go_menu_back)
        go_menu.add(go_menu_forward)
        go_menu.add(gtk.SeparatorMenuItem())
        go_menu.add(go_menu_tags)

        revision_menu = gtk.Menu()
        revision_menuitem = gtk.MenuItem("_Revision")
        revision_menuitem.set_submenu(revision_menu)

        revision_menu.add(gtk.MenuItem("Tag Revision"))
        revision_menu.add(gtk.MenuItem("View Changes"))

        branch_menu = gtk.Menu()
        branch_menuitem = gtk.MenuItem("_Branch")
        branch_menuitem.set_submenu(branch_menu)

        branch_menu.add(gtk.MenuItem("Pu_ll Revisions"))
        branch_menu.add(gtk.MenuItem("Pu_sh Revisions"))
       
        menubar.add(file_menuitem)
        menubar.add(edit_menuitem)
        menubar.add(view_menuitem)
        menubar.add(go_menuitem)
        menubar.add(revision_menuitem)
        menubar.add(branch_menuitem)
        menubar.show_all()

        return menubar
    
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
        # FIXME: Make broken_line_length configurable
        self.treeview = TreeView(self.branch, self.start, self.maxnum, 32)

        self.treeview.connect("revision-selected",
                self._treeselection_changed_cb)

        self.treeview.connect('revisions-loaded', 
                lambda x: self.loading_msg_box.hide())

        self.treeview.show()

        return self.treeview

    def construct_navigation(self):
        """Construct the navigation buttons."""
        self.toolbar = gtk.Toolbar()
        self.toolbar.set_style(gtk.TOOLBAR_BOTH_HORIZ)

        self.back_button = gtk.MenuToolButton(stock_id=gtk.STOCK_GO_DOWN)
        self.back_button.add_accelerator("clicked", self.accel_group, ord('['),
                                         0, 0)
        self.back_button.connect("clicked", self._back_clicked_cb)
        self.toolbar.insert(self.back_button, -1)
        self.back_button.show()

        self.fwd_button = gtk.MenuToolButton(stock_id=gtk.STOCK_GO_UP)
        self.fwd_button.add_accelerator("clicked", self.accel_group, ord(']'),
                                        0, 0)
        self.fwd_button.connect("clicked", self._fwd_clicked_cb)
        self.toolbar.insert(self.fwd_button, -1)
        self.fwd_button.show()

        self.toolbar.show()

        return self.toolbar

    def construct_bottom(self):
        """Construct the bottom half of the window."""
        from bzrlib.plugins.gtk.revisionview import RevisionView
        self.revisionview = RevisionView(None, tags=[], show_children=True, branch=self.branch)
        (width, height) = self.get_size()
        self.revisionview.set_size_request(width, int(height / 2.5))
        self.revisionview.show()
        self.revisionview.set_show_callback(self._show_clicked_cb)
        self.revisionview.set_go_callback(self._go_clicked_cb)
        return self.revisionview

    def _tag_selected_cb(self, menuitem, revid):
        self.treeview.set_revision_id(revid)

    def _treeselection_changed_cb(self, selection, *args):
        """callback for when the treeview changes."""
        revision = self.treeview.get_revision()
        parents  = self.treeview.get_parents()
        children = self.treeview.get_children()

        if revision is not None:
            back_menu = gtk.Menu()
            if len(parents) > 0:
                self.back_button.set_sensitive(True)
                for parent_id in parents:
                    parent = self.branch.repository.get_revision(parent_id)
                    try:
                        str = ' (' + parent.properties['branch-nick'] + ')'
                    except KeyError:
                        str = ""

                    item = gtk.MenuItem(parent.message.split("\n")[0] + str)
                    item.connect('activate', self._set_revision_cb, parent_id)
                    back_menu.add(item)
                back_menu.show_all()
            else:
                self.back_button.set_sensitive(False)
                back_menu.hide()

            self.back_button.set_menu(back_menu)

            fwd_menu = gtk.Menu()
            if len(children) > 0:
                self.fwd_button.set_sensitive(True)
                for child_id in children:
                    child = self.branch.repository.get_revision(child_id)
                    try:
                        str = ' (' + child.properties['branch-nick'] + ')'
                    except KeyError:
                        str = ""

                    item = gtk.MenuItem(child.message.split("\n")[0] + str)
                    item.connect('activate', self._set_revision_cb, child_id)
                    fwd_menu.add(item)
                fwd_menu.show_all()
            else:
                self.fwd_button.set_sensitive(False)
                fwd_menu.hide()

            self.fwd_button.set_menu(fwd_menu)

            tags = []
            if self.branch.supports_tags():
                tagdict = self.branch.tags.get_reverse_tag_dict()
                if tagdict.has_key(revision.revision_id):
                    tags = tagdict[revision.revision_id]
            self.revisionview.set_revision(revision, tags, children)

    def _back_clicked_cb(self, *args):
        """Callback for when the back button is clicked."""
        self.treeview.back()
        
    def _fwd_clicked_cb(self, *args):
        """Callback for when the forward button is clicked."""
        self.treeview.forward()

    def _go_clicked_cb(self, revid):
        """Callback for when the go button for a parent is clicked."""
        self.treeview.set_revision_id(revid)

    def _show_clicked_cb(self, revid, parentid):
        """Callback for when the show button for a parent is clicked."""
        self.treeview.show_diff(self.branch, revid, parentid)
        self.treeview.grab_focus()

    def _set_revision_cb(self, w, revision_id):
        self.treeview.set_revision_id(revision_id)

    def _col_visibility_changed(self, col, property):
        self.treeview.set_property(property + '-column-visible', col.get_active())

    def _toolbar_visibility_changed(self, col):
        if col.get_active():
            self.toolbar.show() 
        else:
            self.toolbar.hide()
