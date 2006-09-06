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

import ConfigParser
import os
import os.path
import sys

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass
try:
    import gtk
    import gtk.gdk
    import gtk.glade
except:
    sys.exit(1)

from handler import OliveHandler
import bzrlib.errors as errors

# Olive GTK UI version
__version__ = '0.10.0'

class OliveGtk:
    """ The main Olive GTK frontend class. This is called when launching the
    program. """
    
    def __init__(self):
        # Load the glade file
        if sys.platform == 'win32':
            self.gladefile = os.path.dirname(sys.executable) + "/share/olive/olive.glade"
        else:
            self.gladefile = "/usr/share/olive/olive.glade"

        if not os.path.exists(self.gladefile):
            # Load from current directory if not installed
            self.gladefile = "olive.glade"
            # Check again
            if not os.path.exists(self.gladefile):
                # Fail
                print _('Glade file cannot be found.')
                sys.exit(1)

        self.toplevel = gtk.glade.XML(self.gladefile, 'window_main', 'olive-gtk')
        
        self.window = self.toplevel.get_widget('window_main')
        
        self.pref = OlivePreferences()
        self.comm = OliveCommunicator(self.toplevel, self.pref)
        handler = OliveHandler(self.gladefile, self.comm)
        
        # Dictionary for signal_autoconnect
        dic = { "on_window_main_destroy": gtk.main_quit,
                "on_window_main_delete_event": handler.on_window_main_delete_event,
                "on_quit_activate": handler.on_window_main_delete_event,
                "on_about_activate": handler.on_about_activate,
                "on_menuitem_add_files_activate": handler.on_menuitem_add_files_activate,
                "on_menuitem_remove_file_activate": handler.on_menuitem_remove_file_activate,
                "on_menuitem_file_make_directory_activate": handler.on_menuitem_file_make_directory_activate,
                "on_menuitem_file_move_activate": handler.on_menuitem_file_move_activate,
                "on_menuitem_file_rename_activate": handler.on_menuitem_file_rename_activate,
                "on_menuitem_view_show_hidden_files_activate": handler.on_menuitem_view_show_hidden_files_activate,
                "on_menuitem_view_refresh_activate": handler.on_menuitem_view_refresh_activate,
                "on_menuitem_branch_initialize_activate": handler.on_menuitem_branch_initialize_activate,
                "on_menuitem_branch_get_activate": handler.on_menuitem_branch_get_activate,
                "on_menuitem_branch_checkout_activate": handler.on_menuitem_branch_checkout_activate,
                "on_menuitem_branch_commit_activate": handler.on_menuitem_branch_commit_activate,
                "on_menuitem_branch_push_activate": handler.on_menuitem_branch_push_activate,
                "on_menuitem_branch_pull_activate": handler.on_menuitem_branch_pull_activate,
                "on_menuitem_branch_status_activate": handler.on_menuitem_branch_status_activate,
                "on_menuitem_branch_missing_revisions_activate": handler.on_menuitem_branch_missing_revisions_activate,
                "on_menuitem_stats_diff_activate": handler.on_menuitem_stats_diff_activate,
                "on_menuitem_stats_log_activate": handler.on_menuitem_stats_log_activate,
                "on_menuitem_stats_infos_activate": handler.on_menuitem_stats_infos_activate,
                "on_toolbutton_refresh_clicked": handler.on_menuitem_view_refresh_activate,
                "on_toolbutton_log_clicked": handler.on_menuitem_stats_log_activate,
                #"on_menutoolbutton_diff_clicked": handler.on_menuitem_stats_diff_activate,
                "on_toolbutton_diff_clicked": handler.on_menuitem_stats_diff_activate,
                "on_toolbutton_commit_clicked": handler.on_menuitem_branch_commit_activate,
                "on_toolbutton_pull_clicked": handler.on_menuitem_branch_pull_activate,
                "on_toolbutton_push_clicked": handler.on_menuitem_branch_push_activate,
                "on_treeview_right_button_press_event": handler.on_treeview_right_button_press_event,
                "on_treeview_right_row_activated": handler.on_treeview_right_row_activated,
                "on_treeview_left_button_press_event": handler.on_treeview_left_button_press_event,
                "on_treeview_left_row_activated": handler.on_treeview_left_row_activated }
        
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
        self.comm.hpaned_main.set_position(pos)
        
        # Apply menu to the toolbutton
        #menubutton = self.toplevel.get_widget('menutoolbutton_diff')
        #menubutton.set_menu(handler.menu.toolbar_diff)
        
        # Now we can show the window
        self.window.show_all()
        
        # Load default data into the panels
        self.treeview_left = self.toplevel.get_widget('treeview_left')
        self.treeview_right = self.toplevel.get_widget('treeview_right')
        self._load_left()
        self._load_right()

        # Apply menu state
        self.comm.menuitem_view_show_hidden_files.set_active(self.pref.get_preference('dotted_files', 'bool'))
        
    def _load_left(self):
        """ Load data into the left panel. (Bookmarks) """
        # set cursor to busy
        self.comm.set_busy(self.treeview_left)
        
        # Create TreeStore
        treestore = gtk.TreeStore(str, str)
        
        # Get bookmarks
        bookmarks = self.comm.pref.get_bookmarks()
        
        # Add them to the TreeStore
        titer = treestore.append(None, [_('Bookmarks'), None])
        for item in bookmarks:
            title = self.comm.pref.get_bookmark_title(item)
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
        
        self.comm.set_busy(self.treeview_left, False)
        
    def _load_right(self):
        """ Load data into the right panel. (Filelist) """
        # set cursor to busy
        self.comm.set_busy(self.treeview_right)
        
        # Create ListStore
        liststore = gtk.ListStore(str, str, str)
        
        dirs = ['..']
        files = []
        
        # Fill the appropriate lists
        path = self.comm.get_path()
        dotted_files = self.pref.get_preference('dotted_files', 'bool')
        for item in os.listdir(path):
            if not dotted_files and item[0] == '.':
                continue
            if os.path.isdir(path + '/' + item):
                dirs.append(item)
            else:
                files.append(item)
            
        # Sort'em
        dirs.sort()
        files.sort()
        
        # Add'em to the ListStore
        for item in dirs:    
            liststore.append([gtk.STOCK_DIRECTORY, item, ''])
        for item in files:
            try:
                status = check_status(path + '/' + item)
            except errors.PermissionDenied:
                continue
            
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
        
        # Check if current directory is versioned
        try:
            from bzrlib.branch import Branch
            Branch.open_containing(self.comm.get_path())
            # Activate some items
            self.comm.menuitem_branch_init.set_sensitive(False)
            self.comm.menuitem_branch_get.set_sensitive(True)
            self.comm.menuitem_branch_checkout.set_sensitive(True)
            self.comm.menuitem_branch_pull.set_sensitive(True)
            self.comm.menuitem_branch_push.set_sensitive(True)
            self.comm.menuitem_branch_commit.set_sensitive(True)
            self.comm.menuitem_branch_status.set_sensitive(True)
            self.comm.menuitem_branch_missing.set_sensitive(True)
            self.comm.menuitem_stats.set_sensitive(True)
            self.comm.menuitem_add_files.set_sensitive(True)
            self.comm.menuitem_remove_files.set_sensitive(True)
            self.comm.menuitem_file_make_directory.set_sensitive(True)
            self.comm.menuitem_file_rename.set_sensitive(True)
            self.comm.menuitem_file_move.set_sensitive(True)
            #self.comm.menutoolbutton_diff.set_sensitive(True)
            self.comm.toolbutton_diff.set_sensitive(True)
            self.comm.toolbutton_log.set_sensitive(True)
            self.comm.toolbutton_commit.set_sensitive(True)
            self.comm.toolbutton_pull.set_sensitive(True)
            self.comm.toolbutton_push.set_sensitive(True)
        except errors.NotBranchError:
            # Deactivate some items
            self.comm.menuitem_branch_init.set_sensitive(True)
            self.comm.menuitem_branch_get.set_sensitive(False)
            self.comm.menuitem_branch_checkout.set_sensitive(False)
            self.comm.menuitem_branch_pull.set_sensitive(False)
            self.comm.menuitem_branch_push.set_sensitive(False)
            self.comm.menuitem_branch_commit.set_sensitive(False)
            self.comm.menuitem_branch_status.set_sensitive(False)
            self.comm.menuitem_branch_missing.set_sensitive(False)
            self.comm.menuitem_stats.set_sensitive(False)
            self.comm.menuitem_add_files.set_sensitive(False)
            self.comm.menuitem_remove_files.set_sensitive(False)
            self.comm.menuitem_file_make_directory.set_sensitive(False)
            self.comm.menuitem_file_rename.set_sensitive(False)
            self.comm.menuitem_file_move.set_sensitive(False)
            #self.comm.menutoolbutton_diff.set_sensitive(False)
            self.comm.toolbutton_diff.set_sensitive(False)
            self.comm.toolbutton_log.set_sensitive(False)
            self.comm.toolbutton_commit.set_sensitive(False)
            self.comm.toolbutton_pull.set_sensitive(False)
            self.comm.toolbutton_push.set_sensitive(False)
    
        # set cursor to default
        self.comm.set_busy(self.treeview_right, False)

