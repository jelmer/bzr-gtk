# Copyright (C) 2006 by Szilveszter Farkas (Phanatic) <szilveszter.farkas@gmail.com>
# Some parts of the code are:
# Copyright (C) 2005, 2006 by Canonical Ltd
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import os
import gtk
import gobject

from bzrlib.plugins.gtk import _i18n, icon_path


class OliveGui(gtk.Window):
    """ Olive main window """
    
    def __init__(self, calling_app):
        # Pointer to calling instance for signal connection
        self.signal = calling_app
        
        # Initialise window
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.set_title(_i18n("Olive - Bazaar GUI"))
        self.set_icon_list(gtk.gdk.pixbuf_new_from_file(icon_path("oliveicon2.png")),
                           gtk.gdk.pixbuf_new_from_file(icon_path("olive-gtk.png")),
                           # Who has the svg version of the icon? Would be nice to include
                           #gtk.gdk.pixbuf_new_from_file(icon_path("olive.svg"))
                           )
        self.set_property("width-request", 700)
        self.set_property("height-request", 400)
        
        self.connect("destroy", self.destroy)
        self.connect("delete_event", self.signal.on_window_main_delete_event)
        
        # Accelerator group to Quit program
        accelgroup = gtk.AccelGroup()
        self.add_accel_group(accelgroup)
        self.quit_action = gtk.Action(_i18n("Quit"), None, None, gtk.STOCK_QUIT)
        self.quit_action.connect('activate', self.signal.on_window_main_delete_event)
        actiongroup = gtk.ActionGroup('QuitAction')
        actiongroup.add_action_with_accel(self.quit_action, None)
        self.quit_action.set_accel_group(accelgroup)
        self.quit_action.connect_accelerator()
        
        # High level build up of window
        self.vbox = gtk.VBox(False, 0)
        self.add(self.vbox)
        
        # Menu bar
        self._create_menubar()
        self.vbox.pack_start(self.mb, False, False, 0)
        
        # Toolbar
        self._create_toolbar()
        self.vbox.pack_start(self.tb, False, False, 0)
        
        # Locationbar
        self._create_locationbar()
        self.vbox.pack_start(self.locationbar, False, False, 0)
        
        # Main area
        self.hpaned_main = gtk.HPaned()
        self._create_bookmarklist()
        self.hpaned_main.add(self.scrolledwindow_left)
        self._create_filelist()
        self.hpaned_main.add(self.scrolledwindow_right)
        self.vbox.pack_start(self.hpaned_main, True, True, 0)
        
        # Statusbar
        self.statusbar = gtk.Statusbar()
        self.vbox.pack_end(self.statusbar, False, False, 0)
    
    def show(self):
        self.show_all()        
    
    def destroy(self, widget=None, data=None):
        """ Ends the program """
        gtk.main_quit()

    def _create_menubar(self):
        self.mb = gtk.MenuBar()
        
        # File menu
        self.mb_file = gtk.MenuItem(_i18n("_File"))
        self.mb_file_menu = gtk.Menu()
        
        self.mb_file_add = gtk.ImageMenuItem(gtk.STOCK_ADD, _i18n("_Add file(s)"))
        self.mb_file_add.connect('activate', self.signal.on_menuitem_add_files_activate)
        self.mb_file_menu.append(self.mb_file_add)
        
        self.mb_file_remove = gtk.ImageMenuItem(gtk.STOCK_REMOVE, _i18n("_Remove file(s)"))
        self.mb_file_remove.connect('activate', self.signal.on_menuitem_remove_file_activate)
        self.mb_file_menu.append(self.mb_file_remove)
        
        self.mb_file_menu.append(gtk.SeparatorMenuItem())
        
        self.mb_file_bookmark = gtk.MenuItem(_i18n("_Bookmark current directory"))
        self.mb_file_bookmark.connect('activate', self.signal.on_menuitem_file_bookmark_activate)
        self.mb_file_menu.append(self.mb_file_bookmark)
        
        self.mb_file_mkdir = gtk.MenuItem(_i18n("_Make directory"))
        self.mb_file_mkdir.connect('activate', self.signal.on_menuitem_file_make_directory_activate)
        self.mb_file_menu.append(self.mb_file_mkdir)
        
        self.mb_file_menu.append(gtk.SeparatorMenuItem())
        
        self.mb_file_rename = gtk.MenuItem(_i18n("_Rename"))
        self.mb_file_rename.connect('activate', self.signal.on_menuitem_file_rename_activate)
        self.mb_file_menu.append(self.mb_file_rename)
        
        self.mb_file_move = gtk.MenuItem(_i18n("_Move"))
        self.mb_file_move.connect('activate', self.signal.on_menuitem_file_move_activate)
        self.mb_file_menu.append(self.mb_file_move)
        
        self.mb_file_annotate = gtk.MenuItem(_i18n("_Annotate"))
        self.mb_file_annotate.connect('activate', self.signal.on_menuitem_file_annotate_activate)
        self.mb_file_menu.append(self.mb_file_annotate)
        
        self.mb_file_menu.append(gtk.SeparatorMenuItem())
        
        self.mb_file_quit = self.quit_action.create_menu_item()
        self.mb_file_menu.append(self.mb_file_quit)
        
        self.mb_file.set_submenu(self.mb_file_menu)
        self.mb.append(self.mb_file)
        
        # View menu
        self.mb_view = gtk.MenuItem(_i18n("_View"))
        self.mb_view_menu = gtk.Menu()
        
        self.mb_view_showhidden = gtk.CheckMenuItem(_i18n("Show _hidden files"))
        self.mb_view_showhidden.connect('activate', self.signal.on_menuitem_view_show_hidden_files_activate)
        self.mb_view_menu.append(self.mb_view_showhidden)
        
        self.mb_view_showignored = gtk.CheckMenuItem(_i18n("Show _ignored files"))
        self.mb_view_showignored.connect('activate', self.signal.on_menuitem_view_show_ignored_files_activate)
        self.mb_view_menu.append(self.mb_view_showignored)
        
        self.mb_view_menu.append(gtk.SeparatorMenuItem())
        
        self.mb_view_refresh = gtk.ImageMenuItem(gtk.STOCK_REFRESH, _i18n("_Refresh"))
        self.mb_view_refresh.connect('activate', self.signal.on_menuitem_view_refresh_activate)
        self.mb_view_menu.append(self.mb_view_refresh)
        
        self.mb_view.set_submenu(self.mb_view_menu)
        self.mb.append(self.mb_view)
        
        # Branch menu
        self.mb_branch = gtk.MenuItem(_i18n("_Branch"))
        self.mb_branch_menu = gtk.Menu()
        
        self.mb_branch_initialize = gtk.MenuItem(_i18n("_Initialize"))
        self.mb_branch_initialize.connect('activate', self.signal.on_menuitem_branch_initialize_activate)
        self.mb_branch_menu.append(self.mb_branch_initialize)
        
        self.mb_branch_get = gtk.MenuItem(_i18n("_Get"))
        self.mb_branch_get.connect('activate', self.signal.on_menuitem_branch_get_activate)
        self.mb_branch_menu.append(self.mb_branch_get)
        
        self.mb_branch_checkout = gtk.MenuItem(_i18n("C_heckout"))
        self.mb_branch_checkout.connect('activate', self.signal.on_menuitem_branch_checkout_activate)
        self.mb_branch_menu.append(self.mb_branch_checkout)
        
        self.mb_branch_menu.append(gtk.SeparatorMenuItem())
        
        self.mb_branch_pull = gtk.ImageMenuItem(_i18n("Pu_ll"))
        pullimage = gtk.Image()
        pullimage.set_from_file(icon_path("pull16.png"))
        self.mb_branch_pull.set_image(pullimage)
        self.mb_branch_pull.connect('activate', self.signal.on_menuitem_branch_pull_activate)
        self.mb_branch_menu.append(self.mb_branch_pull)
        
        self.mb_branch_push = gtk.ImageMenuItem(_i18n("Pu_sh"))
        pushimage = gtk.Image()
        pushimage.set_from_file(icon_path("push16.png"))
        self.mb_branch_push.set_image(pushimage)
        self.mb_branch_push.connect('activate', self.signal.on_menuitem_branch_push_activate)
        self.mb_branch_menu.append(self.mb_branch_push)
        
        self.mb_branch_update = gtk.MenuItem(_i18n("_Update"))
        self.mb_branch_update.connect('activate', self.signal.on_menuitem_branch_update_activate)
        self.mb_branch_menu.append(self.mb_branch_update)
        
        self.mb_branch_menu.append(gtk.SeparatorMenuItem())
        
        self.mb_branch_revert = gtk.ImageMenuItem(_i18n("_Revert all changes"))
        revertimage = gtk.Image()
        revertimage.set_from_stock(gtk.STOCK_REVERT_TO_SAVED, gtk.ICON_SIZE_MENU)
        self.mb_branch_revert.set_image(revertimage)
        self.mb_branch_revert.connect('activate', self.signal.on_menuitem_branch_revert_activate)
        self.mb_branch_menu.append(self.mb_branch_revert)
        
        self.mb_branch_merge = gtk.MenuItem(_i18n("_Merge"))
        self.mb_branch_merge.connect('activate', self.signal.on_menuitem_branch_merge_activate)
        self.mb_branch_menu.append(self.mb_branch_merge)
        
        self.mb_branch_commit = gtk.ImageMenuItem(_i18n("_Commit"))
        commitimage = gtk.Image()
        commitimage.set_from_file(icon_path("commit16.png"))
        self.mb_branch_commit.set_image(commitimage)
        self.mb_branch_commit.connect('activate', self.signal.on_menuitem_branch_commit_activate)
        self.mb_branch_menu.append(self.mb_branch_commit)
        
        self.mb_branch_menu.append(gtk.SeparatorMenuItem())
        
        self.mb_branch_tags = gtk.ImageMenuItem(_i18n("Ta_gs"))
        tagsimage = gtk.Image()
        tagsimage.set_from_file(icon_path("tag-16.png"))
        self.mb_branch_tags.set_image(tagsimage)
        self.mb_branch_tags.connect('activate', self.signal.on_menuitem_branch_tags_activate)
        self.mb_branch_menu.append(self.mb_branch_tags)
        
        self.mb_branch_status = gtk.MenuItem(_i18n("S_tatus"))
        self.mb_branch_status.connect('activate', self.signal.on_menuitem_branch_status_activate)
        self.mb_branch_menu.append(self.mb_branch_status)
        
        self.mb_branch_missingrevisions = gtk.MenuItem(_i18n("Missing _revisions"))
        self.mb_branch_missingrevisions.connect('activate', self.signal.on_menuitem_branch_missing_revisions_activate)
        self.mb_branch_menu.append(self.mb_branch_missingrevisions)
        
        self.mb_branch_conflicts = gtk.MenuItem(_i18n("Con_flicts"))
        self.mb_branch_conflicts.connect('activate', self.signal.on_menuitem_branch_conflicts_activate)
        self.mb_branch_menu.append(self.mb_branch_conflicts)
        
        self.mb_branch.set_submenu(self.mb_branch_menu)
        self.mb.append(self.mb_branch)
        
        # Statistics menu
        self.mb_statistics = gtk.MenuItem(_i18n("_Statistics"))
        self.mb_statistics_menu = gtk.Menu()
        
        self.mb_statistics_differences = gtk.ImageMenuItem(_i18n("_Differences"))
        diffimage = gtk.Image()
        diffimage.set_from_file(icon_path("diff16.png"))
        self.mb_statistics_differences.set_image(diffimage)
        self.mb_statistics_differences.connect('activate', self.signal.on_menuitem_stats_diff_activate)
        self.mb_statistics_menu.append(self.mb_statistics_differences)
        
        self.mb_statistics_log = gtk.ImageMenuItem(_i18n("_Log"))
        logimage = gtk.Image()
        logimage.set_from_file(icon_path("log16.png"))
        self.mb_statistics_log.set_image(logimage)
        self.mb_statistics_log.connect('activate', self.signal.on_menuitem_stats_log_activate)
        self.mb_statistics_menu.append(self.mb_statistics_log)
        
        self.mb_statistics_information = gtk.MenuItem(_i18n("_Information"))
        self.mb_statistics_information.connect('activate', self.signal.on_menuitem_stats_infos_activate)
        self.mb_statistics_menu.append(self.mb_statistics_information)
        
        self.mb_statistics.set_submenu(self.mb_statistics_menu)
        self.mb.append(self.mb_statistics)
        
        # Help menu
        self.mb_help = gtk.MenuItem(_i18n("Help"))
        self.mb_help_menu = gtk.Menu()
        
        self.mb_help_about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
        self.mb_help_about.connect('activate', self.signal.on_about_activate)
        self.mb_help_menu.append(self.mb_help_about)
        
        self.mb_help.set_submenu(self.mb_help_menu)
        self.mb.append(self.mb_help)
    
    def _create_toolbar(self):
        self.tb = gtk.Toolbar()
        
        self.tb_refresh_icon = gtk.Image()
        self.tb_refresh_icon.set_from_file(icon_path("refresh.png"))
        self.tb_refresh = gtk.ToolButton(self.tb_refresh_icon, _i18n("Refresh"))
        self.tb_refresh.connect('clicked', self.signal.on_menuitem_view_refresh_activate)
        self.tb.add(self.tb_refresh)
        
        self.tb_diff_icon = gtk.Image()
        self.tb_diff_icon.set_from_file(icon_path("diff.png"))
        self.tb_diff = gtk.ToolButton(self.tb_diff_icon, _i18n("Diff"))
        self.tb_diff.connect('clicked', self.signal.on_menuitem_stats_diff_activate)
        self.tb.add(self.tb_diff)
        
        self.tb_log_icon = gtk.Image()
        self.tb_log_icon.set_from_file(icon_path("log.png"))
        self.tb_log = gtk.ToolButton(self.tb_log_icon, _i18n("Log"))
        self.tb_log.connect('clicked', self.signal.on_menuitem_stats_log_activate)
        self.tb.add(self.tb_log)
        
        self.tb.add(gtk.SeparatorToolItem())
        
        self.tb_commit_icon = gtk.Image()
        self.tb_commit_icon.set_from_file(icon_path("commit.png"))
        self.tb_commit = gtk.ToolButton(self.tb_commit_icon, _i18n("Commit"))
        self.tb_commit.connect('clicked', self.signal.on_menuitem_branch_commit_activate)
        self.tb.add(self.tb_commit)
        
        self.tb.add(gtk.SeparatorToolItem())
        
        self.tb_pull_icon = gtk.Image()
        self.tb_pull_icon.set_from_file(icon_path("pull.png"))
        self.tb_pull = gtk.ToolButton(self.tb_pull_icon, _i18n("Pull"))
        self.tb_pull.connect('clicked', self.signal.on_menuitem_branch_pull_activate)
        self.tb.add(self.tb_pull)
        
        self.tb_push_icon = gtk.Image()
        self.tb_push_icon.set_from_file(icon_path("push.png"))
        self.tb_push = gtk.ToolButton(self.tb_push_icon, _i18n("Push"))
        self.tb_push.connect('clicked', self.signal.on_menuitem_branch_push_activate)
        self.tb.add(self.tb_push)
        
        self.tb_update_icon = gtk.Image()
        self.tb_update_icon.set_from_file(icon_path("pull.png"))
        self.tb_update = gtk.ToolButton(self.tb_update_icon, _i18n("Update"))
        self.tb_update.connect('clicked', self.signal.on_menuitem_branch_update_activate)
        self.tb.add(self.tb_update)
    
    def _create_locationbar(self):
        """ Creates the location bar, including the history widgets """
        self.locationbar = gtk.HBox()
        
        self.button_location_up = gtk.Button()
        self.button_location_up.set_relief(gtk.RELIEF_NONE)
        image_location_up = gtk.Image()
        image_location_up.set_from_stock(gtk.STOCK_GO_UP, gtk.ICON_SIZE_BUTTON)
        self.button_location_up.add(image_location_up)
        self.button_location_up.connect("clicked", self.signal.on_button_location_up_clicked)
        self.locationbar.pack_start(self.button_location_up, False, False, 0)
        
        self.entry_location = gtk.Entry()
        self.entry_location.connect("key-press-event", self.signal.on_entry_location_key_press_event)
        self.locationbar.pack_start(self.entry_location, True, True, 0)
        
        self.image_location_error = gtk.Image()
        self.image_location_error.set_from_stock(gtk.STOCK_DIALOG_ERROR, gtk.ICON_SIZE_BUTTON)
        self.locationbar.pack_start(self.image_location_error, False, False, 0)
        
        self.button_location_jump = gtk.Button(stock=gtk.STOCK_JUMP_TO)
        self.button_location_jump.set_relief(gtk.RELIEF_NONE)
        self.button_location_jump.connect("clicked", self.signal.on_button_location_jump_clicked)
        self.locationbar.pack_start(self.button_location_jump, False, False, 0)
        
        self.locationbar.pack_start(gtk.VSeparator(), False, False, 0)
        
        self.checkbutton_history = gtk.CheckButton(_i18n("H_istory Mode"))
        self.checkbutton_history.connect("toggled", self.signal.on_checkbutton_history_toggled)
        self.locationbar.pack_start(self.checkbutton_history, False, False, 0)
        
        self.entry_history_revno = gtk.Entry()
        self.entry_history_revno.set_property("width-request", 75)
        self.entry_history_revno.set_sensitive(False)
        self.entry_history_revno.connect("key-press-event", self.signal.on_entry_history_revno_key_press_event)
        self.locationbar.pack_start(self.entry_history_revno, False, False, 0)
        
        self.button_history_browse = gtk.Button()
        self.button_history_browse.set_sensitive(False)
        self.image_history_browse = gtk.Image()
        self.image_history_browse.set_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_BUTTON)
        self.button_history_browse.add(self.image_history_browse)
        self.button_history_browse.connect("clicked", self.signal.on_button_history_browse_clicked)
        self.locationbar.pack_start(self.button_history_browse, False, False, 0)
    
    def _create_bookmarklist(self):
        """ Creates the bookmark list (a ListStore in a TreeView in a ScrolledWindow)"""
        self.scrolledwindow_left = gtk.ScrolledWindow()
        self.scrolledwindow_left.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        
        self.treeview_left = gtk.TreeView()
        self.treeview_left.set_headers_visible(False)
        self.treeview_left.connect("button-press-event", self.signal.on_treeview_left_button_press_event)
        self.treeview_left.connect("button-release-event", self.signal.on_treeview_left_button_release_event)
        self.treeview_left.connect("row-activated", self.signal.on_treeview_left_row_activated)
        self.scrolledwindow_left.add(self.treeview_left)

        # Move olive/__init__.py _load_left List creation here
            
    def _create_filelist(self):
        """ Creates the file list (a ListStore in a TreeView in a ScrolledWindow)"""
        self.scrolledwindow_right = gtk.ScrolledWindow()
        self.scrolledwindow_right.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        
        self.treeview_right = gtk.TreeView()
        self.treeview_right.connect("button-press-event", self.signal.on_treeview_right_button_press_event)
        self.treeview_right.connect("row-activated", self.signal.on_treeview_right_row_activated)
        self.scrolledwindow_right.add(self.treeview_right)
        
        # Model: [ icon, dir, name, status text, status, size (int), size (human), mtime (int), mtime (local), fileid ]
        self.filelist = gtk.ListStore(gobject.TYPE_STRING,
                                      gobject.TYPE_BOOLEAN,
                                      gobject.TYPE_STRING,
                                      gobject.TYPE_STRING,
                                      gobject.TYPE_STRING,
                                      gobject.TYPE_STRING,
                                      gobject.TYPE_STRING,
                                      gobject.TYPE_INT,
                                      gobject.TYPE_STRING,
                                      gobject.TYPE_STRING)
        self.treeview_right.set_model(self.filelist)
        
        # Set up the cells
        cellpb = gtk.CellRendererPixbuf()
        cell = gtk.CellRendererText()
        
        self.col_filename = gtk.TreeViewColumn(_i18n('Filename'))
        self.col_filename.pack_start(cellpb, False)
        self.col_filename.pack_start(cell, True)
        self.col_filename.set_attributes(cellpb, stock_id=0)
        self.col_filename.add_attribute(cell, 'text', 2)
        self.col_filename.set_resizable(True)
        self.treeview_right.append_column(self.col_filename)
        
        self.col_status = gtk.TreeViewColumn(_i18n('Status'))
        self.col_status.pack_start(cell, True)
        self.col_status.add_attribute(cell, 'text', 3)
        self.col_status.set_resizable(True)
        self.treeview_right.append_column(self.col_status)
        
        self.col_size = gtk.TreeViewColumn(_i18n('Size'))
        self.col_size.pack_start(cell, True)
        self.col_size.add_attribute(cell, 'text', 6)
        self.col_size.set_resizable(True)
        self.treeview_right.append_column(self.col_size)
        
        self.col_mtime = gtk.TreeViewColumn(_i18n('Last modified'))
        self.col_mtime.pack_start(cell, True)
        self.col_mtime.add_attribute(cell, 'text', 8)
        self.col_mtime.set_resizable(True)
        self.treeview_right.append_column(self.col_mtime)
        
        # Set up the properties of the TreeView
        self.treeview_right.set_headers_visible(True)
        self.treeview_right.set_headers_clickable(True)
        self.treeview_right.set_search_column(1)
        
        # Set up sorting
        self.filelist.set_sort_func(13, self.signal._sort_filelist_callback, None)
        self.filelist.set_sort_column_id(13, gtk.SORT_ASCENDING)
        self.col_filename.set_sort_column_id(13)
        self.col_status.set_sort_column_id(3)
        self.col_size.set_sort_column_id(5)
        self.col_mtime.set_sort_column_id(7)
    
    def set_view_to_localbranch(self, notbranch=False):
        """ Change the sensitivity of gui items to reflect the fact that the path is a branch or not"""
        self.mb_branch_initialize.set_sensitive(notbranch)
        self.mb_branch_get.set_sensitive(notbranch)
        self.mb_branch_checkout.set_sensitive(notbranch)
        self.mb_branch_pull.set_sensitive(not notbranch)
        self.mb_branch_push.set_sensitive(not notbranch)
        self.mb_branch_update.set_sensitive(not notbranch)
        self.mb_branch_revert.set_sensitive(not notbranch)
        self.mb_branch_merge.set_sensitive(not notbranch)
        self.mb_branch_commit.set_sensitive(not notbranch)
        self.mb_branch_tags.set_sensitive(not notbranch)
        self.mb_branch_status.set_sensitive(not notbranch)
        self.mb_branch_missingrevisions.set_sensitive(not notbranch)
        self.mb_branch_conflicts.set_sensitive(not notbranch)
        self.mb_statistics.set_sensitive(not notbranch)
        self.mb_statistics_differences.set_sensitive(not notbranch)
        self.mb_file_add.set_sensitive(not notbranch)
        self.mb_file_remove.set_sensitive(not notbranch)
        self.mb_file_mkdir.set_sensitive(not notbranch)
        self.mb_file_rename.set_sensitive(not notbranch)
        self.mb_file_move.set_sensitive(not notbranch)
        self.mb_file_annotate.set_sensitive(not notbranch)
        self.tb_diff.set_sensitive(not notbranch)
        self.tb_log.set_sensitive(not notbranch)
        self.tb_commit.set_sensitive(not notbranch)
        self.tb_pull.set_sensitive(not notbranch)
        self.tb_push.set_sensitive(not notbranch)
        self.tb_update.set_sensitive(not notbranch)
    
    def set_view_to_remotebranch(self):
        """ Change the sensitivity of gui items to reflect the fact that the branch is remote"""
        self.mb_file_add.set_sensitive(False)
        self.mb_file_remove.set_sensitive(False)
        self.mb_file_mkdir.set_sensitive(False)
        self.mb_file_rename.set_sensitive(False)
        self.mb_file_move.set_sensitive(False)
        self.mb_file_annotate.set_sensitive(False)
        self.mb_branch_initialize.set_sensitive(False)
        self.mb_branch_get.set_sensitive(True)
        self.mb_branch_checkout.set_sensitive(True)
        self.mb_branch_pull.set_sensitive(False)
        self.mb_branch_push.set_sensitive(False)
        self.mb_branch_update.set_sensitive(False)
        self.mb_branch_revert.set_sensitive(False)
        self.mb_branch_merge.set_sensitive(False)
        self.mb_branch_commit.set_sensitive(False)
        self.mb_branch_tags.set_sensitive(True)
        self.mb_branch_status.set_sensitive(False)
        self.mb_branch_missingrevisions.set_sensitive(False)
        self.mb_branch_conflicts.set_sensitive(False)
        self.mb_statistics.set_sensitive(True)
        self.mb_statistics_differences.set_sensitive(False)
        self.tb_diff.set_sensitive(False)
        self.tb_log.set_sensitive(True)
        self.tb_commit.set_sensitive(False)
        self.tb_pull.set_sensitive(False)
        self.tb_push.set_sensitive(False)
        self.tb_update.set_sensitive(False)
