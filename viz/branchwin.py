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
from bzrlib.plugins.gtk.tags import AddTagDialog
from bzrlib.plugins.gtk.preferences import PreferencesWindow
from bzrlib.plugins.gtk.branchview import TreeView
from bzrlib.revision import Revision
from bzrlib.config import BranchConfig
from bzrlib.config import GlobalConfig

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

        self.branch      = branch
        self.start       = start
        self.maxnum      = maxnum
        self.config      = GlobalConfig()

        if self.config.get_user_option('viz-compact-view') == 'yes':
            self.compact_view = True
        else:
            self.compact_view = False

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

        gtk.accel_map_add_entry("<viz>/Go/Next Revision", gtk.keysyms.Up, gtk.gdk.MOD1_MASK)
        gtk.accel_map_add_entry("<viz>/Go/Previous Revision", gtk.keysyms.Down, gtk.gdk.MOD1_MASK)

        self.accel_group = gtk.AccelGroup()
        self.add_accel_group(self.accel_group)

        gtk.Action.set_tool_item_type(gtk.MenuToolButton)

        self.prev_rev_action = gtk.Action("prev-rev", "_Previous Revision", "Go to the previous revision", gtk.STOCK_GO_DOWN)
        self.prev_rev_action.set_accel_path("<viz>/Go/Previous Revision")
        self.prev_rev_action.set_accel_group(self.accel_group)
        self.prev_rev_action.connect("activate", self._back_clicked_cb)
        self.prev_rev_action.connect_accelerator()

        self.next_rev_action = gtk.Action("next-rev", "_Next Revision", "Go to the next revision", gtk.STOCK_GO_UP)
        self.next_rev_action.set_accel_path("<viz>/Go/Next Revision")
        self.next_rev_action.set_accel_group(self.accel_group)
        self.next_rev_action.connect("activate", self._fwd_clicked_cb)
        self.next_rev_action.connect_accelerator()

        self.construct()

    def set_revision(self, revid):
        self.treeview.set_revision_id(revid)

    def construct(self):
        """Construct the window contents."""
        vbox = gtk.VBox(spacing=0)
        self.add(vbox)

        self.paned = gtk.VPaned()
        self.paned.pack1(self.construct_top(), resize=True, shrink=False)
        self.paned.pack2(self.construct_bottom(), resize=False, shrink=True)
        self.paned.show()

        vbox.pack_start(self.construct_menubar(), expand=False, fill=True)
        vbox.pack_start(self.construct_navigation(), expand=False, fill=True)
        vbox.pack_start(self.construct_loading_msg(), expand=False, fill=True)
        
        vbox.pack_start(self.paned, expand=True, fill=True)
        vbox.set_focus_child(self.paned)

        vbox.show()

    def construct_menubar(self):
        menubar = gtk.MenuBar()

        file_menu = gtk.Menu()
        file_menuitem = gtk.MenuItem("_File")
        file_menuitem.set_submenu(file_menu)

        file_menu_close = gtk.ImageMenuItem(gtk.STOCK_CLOSE, self.accel_group)
        file_menu_close.connect('activate', lambda x: self.destroy())
        
        file_menu_quit = gtk.ImageMenuItem(gtk.STOCK_QUIT, self.accel_group)
        file_menu_quit.connect('activate', lambda x: gtk.main_quit())
        
        if self._parent is not None:
            file_menu.add(file_menu_close)
        file_menu.add(file_menu_quit)

        edit_menu = gtk.Menu()
        edit_menuitem = gtk.MenuItem("_Edit")
        edit_menuitem.set_submenu(edit_menu)

        edit_menu_find = gtk.ImageMenuItem(gtk.STOCK_FIND)

        edit_menu_branchopts = gtk.MenuItem("Branch Settings")
        edit_menu_branchopts.connect('activate', lambda x: PreferencesWindow(self.branch.get_config()).show())

        edit_menu_globopts = gtk.MenuItem("Global Settings")
        edit_menu_globopts.connect('activate', lambda x: PreferencesWindow().show())

        edit_menu.add(edit_menu_find)
        edit_menu.add(edit_menu_branchopts)
        edit_menu.add(edit_menu_globopts)

        view_menu = gtk.Menu()
        view_menuitem = gtk.MenuItem("_View")
        view_menuitem.set_submenu(view_menu)

        view_menu_toolbar = gtk.CheckMenuItem("Show Toolbar")
        view_menu_toolbar.set_active(True)
        view_menu_toolbar.connect('toggled', self._toolbar_visibility_changed)

        view_menu_compact = gtk.CheckMenuItem("Show Compact Graph")
        view_menu_compact.set_active(self.compact_view)
        view_menu_compact.connect('activate', self._brokenlines_toggled_cb)

        view_menu.add(view_menu_toolbar)
        view_menu.add(view_menu_compact)
        view_menu.add(gtk.SeparatorMenuItem())

        for (label, name) in [("Revision _Number", "revno"), ("_Date", "date")]:
            col = gtk.CheckMenuItem("Show " + label + " Column")
            col.set_active(self.treeview.get_property(name + "-column-visible"))
            col.connect('toggled', self._col_visibility_changed, name)
            view_menu.add(col)

        go_menu = gtk.Menu()
        go_menu.set_accel_group(self.accel_group)
        go_menuitem = gtk.MenuItem("_Go")
        go_menuitem.set_submenu(go_menu)
        
        go_menu_next = self.next_rev_action.create_menu_item()
        go_menu_prev = self.prev_rev_action.create_menu_item()

        self.go_menu_tags = gtk.MenuItem("_Tags")
        self._update_tags()

        go_menu.add(go_menu_next)
        go_menu.add(go_menu_prev)
        go_menu.add(gtk.SeparatorMenuItem())
        go_menu.add(self.go_menu_tags)

        revision_menu = gtk.Menu()
        revision_menuitem = gtk.MenuItem("_Revision")
        revision_menuitem.set_submenu(revision_menu)

        revision_menu_diff = gtk.MenuItem("View Changes")
        revision_menu_diff.connect('activate', 
                lambda w: self.treeview.show_diff())

        revision_menu_tag = gtk.MenuItem("Tag Revision")
        revision_menu_tag.connect('activate', self._tag_revision_cb)

        revision_menu.add(revision_menu_tag)
        revision_menu.add(revision_menu_diff)

        branch_menu = gtk.Menu()
        branch_menuitem = gtk.MenuItem("_Branch")
        branch_menuitem.set_submenu(branch_menu)

        branch_menu.add(gtk.MenuItem("Pu_ll Revisions"))
        branch_menu.add(gtk.MenuItem("Pu_sh Revisions"))

        help_menu = gtk.Menu()
        help_menuitem = gtk.MenuItem("_Help")
        help_menuitem.set_submenu(help_menu)

        help_about_menuitem = gtk.ImageMenuItem(gtk.STOCK_ABOUT, self.accel_group)
        help_about_menuitem.connect('activate', self._about_dialog_cb)

        help_menu.add(help_about_menuitem)

        menubar.add(file_menuitem)
        menubar.add(edit_menuitem)
        menubar.add(view_menuitem)
        menubar.add(go_menuitem)
        menubar.add(revision_menuitem)
        menubar.add(branch_menuitem)
        menubar.add(help_menuitem)
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

        self.treeview = TreeView(self.branch, self.start, self.maxnum, self.compact_view)

        self.treeview.connect('revision-selected',
                self._treeselection_changed_cb)

        self.treeview.connect('revisions-loaded', 
                lambda x: self.loading_msg_box.hide())

        self.treeview.connect('tag-added', lambda w, t, r: self._update_tags())

        for col in ["revno", "date"]:
            option = self.config.get_user_option(col + '-column-visible')
            if option is not None:
                self.treeview.set_property(col + '-column-visible', option == 'True')

        self.treeview.show()

        align = gtk.Alignment(0.0, 0.0, 1.0, 1.0)
        align.set_padding(5, 0, 0, 0)
        align.add(self.treeview)
        align.show()

        return align

    def construct_navigation(self):
        """Construct the navigation buttons."""
        self.toolbar = gtk.Toolbar()
        self.toolbar.set_style(gtk.TOOLBAR_BOTH_HORIZ)

        self.prev_button = self.prev_rev_action.create_tool_item()
        self.toolbar.insert(self.prev_button, -1)

        self.next_button = self.next_rev_action.create_tool_item()
        self.toolbar.insert(self.next_button, -1)

        self.toolbar.insert(gtk.SeparatorToolItem(), -1)

        refresh_button = gtk.ToolButton(gtk.STOCK_REFRESH)
        refresh_button.connect('clicked', self._refresh_clicked)
        self.toolbar.insert(refresh_button, -1)

        self.toolbar.show_all()

        return self.toolbar

    def construct_bottom(self):
        """Construct the bottom half of the window."""
        from bzrlib.plugins.gtk.revisionview import RevisionView
        self.revisionview = RevisionView(branch=self.branch)
        (width, height) = self.get_size()
        self.revisionview.set_size_request(width, int(height / 2.5))
        self.revisionview.show()
        self.revisionview.set_show_callback(self._show_clicked_cb)
        self.revisionview.connect('notify::revision', self._go_clicked_cb)
        self.treeview.connect('tag-added', lambda w, t, r: self.revisionview.update_tags())
        return self.revisionview

    def _tag_selected_cb(self, menuitem, revid):
        self.treeview.set_revision_id(revid)

    def _treeselection_changed_cb(self, selection, *args):
        """callback for when the treeview changes."""
        revision = self.treeview.get_revision()
        parents  = self.treeview.get_parents()
        children = self.treeview.get_children()

        if revision is not None:
            prev_menu = gtk.Menu()
            if len(parents) > 0:
                self.prev_rev_action.set_sensitive(True)
                for parent_id in parents:
                    parent = self.branch.repository.get_revision(parent_id)
                    try:
                        str = ' (' + parent.properties['branch-nick'] + ')'
                    except KeyError:
                        str = ""

                    item = gtk.MenuItem(parent.message.split("\n")[0] + str)
                    item.connect('activate', self._set_revision_cb, parent_id)
                    prev_menu.add(item)
                prev_menu.show_all()
            else:
                self.prev_rev_action.set_sensitive(False)
                prev_menu.hide()

            self.prev_button.set_menu(prev_menu)

            next_menu = gtk.Menu()
            if len(children) > 0:
                self.next_rev_action.set_sensitive(True)
                for child_id in children:
                    child = self.branch.repository.get_revision(child_id)
                    try:
                        str = ' (' + child.properties['branch-nick'] + ')'
                    except KeyError:
                        str = ""

                    item = gtk.MenuItem(child.message.split("\n")[0] + str)
                    item.connect('activate', self._set_revision_cb, child_id)
                    next_menu.add(item)
                next_menu.show_all()
            else:
                self.next_rev_action.set_sensitive(False)
                next_menu.hide()

            self.next_button.set_menu(next_menu)

            self.revisionview.set_revision(revision)
            self.revisionview.set_children(children)

    def _back_clicked_cb(self, *args):
        """Callback for when the back button is clicked."""
        self.treeview.back()
        
    def _fwd_clicked_cb(self, *args):
        """Callback for when the forward button is clicked."""
        self.treeview.forward()

    def _go_clicked_cb(self, w, p):
        """Callback for when the go button for a parent is clicked."""
        if self.revisionview.get_revision() is not None:
            self.treeview.set_revision(self.revisionview.get_revision())

    def _show_clicked_cb(self, revid, parentid):
        """Callback for when the show button for a parent is clicked."""
        self.treeview.show_diff(revid, parentid)
        self.treeview.grab_focus()

    def _set_revision_cb(self, w, revision_id):
        self.treeview.set_revision_id(revision_id)

    def _brokenlines_toggled_cb(self, button):
        self.compact_view = button.get_active()

        if self.compact_view:
            option = 'yes'
        else:
            option = 'no'

        self.config.set_user_option('viz-compact-view', option)
        self.treeview.set_property('compact', self.compact_view)
        self.treeview.refresh()

    def _tag_revision_cb(self, w):
        try:
            self.treeview.set_sensitive(False)
            dialog = AddTagDialog(self.branch.repository, self.treeview.get_revision().revision_id, self.branch)
            response = dialog.run()
            if response != gtk.RESPONSE_NONE:
                dialog.hide()
            
                if response == gtk.RESPONSE_OK:
                    self.treeview.add_tag(dialog.tagname, dialog._revid)
                
                dialog.destroy()

        finally:
            self.treeview.set_sensitive(True)

    def _about_dialog_cb(self, w):
        from bzrlib.plugins.gtk.about import AboutDialog

        AboutDialog().run()

    def _col_visibility_changed(self, col, property):
        self.config.set_user_option(property + '-column-visible', col.get_active())
        self.treeview.set_property(property + '-column-visible', col.get_active())

    def _toolbar_visibility_changed(self, col):
        if col.get_active():
            self.toolbar.show() 
        else:
            self.toolbar.hide()

    def _show_about_cb(self, w):
        dialog = AboutDialog()
        dialog.connect('response', lambda d,r: d.destroy())
        dialog.run()

    def _refresh_clicked(self, w):
        self.treeview.update()

    def _update_tags(self):
        menu = gtk.Menu()

        if self.branch.supports_tags():
            tags = self.branch.tags.get_tag_dict().items()
            tags.sort()
            tags.reverse()
            for tag, revid in tags:
                tag_item = gtk.MenuItem(tag)
                tag_item.connect('activate', self._tag_selected_cb, revid)
                menu.add(tag_item)
            self.go_menu_tags.set_submenu(menu)

            self.go_menu_tags.set_sensitive(len(tags) != 0)
        else:
            self.go_menu_tags.set_sensitive(False)

        self.go_menu_tags.show_all()


