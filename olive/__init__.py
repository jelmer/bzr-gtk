# Copyright (C) 2006 by Szilveszter Farkas (Phanatic) <szilveszter.farkas@gmail.com>
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
import sys

# gettext support
import gettext
gettext.install('olive-gtk')

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

import gtk
import gtk.gdk
import gtk.glade

from bzrlib.branch import Branch
import bzrlib.errors as errors
from bzrlib.workingtree import WorkingTree

# Olive GTK UI version
__version__ = '0.11.0'

# Load the glade file
if sys.platform == 'win32':
    gladefile = os.path.dirname(sys.executable) + "/share/olive/olive.glade"
else:
    gladefile = "/usr/share/olive/olive.glade"

if not os.path.exists(gladefile):
    # Load from sources directory if not installed
    dir_ = os.path.split(os.path.dirname(__file__))[0]
    gladefile = os.path.join(dir_, "olive.glade")
    # Check again
    if not os.path.exists(gladefile):
        # Fail
        print _('Glade file cannot be found.')
        sys.exit(1)

from dialog import error_dialog, info_dialog

# import this classes only once
try:
    from bzrlib.plugins.gtk.viz.diffwin import DiffWindow
    from bzrlib.plugins.gtk.viz.branchwin import BranchWindow
except ImportError:
    # olive+bzr-gtk not installed. try to import from sources
    path = os.path.dirname(os.path.dirname(__file__))
    if path not in sys.path:
        sys.path.append(path)
    from viz.diffwin import DiffWindow
    from viz.branchwin import BranchWindow