class OliveCommunicator:
    """ This class is responsible for the communication between the different
    modules. """
    def __init__(self, toplevel, pref):
        # Get glade main component
        self.toplevel = toplevel
        # Preferences object
        self.pref = pref
        # Default path
        self._path = os.getcwd()
        
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
    
    def set_path(self, path):
        """ Set the current path while browsing the directories. """
        self._path = path
    
    def get_path(self):
        """ Get the current path. """
        return self._path
    
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
    
    def refresh_left(self):
        """ Refresh the bookmark list. """
        # set cursor to busy
        self.set_busy(self.treeview_left)
        
        # Get TreeStore and clear it
        treestore = self.treeview_left.get_model()
        treestore.clear()
        
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
        
        self.set_busy(self.treeview_left, False)
    
    def refresh_right(self, path=None):
        """ Refresh the file list. """
        self.set_busy(self.treeview_right)
        
        if path is None:
            path = self.get_path()
        
        # A workaround for double-clicking Bookmarks
        if not os.path.exists(path):
            self.set_busy(self.treeview_right, False)
            return

        # Get ListStore and clear it
        liststore = self.treeview_right.get_model()
        liststore.clear()
        
        dirs = ['..']
        files = []
        
        # Fill the appropriate lists
        dotted_files = self.pref.get_preference('dotted_files', 'bool')
        for item in os.listdir(path):
            if not dotted_files and item[0] == '.':
                continue
            if os.path.isdir(path + '/' + item):
                dirs.append(item)
            else:
                files.append(item)
            
        # Sort'em
        dirs.sort()
        files.sort()
        
        # Add'em to the ListStore
        for item in dirs:    
            liststore.append([gtk.STOCK_DIRECTORY, item, ''])
        for item in files:
            try:
                status = check_status(path + '/' + item)
            except errors.PermissionDenied:
                continue
            
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
        
        # Check if current directory is a branch
        try:
            from bzrlib.branch import Branch
            Branch.open_containing(self.get_path())
            # Activate some items
            self.menuitem_branch_init.set_sensitive(False)
            self.menuitem_branch_get.set_sensitive(True)
            self.menuitem_branch_checkout.set_sensitive(True)
            self.menuitem_branch_pull.set_sensitive(True)
            self.menuitem_branch_push.set_sensitive(True)
            self.menuitem_branch_commit.set_sensitive(True)
            self.menuitem_branch_status.set_sensitive(True)
            self.menuitem_branch_missing.set_sensitive(True)
            self.menuitem_stats.set_sensitive(True)
            self.menuitem_add_files.set_sensitive(True)
            self.menuitem_remove_files.set_sensitive(True)
            self.menuitem_file_make_directory.set_sensitive(True)
            self.menuitem_file_rename.set_sensitive(True)
            self.menuitem_file_move.set_sensitive(True)
            #self.menutoolbutton_diff.set_sensitive(True)
            self.toolbutton_diff.set_sensitive(True)
            self.toolbutton_log.set_sensitive(True)
            self.toolbutton_commit.set_sensitive(True)
            self.toolbutton_pull.set_sensitive(True)
            self.toolbutton_push.set_sensitive(True)
        except errors.NotBranchError:
            # Deactivate some items
            self.menuitem_branch_init.set_sensitive(True)
            self.menuitem_branch_get.set_sensitive(False)
            self.menuitem_branch_checkout.set_sensitive(False)
            self.menuitem_branch_pull.set_sensitive(False)
            self.menuitem_branch_push.set_sensitive(False)
            self.menuitem_branch_commit.set_sensitive(False)
            self.menuitem_branch_status.set_sensitive(False)
            self.menuitem_branch_missing.set_sensitive(False)
            self.menuitem_stats.set_sensitive(False)
            self.menuitem_add_files.set_sensitive(False)
            self.menuitem_remove_files.set_sensitive(False)
            self.menuitem_file_make_directory.set_sensitive(False)
            self.menuitem_file_rename.set_sensitive(False)
            self.menuitem_file_move.set_sensitive(False)
            #self.menutoolbutton_diff.set_sensitive(False)
            self.toolbutton_diff.set_sensitive(False)
            self.toolbutton_log.set_sensitive(False)
            self.toolbutton_commit.set_sensitive(False)
            self.toolbutton_pull.set_sensitive(False)
            self.toolbutton_push.set_sensitive(False)
        
        self.set_busy(self.treeview_right, False)

    def set_busy(self, widget, busy=True):
        if busy:
            widget.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
        else:
            widget.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.LEFT_PTR))

        gtk.main_iteration(0)

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
        if sys.platform == 'win32':
            # Windows - no dotted files
            self.config.read([os.path.expanduser('~/olive.conf')])
        else:
            self.config.read([os.path.expanduser('~/.olive.conf')])
        
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
    
    def set_preference(self, option, value):
        """ Set the value of the given option. """
        if self.config.has_section('preferences'):
            self.config.set('preferences', option, value)
        else:
            self.config.add_section('preferences')
            self.config.set('preferences', option, value)
    
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

