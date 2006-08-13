# Copyright (C) 2006 by Szilveszter Farkas (Phanatic) <szilveszter.farkas@gmail.com>
#
# Some parts of the code:
# Copyright (C) 2005 by Canonical Ltd.
# Author: Scott James Remnant <scott@ubuntu.com>
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

import sys

from cStringIO import StringIO

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass
try:
    import gtk
    import gtk.glade
    import gobject
    import pango
except:
    sys.exit(1)

try:
    import gtksourceview
    have_gtksourceview = True
except ImportError:
    have_gtksourceview = False

import bzrlib

if bzrlib.version_info < (0, 9):
    # function deprecated after 0.9
    from bzrlib.delta import compare_trees

from bzrlib.diff import show_diff_trees
import bzrlib.errors as errors
from bzrlib.workingtree import WorkingTree

class OliveDiff:
    """ Display Diff window and perform the needed actions. """
    def __init__(self, gladefile, comm, dialog):
        """ Initialize the Diff window. """
        self.gladefile = gladefile
        self.glade = gtk.glade.XML(self.gladefile, 'window_diff')
        
        # Communication object
        self.comm = comm
        # Dialog object
        self.dialog = dialog
        
        # Get some important widgets
        self.window = self.glade.get_widget('window_diff')
        self.treeview = self.glade.get_widget('treeview_diff_files')

        # Check if current location is a branch
        try:
            (self.wt, path) = WorkingTree.open_containing(self.comm.get_path())
            branch = self.wt.branch
        except errors.NotBranchError:
            self.notbranch = True
            return
        except:
            raise

        file_id = self.wt.path2id(path)

        self.notbranch = False
        if file_id is None:
            self.notbranch = True
            return
        
        # Set the old working tree
        self.old_tree = self.wt.branch.repository.revision_tree(self.wt.branch.last_revision())
        
        # Dictionary for signal_autoconnect
        dic = { "on_button_diff_close_clicked": self.close,
                "on_treeview_diff_files_cursor_changed": self.cursor_changed }
        
        # Connect the signals to the handlers
        self.glade.signal_autoconnect(dic)
        
        # Create the file list
        self._create_file_view()
        
        # Generate initial diff
        self._init_diff()
    
    def display(self):
        """ Display the Diff window. """
        if self.notbranch:
            self.dialog.error_dialog('Directory is not a branch',
                                     'You can perform this action only in a branch.')
            self.close()
        else:
            self.window.show_all()
    
    def _create_file_view(self):
        """ Create the list of files. """
        self.model = gtk.TreeStore(str, str)
        self.treeview.set_model(self.model)
        
        cell = gtk.CellRendererText()
        cell.set_property("width-chars", 20)
        column = gtk.TreeViewColumn()
        column.pack_start(cell, expand=True)
        column.add_attribute(cell, "text", 0)
        self.treeview.append_column(column)
        
        if have_gtksourceview:
            self.buffer = gtksourceview.SourceBuffer()
            slm = gtksourceview.SourceLanguagesManager()
            gsl = slm.get_language_from_mime_type("text/x-patch")
            self.buffer.set_language(gsl)
            self.buffer.set_highlight(True)

            sourceview = gtksourceview.SourceView(self.buffer)
        else:
            self.buffer = gtk.TextBuffer()
            sourceview = gtk.TextView(self.buffer)

        sourceview.set_editable(False)
        sourceview.modify_font(pango.FontDescription("Monospace"))
        scrollwin_diff = self.glade.get_widget('scrolledwindow_diff_diff')
        scrollwin_diff.add(sourceview)
    
    def _init_diff(self):
        """ Generate initial diff. """
        self.model.clear()
        if bzrlib.version_info < (0, 9):
            delta = compare_trees(self.old_tree, self.wt)
        else:
            delta = self.wt.changes_from(self.old_tree)

        self.model.append(None, [ "Complete Diff", "" ])

        if len(delta.added):
            titer = self.model.append(None, [ "Added", None ])
            for path, id, kind in delta.added:
                self.model.append(titer, [ path, path ])

        if len(delta.removed):
            titer = self.model.append(None, [ "Removed", None ])
            for path, id, kind in delta.removed:
                self.model.append(titer, [ path, path ])

        if len(delta.renamed):
            titer = self.model.append(None, [ "Renamed", None ])
            for oldpath, newpath, id, kind, text_modified, meta_modified \
                    in delta.renamed:
                self.model.append(titer, [ oldpath, newpath ])

        if len(delta.modified):
            titer = self.model.append(None, [ "Modified", None ])
            for path, id, kind, text_modified, meta_modified in delta.modified:
                self.model.append(titer, [ path, path ])

        self.treeview.expand_all()
    
    def cursor_changed(self, *args):
        """ Callback when the TreeView cursor changes. """
        (path, col) = self.treeview.get_cursor()
        specific_files = [ self.model[path][1] ]
        if specific_files == [ None ]:
            return
        elif specific_files == [ "" ]:
            specific_files = []

        s = StringIO()
        show_diff_trees(self.old_tree, self.wt, s, specific_files)
        self.buffer.set_text(s.getvalue())
    
    def close(self, widget=None):
        self.window.destroy()