class OliveGtk:
    """ The main Olive GTK frontend class. This is called when launching the
    program. """
    
    def __init__(self):
        self.toplevel = gtk.glade.XML(gladefile, 'window_main', 'olive-gtk')
        
        self.window = self.toplevel.get_widget('window_main')
        
        self.pref = OlivePreferences()
        
        self.path = None

        # Initialize the statusbar
        self.statusbar = self.toplevel.get_widget('statusbar')
        self.context_id = self.statusbar.get_context_id('olive')
        
        # Get the main window
        self.window_main = self.toplevel.get_widget('window_main')
        # Get the HPaned
        self.hpaned_main = self.toplevel.get_widget('hpaned_main')
        # Get the TreeViews
        self.treeview_left = self.toplevel.get_widget('treeview_left')
        self.treeview_right = self.toplevel.get_widget('treeview_right')
        # Get some important menu items
        self.menuitem_add_files = self.toplevel.get_widget('menuitem_add_files')
        self.menuitem_remove_files = self.toplevel.get_widget('menuitem_remove_file')
        self.menuitem_file_make_directory = self.toplevel.get_widget('menuitem_file_make_directory')
        self.menuitem_file_rename = self.toplevel.get_widget('menuitem_file_rename')
        self.menuitem_file_move = self.toplevel.get_widget('menuitem_file_move')
        self.menuitem_view_show_hidden_files = self.toplevel.get_widget('menuitem_view_show_hidden_files')
        self.menuitem_branch = self.toplevel.get_widget('menuitem_branch')
        self.menuitem_branch_init = self.toplevel.get_widget('menuitem_branch_initialize')
        self.menuitem_branch_get = self.toplevel.get_widget('menuitem_branch_get')
        self.menuitem_branch_checkout = self.toplevel.get_widget('menuitem_branch_checkout')
        self.menuitem_branch_pull = self.toplevel.get_widget('menuitem_branch_pull')
        self.menuitem_branch_push = self.toplevel.get_widget('menuitem_branch_push')
        self.menuitem_branch_merge = self.toplevel.get_widget('menuitem_branch_merge')
        self.menuitem_branch_commit = self.toplevel.get_widget('menuitem_branch_commit')
        self.menuitem_branch_status = self.toplevel.get_widget('menuitem_branch_status')
        self.menuitem_branch_missing = self.toplevel.get_widget('menuitem_branch_missing_revisions')
        self.menuitem_stats = self.toplevel.get_widget('menuitem_stats')
        self.menuitem_stats_diff = self.toplevel.get_widget('menuitem_stats_diff')
        self.menuitem_stats_log = self.toplevel.get_widget('menuitem_stats_log')
        # Get some toolbuttons
        #self.menutoolbutton_diff = self.toplevel.get_widget('menutoolbutton_diff')
        self.toolbutton_diff = self.toplevel.get_widget('toolbutton_diff')
        self.toolbutton_log = self.toplevel.get_widget('toolbutton_log')
        self.toolbutton_commit = self.toplevel.get_widget('toolbutton_commit')
        self.toolbutton_pull = self.toplevel.get_widget('toolbutton_pull')
        self.toolbutton_push = self.toplevel.get_widget('toolbutton_push')
        # Get the drive selector
        self.combobox_drive = gtk.combo_box_new_text()
        self.combobox_drive.connect("changed", self._refresh_drives)
        
        self.vbox_main_right = self.toplevel.get_widget('vbox_main_right')
 
        
        # Dictionary for signal_autoconnect
        dic = { "on_window_main_destroy": gtk.main_quit,
                "on_window_main_delete_event": self.on_window_main_delete_event,
                "on_quit_activate": self.on_window_main_delete_event,
                "on_about_activate": self.on_about_activate,
                "on_menuitem_add_files_activate": self.on_menuitem_add_files_activate,
                "on_menuitem_remove_file_activate": self.on_menuitem_remove_file_activate,
                "on_menuitem_file_make_directory_activate": self.on_menuitem_file_make_directory_activate,
                "on_menuitem_file_move_activate": self.on_menuitem_file_move_activate,
                "on_menuitem_file_rename_activate": self.on_menuitem_file_rename_activate,
                "on_menuitem_view_show_hidden_files_activate": self.on_menuitem_view_show_hidden_files_activate,
                "on_menuitem_view_refresh_activate": self.on_menuitem_view_refresh_activate,
                "on_menuitem_branch_initialize_activate": self.on_menuitem_branch_initialize_activate,
                "on_menuitem_branch_get_activate": self.on_menuitem_branch_get_activate,
                "on_menuitem_branch_checkout_activate": self.on_menuitem_branch_checkout_activate,
                "on_menuitem_branch_merge_activate": self.on_menuitem_branch_merge_activate,
                "on_menuitem_branch_commit_activate": self.on_menuitem_branch_commit_activate,
                "on_menuitem_branch_push_activate": self.on_menuitem_branch_push_activate,
                "on_menuitem_branch_pull_activate": self.on_menuitem_branch_pull_activate,
                "on_menuitem_branch_status_activate": self.on_menuitem_branch_status_activate,
                "on_menuitem_branch_missing_revisions_activate": self.on_menuitem_branch_missing_revisions_activate,
                "on_menuitem_stats_diff_activate": self.on_menuitem_stats_diff_activate,
                "on_menuitem_stats_log_activate": self.on_menuitem_stats_log_activate,
                "on_menuitem_stats_infos_activate": self.on_menuitem_stats_infos_activate,
                "on_toolbutton_refresh_clicked": self.on_menuitem_view_refresh_activate,
                "on_toolbutton_log_clicked": self.on_menuitem_stats_log_activate,
                #"on_menutoolbutton_diff_clicked": self.on_menuitem_stats_diff_activate,
                "on_toolbutton_diff_clicked": self.on_menuitem_stats_diff_activate,
                "on_toolbutton_commit_clicked": self.on_menuitem_branch_commit_activate,
                "on_toolbutton_pull_clicked": self.on_menuitem_branch_pull_activate,
                "on_toolbutton_push_clicked": self.on_menuitem_branch_push_activate,
                "on_treeview_right_button_press_event": self.on_treeview_right_button_press_event,
                "on_treeview_right_row_activated": self.on_treeview_right_row_activated,
                "on_treeview_left_button_press_event": self.on_treeview_left_button_press_event,
                "on_treeview_left_row_activated": self.on_treeview_left_row_activated }
        
        # Connect the signals to the handlers
        self.toplevel.signal_autoconnect(dic)
        
        # Apply window size and position
        width = self.pref.get_preference('window_width', 'int')
        height = self.pref.get_preference('window_height', 'int')
        self.window.resize(width, height)
        x = self.pref.get_preference('window_x', 'int')
        y = self.pref.get_preference('window_y', 'int')
        self.window.move(x, y)
        # Apply paned position
        pos = self.pref.get_preference('paned_position', 'int')
        self.hpaned_main.set_position(pos)
        
        # Apply menu to the toolbutton
        #menubutton = self.toplevel.get_widget('menutoolbutton_diff')
        #menubutton.set_menu(handler.menu.toolbar_diff)
        
        # Now we can show the window
        self.window.show()
        
        # Show drive selector if under Win32
        if sys.platform == 'win32':
            self.vbox_main_right.pack_start(self.combobox_drive, False, True, 0)
            self.vbox_main_right.reorder_child(self.combobox_drive, 0)
            self.combobox_drive.show()
            self.gen_hard_selector()
        
        self._load_left()

        # Apply menu state
        self.menuitem_view_show_hidden_files.set_active(self.pref.get_preference('dotted_files', 'bool'))

        self.set_path(os.getcwd())
        self._load_right()

    def set_path(self, path):
        self.path = path
        self.notbranch = False
        
        try:
            self.wt, self.wtpath = WorkingTree.open_containing(self.path)
        except (errors.NotBranchError, errors.NoWorkingTree):
            self.notbranch = True
        
        self.statusbar.push(self.context_id, path)

    def get_path(self):
        return self.path
   
    def on_about_activate(self, widget):
        from dialog import about
        about()
        
    def on_menuitem_add_files_activate(self, widget):
        """ Add file(s)... menu handler. """
        from add import OliveAdd
        add = OliveAdd(self.wt, self.wtpath, self.get_selected_right())
        add.display()
    
    def on_menuitem_branch_get_activate(self, widget):
        """ Branch/Get... menu handler. """
        from branch import BranchDialog
        branch = BranchDialog(self.get_path())
        branch.display()
    
    def on_menuitem_branch_checkout_activate(self, widget):
        """ Branch/Checkout... menu handler. """
        from checkout import OliveCheckout
        checkout = OliveCheckout(self.get_path())
        checkout.display()
    
    def on_menuitem_branch_commit_activate(self, widget):
        """ Branch/Commit... menu handler. """
        from commit import CommitDialog
        commit = CommitDialog(self.wt, self.wtpath)
        commit.display()
    
    def on_menuitem_branch_merge_activate(self, widget):
        """ Branch/Merge... menu handler. """
        from merge import MergeDialog
        merge = MergeDialog(self.wt, self.wtpath)
        merge.display()

    def on_menuitem_branch_missing_revisions_activate(self, widget):
        """ Branch/Missing revisions menu handler. """
        local_branch = self.wt.branch
        
        other_branch = local_branch.get_parent()
        if other_branch is None:
            error_dialog(_('Parent location is unknown'),
                         _('Cannot determine missing revisions if no parent location is known.'))
            return
        
        remote_branch = Branch.open(other_branch)
        
        if remote_branch.base == local_branch.base:
            remote_branch = local_branch

        ret = len(local_branch.missing_revisions(remote_branch))

        if ret > 0:
            info_dialog(_('There are missing revisions'),
                        _('%d revision(s) missing.') % ret)
        else:
            info_dialog(_('Local branch up to date'),
                        _('There are no missing revisions.'))

    def on_menuitem_branch_pull_activate(self, widget):
        """ Branch/Pull menu handler. """
        branch_to = self.wt.branch

        location = branch_to.get_parent()
        if location is None:
            error_dialog(_('Parent location is unknown'),
                                     _('Pulling is not possible until there is a parent location.'))
            return

        try:
            branch_from = Branch.open(location)
        except errors.NotBranchError:
            error_dialog(_('Directory is not a branch'),
                                     _('You can perform this action only in a branch.'))

        if branch_to.get_parent() is None:
            branch_to.set_parent(branch_from.base)

        #old_rh = branch_to.revision_history()
        #if tree_to is not None:
        #    tree_to.pull(branch_from)
        #else:
        #    branch_to.pull(branch_from)
        ret = branch_to.pull(branch_from)
        
        info_dialog(_('Pull successful'), _('%d revision(s) pulled.') % ret)
    
    def on_menuitem_branch_push_activate(self, widget):
        """ Branch/Push... menu handler. """
        from push import OlivePush
        push = OlivePush(self.wt.branch)
        push.display()
    
    def on_menuitem_branch_status_activate(self, widget):
        """ Branch/Status... menu handler. """
        from status import OliveStatus
        status = OliveStatus(self.wt, self.wtpath)
        status.display()
    
    def on_menuitem_branch_initialize_activate(self, widget):
        """ Initialize current directory. """
        import bzrlib.bzrdir as bzrdir
        
        try:
            if not os.path.exists(self.path):
                os.mkdir(self.path)
     
            try:
                existing_bzrdir = bzrdir.BzrDir.open(self.path)
            except errors.NotBranchError:
                bzrdir.BzrDir.create_branch_convenience(self.path)
            else:
                if existing_bzrdir.has_branch():
                    if existing_bzrdir.has_workingtree():
                        raise errors.AlreadyBranchError(self.path)
                    else:
                        raise errors.BranchExistsWithoutWorkingTree(self.path)
                else:
                    existing_bzrdir.create_branch()
                    existing_bzrdir.create_workingtree()
        except errors.AlreadyBranchError, errmsg:
            error_dialog(_('Directory is already a branch'),
                         _('The current directory (%s) is already a branch.\nYou can start using it, or initialize another directory.') % errmsg)
        except errors.BranchExistsWithoutWorkingTree, errmsg:
            error_dialog(_('Branch without a working tree'),
                         _('The current directory (%s)\nis a branch without a working tree.') % errmsg)
        else:
            info_dialog(_('Initialize successful'),
                        _('Directory successfully initialized.'))
            self.refresh_right()
        
    def on_menuitem_file_make_directory_activate(self, widget):
        """ File/Make directory... menu handler. """
        from mkdir import OliveMkdir
        mkdir = OliveMkdir(self.wt, self.wtpath)
        mkdir.display()
    
    def on_menuitem_file_move_activate(self, widget):
        """ File/Move... menu handler. """
        from move import OliveMove
        move = OliveMove(self.wt, self.wtpath, self.get_selected_right())
        move.display()
    
    def on_menuitem_file_rename_activate(self, widget):
        """ File/Rename... menu handler. """
        from rename import OliveRename
        rename = OliveRename(self.wt, self.wtpath, self.get_selected_right())
        rename.display()

    def on_menuitem_remove_file_activate(self, widget):
        """ Remove (unversion) selected file. """
        from remove import OliveRemove
        remove = OliveRemove(self.wt, self.wtpath, self.get_selected_right())
        remove.display()
    
    def on_menuitem_stats_diff_activate(self, widget):
        """ Statistics/Differences... menu handler. """
        window = DiffWindow()
        parent_tree = self.wt.branch.repository.revision_tree(self.wt.branch.last_revision())
        window.set_diff(self.wt.branch.nick, self.wt, parent_tree)
        window.show()
    
    def on_menuitem_stats_infos_activate(self, widget):
        """ Statistics/Informations... menu handler. """
        from info import OliveInfo
        info = OliveInfo(self.wt)
        info.display()
    
    def on_menuitem_stats_log_activate(self, widget):
        """ Statistics/Log... menu handler. """
        window = BranchWindow()
        window.set_branch(self.wt.branch, self.wt.branch.last_revision(), None)
        window.show()
    
    def on_menuitem_view_refresh_activate(self, widget):
        """ View/Refresh menu handler. """
        # Refresh the left pane
        self.refresh_left()
        # Refresh the right pane
        self.refresh_right()
   
    def on_menuitem_view_show_hidden_files_activate(self, widget):
        """ View/Show hidden files menu handler. """
        self.pref.set_preference('dotted_files', widget.get_active())
        if self.path is not None:
            self.refresh_right()

    def on_treeview_left_button_press_event(self, widget, event):
        """ Occurs when somebody right-clicks in the bookmark list. """
        if event.button == 3:
            # Don't show context with nothing selected
            if self.get_selected_left() == None:
                return

            # Create a menu
            from menu import OliveMenu
            menu = OliveMenu(self.get_path(), self.get_selected_left())
            
            menu.left_context_menu().popup(None, None, None, 0,
                                           event.time)

    def on_treeview_left_row_activated(self, treeview, path, view_column):
        """ Occurs when somebody double-clicks or enters an item in the
        bookmark list. """

        newdir = self.get_selected_left()
        if newdir == None:
            return

        self.set_path(newdir)
        self.refresh_right()

    def on_treeview_right_button_press_event(self, widget, event):
        """ Occurs when somebody right-clicks in the file list. """
        if event.button == 3:
            # Create a menu
            from menu import OliveMenu
            menu = OliveMenu(self.get_path(), self.get_selected_right())
            # get the menu items
            m_add = menu.ui.get_widget('/context_right/add')
            m_remove = menu.ui.get_widget('/context_right/remove')
            m_commit = menu.ui.get_widget('/context_right/commit')
            m_diff = menu.ui.get_widget('/context_right/diff')
            # check if we're in a branch
            try:
                from bzrlib.branch import Branch
                Branch.open_containing(self.get_path())
                m_add.set_sensitive(True)
                m_remove.set_sensitive(True)
                m_commit.set_sensitive(True)
                m_diff.set_sensitive(True)
            except errors.NotBranchError:
                m_add.set_sensitive(False)
                m_remove.set_sensitive(False)
                m_commit.set_sensitive(False)
                m_diff.set_sensitive(False)

            menu.right_context_menu().popup(None, None, None, 0,
                                            event.time)
        
    def on_treeview_right_row_activated(self, treeview, path, view_column):
        """ Occurs when somebody double-clicks or enters an item in the
        file list. """
        from launch import launch
        
        newdir = self.get_selected_right()
        
        if newdir == '..':
            self.set_path(os.path.split(self.get_path())[0])
        else:
            fullpath = os.path.join(self.get_path(), newdir)
            if os.path.isdir(fullpath):
                # selected item is an existant directory
                self.set_path(fullpath)
            else:
                launch(fullpath) 
        
        self.refresh_right()
    
    def on_window_main_delete_event(self, widget, event=None):
        """ Do some stuff before exiting. """
        width, height = self.window_main.get_size()
        self.pref.set_preference('window_width', width)
        self.pref.set_preference('window_height', height)
        x, y = self.window_main.get_position()
        self.pref.set_preference('window_x', x)
        self.pref.set_preference('window_y', y)
        self.pref.set_preference('paned_position',
                                 self.hpaned_main.get_position())
        
        self.pref.write()
        self.window_main.destroy()
        
    def _load_left(self):
        """ Load data into the left panel. (Bookmarks) """
        # Create TreeStore
        treestore = gtk.TreeStore(str, str)
        
        # Get bookmarks
        bookmarks = self.pref.get_bookmarks()
        
        # Add them to the TreeStore
        titer = treestore.append(None, [_('Bookmarks'), None])
        for item in bookmarks:
            title = self.pref.get_bookmark_title(item)
            treestore.append(titer, [title, item])
        
        # Create the column and add it to the TreeView
        self.treeview_left.set_model(treestore)
        tvcolumn_bookmark = gtk.TreeViewColumn(_('Bookmark'))
        self.treeview_left.append_column(tvcolumn_bookmark)
        
        # Set up the cells
        cell = gtk.CellRendererText()
        tvcolumn_bookmark.pack_start(cell, True)
        tvcolumn_bookmark.add_attribute(cell, 'text', 0)
        
        # Expand the tree
        self.treeview_left.expand_all()

    def _add_updir_to_dirlist(self, dirlist, curdir):
        """Add .. to the top of directories list if we not in root directory

        @param  dirlist:    list of directories (modified in place)
        @param  curdir:     current directory
        @return:            nothing
        """
        if curdir is None:
            curdir = self.path

        if sys.platform == 'win32':
            drive, tail = os.path.splitdrive(curdir)
            if tail in ('', '/', '\\'):
                return
        else:
            if curdir == '/':
                return

        # insert always as first element
        dirlist.insert(0, '..')

    def _load_right(self):
        """ Load data into the right panel. (Filelist) """
        # Create ListStore
        liststore = gtk.ListStore(str, str, str)
        
        dirs = []
        files = []
        
        # Fill the appropriate lists
        dotted_files = self.pref.get_preference('dotted_files', 'bool')
        for item in os.listdir(self.path):
            if not dotted_files and item[0] == '.':
                continue
            if os.path.isdir(self.path + os.sep + item):
                dirs.append(item)
            else:
                files.append(item)
            
        # Sort'em
        dirs.sort()
        files.sort()

        # add updir link to dirs
        self._add_updir_to_dirlist(dirs, self.path)
        
        if not self.notbranch:
            branch = self.wt.branch
            tree2 = self.wt.branch.repository.revision_tree(branch.last_revision())
        
            delta = self.wt.changes_from(tree2, want_unchanged=True)
        
        # Add'em to the ListStore
        for item in dirs:    
            liststore.append([gtk.STOCK_DIRECTORY, item, ''])
        for item in files:
            status = 'unknown'
            if not self.notbranch:
                filename = self.wt.relpath(self.path + os.sep + item)
                
                for rpath, rpathnew, id, kind, text_modified, meta_modified in delta.renamed:
                    if rpathnew == filename:
                        status = 'renamed'
                for rpath, id, kind in delta.added:
                    if rpath == filename:
                        status = 'added'
                for rpath, id, kind in delta.removed:
                    if rpath == filename:
                        status = 'removed'
                for rpath, id, kind, text_modified, meta_modified in delta.modified:
                    if rpath == filename:
                        status = 'modified'
                for rpath, id, kind in delta.unchanged:
                    if rpath == filename:
                        status = 'unchanged'
            
            #try:
            #    status = fileops.status(path + os.sep + item)
            #except errors.PermissionDenied:
            #    continue
            
            if status == 'renamed':
                st = _('renamed')
            elif status == 'removed':
                st = _('removed')
            elif status == 'added':
                st = _('added')
            elif status == 'modified':
                st = _('modified')
            elif status == 'unchanged':
                st = _('unchanged')
            else:
                st = _('unknown')
            liststore.append([gtk.STOCK_FILE, item, st])
        
        # Create the columns and add them to the TreeView
        self.treeview_right.set_model(liststore)
        tvcolumn_filename = gtk.TreeViewColumn(_('Filename'))
        tvcolumn_status = gtk.TreeViewColumn(_('Status'))
        self.treeview_right.append_column(tvcolumn_filename)
        self.treeview_right.append_column(tvcolumn_status)
        
        # Set up the cells
        cellpb = gtk.CellRendererPixbuf()
        cell = gtk.CellRendererText()
        tvcolumn_filename.pack_start(cellpb, False)
        tvcolumn_filename.pack_start(cell, True)
        tvcolumn_filename.set_attributes(cellpb, stock_id=0)
        tvcolumn_filename.add_attribute(cell, 'text', 1)
        tvcolumn_status.pack_start(cell, True)
        tvcolumn_status.add_attribute(cell, 'text', 2)
        
        # Set sensitivity
        self.set_sensitivity()
        
    def get_selected_right(self):
        """ Get the selected filename. """
        treeselection = self.treeview_right.get_selection()
        (model, iter) = treeselection.get_selected()
        
        if iter is None:
            return None
        else:
            return model.get_value(iter, 1)
    
    def get_selected_left(self):
        """ Get the selected bookmark. """
        treeselection = self.treeview_left.get_selection()
        (model, iter) = treeselection.get_selected()
        
        if iter is None:
            return None
        else:
            return model.get_value(iter, 1)

    def set_statusbar(self, message):
        """ Set the statusbar message. """
        self.statusbar.push(self.context_id, message)
    
    def clear_statusbar(self):
        """ Clean the last message from the statusbar. """
        self.statusbar.pop(self.context_id)
    
    def set_sensitivity(self):
        """ Set menu and toolbar sensitivity. """
        self.menuitem_branch_init.set_sensitive(self.notbranch)
        self.menuitem_branch_get.set_sensitive(self.notbranch)
        self.menuitem_branch_checkout.set_sensitive(self.notbranch)
        self.menuitem_branch_pull.set_sensitive(not self.notbranch)
        self.menuitem_branch_push.set_sensitive(not self.notbranch)
        self.menuitem_branch_merge.set_sensitive(not self.notbranch)
        self.menuitem_branch_commit.set_sensitive(not self.notbranch)
        self.menuitem_branch_status.set_sensitive(not self.notbranch)
        self.menuitem_branch_missing.set_sensitive(not self.notbranch)
        self.menuitem_stats.set_sensitive(not self.notbranch)
        self.menuitem_add_files.set_sensitive(not self.notbranch)
        self.menuitem_remove_files.set_sensitive(not self.notbranch)
        self.menuitem_file_make_directory.set_sensitive(not self.notbranch)
        self.menuitem_file_rename.set_sensitive(not self.notbranch)
        self.menuitem_file_move.set_sensitive(not self.notbranch)
        #self.menutoolbutton_diff.set_sensitive(True)
        self.toolbutton_diff.set_sensitive(not self.notbranch)
        self.toolbutton_log.set_sensitive(not self.notbranch)
        self.toolbutton_commit.set_sensitive(not self.notbranch)
        self.toolbutton_pull.set_sensitive(not self.notbranch)
        self.toolbutton_push.set_sensitive(not self.notbranch)
    
    def refresh_left(self):
        """ Refresh the bookmark list. """
        
        # Get TreeStore and clear it
        treestore = self.treeview_left.get_model()
        treestore.clear()

        # Re-read preferences
        self.pref.read()

        # Get bookmarks
        bookmarks = self.pref.get_bookmarks()

        # Add them to the TreeStore
        titer = treestore.append(None, [_('Bookmarks'), None])
        for item in bookmarks:
            title = self.pref.get_bookmark_title(item)
            treestore.append(titer, [title, item])

        # Add the TreeStore to the TreeView
        self.treeview_left.set_model(treestore)

        # Expand the tree
        self.treeview_left.expand_all()

    def refresh_right(self, path=None):
        """ Refresh the file list. """
        from bzrlib.workingtree import WorkingTree

        if path is None:
            path = self.get_path()

        # A workaround for double-clicking Bookmarks
        if not os.path.exists(path):
            return

        # Get ListStore and clear it
        liststore = self.treeview_right.get_model()
        liststore.clear()

        dirs = []
        files = []

        # Fill the appropriate lists
        dotted_files = self.pref.get_preference('dotted_files', 'bool')
        for item in os.listdir(path):
            if not dotted_files and item[0] == '.':
                continue
            if os.path.isdir(path + os.sep + item):
                dirs.append(item)
            else:
                files.append(item)

        # Sort'em
        dirs.sort()
        files.sort()

        # add updir link to dirs
        self._add_updir_to_dirlist(dirs, path)

        # Try to open the working tree
        notbranch = False
        try:
            tree1 = WorkingTree.open_containing(path)[0]
        except (errors.NotBranchError, errors.NoWorkingTree):
            notbranch = True
        except errors.PermissionDenied:
            print "DEBUG: permission denied."
        
        if not notbranch:
            branch = tree1.branch
            tree2 = tree1.branch.repository.revision_tree(branch.last_revision())
        
            delta = tree1.changes_from(tree2, want_unchanged=True)

        # Add'em to the ListStore
        for item in dirs:
            liststore.append([gtk.STOCK_DIRECTORY, item, ''])
        for item in files:
            status = 'unknown'
            if not notbranch:
                filename = tree1.relpath(path + os.sep + item)
                
                for rpath, rpathnew, id, kind, text_modified, meta_modified in delta.renamed:
                    if rpathnew == filename:
                        status = 'renamed'
                for rpath, id, kind in delta.added:
                    if rpath == filename:
                        status = 'added'                
                for rpath, id, kind in delta.removed:
                    if rpath == filename:
                        status = 'removed'
                for rpath, id, kind, text_modified, meta_modified in delta.modified:
                    if rpath == filename:
                        status = 'modified'
                for rpath, id, kind in delta.unchanged:
                    if rpath == filename:
                        status = 'unchanged'
            
            #try:
            #    status = fileops.status(path + os.sep + item)
            #except errors.PermissionDenied:
            #    continue

            if status == 'renamed':
                st = _('renamed')
            elif status == 'removed':
                st = _('removed')
            elif status == 'added':
                st = _('added')
            elif status == 'modified':
                st = _('modified')
            elif status == 'unchanged':
                st = _('unchanged')
            else:
                st = _('unknown')
            liststore.append([gtk.STOCK_FILE, item, st])

        # Add the ListStore to the TreeView
        self.treeview_right.set_model(liststore)
        
        # Set sensitivity
        self.set_sensitivity()

    def _harddisks(self):
        """ Returns hard drive letters under Win32. """
        try:
            import win32file
            import string
        except ImportError:
            if sys.platform == 'win32':
                print "pyWin32 modules needed to run Olive on Win32."
                sys.exit(1)
            else:
                pass
        
        driveletters = []
        for drive in string.ascii_uppercase:
            if win32file.GetDriveType(drive+':') == win32file.DRIVE_FIXED:
                driveletters.append(drive+':')
        return driveletters
    
    def gen_hard_selector(self):
        """ Generate the hard drive selector under Win32. """
        drives = self._harddisks()
        for drive in drives:
            self.combobox_drive.append_text(drive)
    
    def _refresh_drives(self, combobox):
        model = combobox.get_model()
        active = combobox.get_active()
        if active >= 0:
            drive = model[active][0]
            self.set_path(drive + '\\')
            self.refresh_right(drive + '\\')