def check_status(filename):
    """ Get the status of a file.
    
    :param filename: the full path to the file
    
    :return: renamed | added | removed | modified | unchanged | unknown
    """
    import bzrlib
    from bzrlib.delta import compare_trees
    from bzrlib.workingtree import WorkingTree
    
    try:
        tree1 = WorkingTree.open_containing(filename)[0]
    except errors.NotBranchError:
        return 'unknown'
    
    branch = tree1.branch
    tree2 = tree1.branch.repository.revision_tree(branch.last_revision())
    
    # find the relative path to the given file (needed for proper delta)
    wtpath = tree1.basedir
    fullpath = filename
    i = 0
    wtsplit = wtpath.split('/')
    fpsplit = fullpath.split('/')
    fpcopy = fullpath.split('/')
    for item in fpsplit:
        if i is not len(wtsplit):
            if item == wtsplit[i]:
                del fpcopy[0]
            i = i + 1
    rel = '/'.join(fpcopy)
    
    delta = tree1.changes_from(tree2,
                                   want_unchanged=True,
                                   specific_files=[rel])
    
    if len(delta.renamed):
        return 'renamed'
    elif len(delta.added):
        return 'added'
    elif len(delta.removed):
        return 'removed'
    elif len(delta.modified):
        return 'modified'
    elif len(delta.unchanged):
        return 'unchanged'
    else:
        return 'unknown'