import ConfigParser

class OlivePreferences:
    """ A class which handles Olive's preferences. """
    def __init__(self):
        """ Initialize the Preferences class. """
        # Some default options
        self.defaults = { 'strict_commit' : False,
                          'dotted_files'  : False,
                          'window_width'  : 700,
                          'window_height' : 400,
                          'window_x'      : 40,
                          'window_y'      : 40,
                          'paned_position': 200 }

        # Create a config parser object
        self.config = ConfigParser.RawConfigParser()
        
        # Load the configuration
        self.read()
        
    def _get_default(self, option):
        """ Get the default option for a preference. """
        try:
            ret = self.defaults[option]
        except KeyError:
            return None
        else:
            return ret

    def refresh(self):
        """ Refresh the configuration. """
        # First write out the changes
        self.write()
        # Then load the configuration again
        self.read()

    def read(self):
        """ Just read the configuration. """
        if sys.platform == 'win32':
            # Windows - no dotted files
            self.config.read([os.path.expanduser('~/olive.conf')])
        else:
            self.config.read([os.path.expanduser('~/.olive.conf')])
    
    def write(self):
        """ Write the configuration to the appropriate files. """
        if sys.platform == 'win32':
            # Windows - no dotted files
            fp = open(os.path.expanduser('~/olive.conf'), 'w')
            self.config.write(fp)
            fp.close()
        else:
            fp = open(os.path.expanduser('~/.olive.conf'), 'w')
            self.config.write(fp)
            fp.close()

    def get_bookmarks(self):
        """ Return the list of bookmarks. """
        bookmarks = self.config.sections()
        if self.config.has_section('preferences'):
            bookmarks.remove('preferences')
        return bookmarks

    def add_bookmark(self, path):
        """ Add bookmark. """
        try:
            self.config.add_section(path)
        except ConfigParser.DuplicateSectionError:
            return False
        else:
            return True

    def get_bookmark_title(self, path):
        """ Get bookmark title. """
        try:
            ret = self.config.get(path, 'title')
        except ConfigParser.NoOptionError:
            ret = path
        
        return ret
    
    def set_bookmark_title(self, path, title):
        """ Set bookmark title. """
        self.config.set(path, 'title', title)
    
    def remove_bookmark(self, path):
        """ Remove bookmark. """
        return self.config.remove_section(path)

    def set_preference(self, option, value):
        """ Set the value of the given option. """
        if value == True:
            value = 'yes'
        elif value == False:
            value = 'no'
        
        if self.config.has_section('preferences'):
            self.config.set('preferences', option, value)
        else:
            self.config.add_section('preferences')
            self.config.set('preferences', option, value)

    def get_preference(self, option, kind='str'):
        """ Get the value of the given option.
        
        :param kind: str/bool/int/float. default: str
        """
        if self.config.has_option('preferences', option):
            if kind == 'bool':
                return self.config.getboolean('preferences', option)
            elif kind == 'int':
                return self.config.getint('preferences', option)
            elif kind == 'float':
                return self.config.getfloat('preferences', option)
            else:
                return self.config.get('preferences', option)
        else:
            try:
                return self._get_default(option)
            except KeyError:
                return None
 
