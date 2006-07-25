# Copyright (C) 2006 by Szilveszter Farkas (Phanatic) <szilveszter.farkas@gmail.com>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import sys

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass
try:
    import gtk
    import gtk.glade
    import gobject
except:
    sys.exit(1)

from bzrlib.delta import compare_trees
import bzrlib.errors as errors
from bzrlib.workingtree import WorkingTree

from dialog import OliveDialog

class OliveCommit:
    """ Display Commit dialog and perform the needed actions. """
    def __init__(self, gladefile, comm):
        """ Initialize the Commit dialog. """
        self.gladefile = gladefile
        self.glade = gtk.glade.XML(self.gladefile, 'window_commit')
        
        self.comm = comm
        
        self.dialog = OliveDialog(self.gladefile)
        
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
        
        # Set the delta
        self.old_tree = self.wt.branch.repository.revision_tree(self.wt.branch.last_revision())
        self.delta = compare_trees(self.old_tree, self.wt)
        
        # Get the Commit dialog widget
        self.window = self.glade.get_widget('window_commit')
        
        # Dictionary for signal_autoconnect
        dic = { "on_button_commit_commit_clicked": self.commit,
                "on_button_commit_cancel_clicked": self.close }
        
        # Connect the signals to the handlers
        self.glade.signal_autoconnect(dic)
        
        # Create the file list
        self._create_file_view()
    
    def display(self):
        """ Display the Push dialog. """
        if self.notbranch:
            self.dialog.error_dialog('Directory is not a branch.')
        else:
            self.window.show_all()
    
    # This code is from Jelmer Vernooij's bzr-gtk branch
    def _create_file_view(self):
        self.file_store = gtk.ListStore(gobject.TYPE_BOOLEAN,
                                        gobject.TYPE_STRING,
                                        gobject.TYPE_STRING)
        self.file_view = self.glade.get_widget('treeview_commit_select')
        self.file_view.set_model(self.file_store)
        crt = gtk.CellRendererToggle()
        crt.set_property("activatable", True)
        crt.connect("toggled", self._toggle_commit, self.file_store)
        self.file_view.append_column(gtk.TreeViewColumn("Commit",
                                     crt, active=0))
        self.file_view.append_column(gtk.TreeViewColumn("Path",
                                     gtk.CellRendererText(), text=1))
        self.file_view.append_column(gtk.TreeViewColumn("Type",
                                     gtk.CellRendererText(), text=2))

        for path, _, _ in self.delta.added:
            self.file_store.append([ True, path, "added" ])

        for path, _, _ in self.delta.removed:
            self.file_store.append([ True, path, "removed" ])

        for oldpath, _, _, _, _, _ in self.delta.renamed:
            self.file_store.append([ True, oldpath, "renamed"])

        for path, _, _, _, _ in self.delta.modified:
            self.file_store.append([ True, path, "modified"])
    
    def _get_specific_files(self):
        ret = []
        it = self.file_store.get_iter_first()
        while it:
            if self.file_store.get_value(it, 0):
                ret.append(self.file_store.get_value(it, 1))
            it = self.file_store.iter_next(it)

        return ret
    # end of bzr-gtk code
    
    def _toggle_commit(self, cell, path, model):
        model[path][0] = not model[path][0]
        return
    
    def commit(self, widget):
        textview = self.glade.get_widget('textview_commit')
        textbuffer = textview.get_buffer()
        start, end = textbuffer.get_bounds()
        message = textbuffer.get_text(start, end)
        
        checkbutton_local = self.glade.get_widget('checkbutton_commit_local')
        checkbutton_strict = self.glade.get_widget('checkbutton_commit_strict')
        checkbutton_force = self.glade.get_widget('checkbutton_commit_force')
        
        specific_files = self._get_specific_files()
        
        # merged from Jelmer Vernooij's olive integration branch
        try:
            self.wt.commit(message, 
                           allow_pointless=checkbutton_force.get_active(),
                           strict=checkbutton_strict.get_active(),
                           local=checkbutton_local.get_active(),
                           specific_files=specific_files)
        except errors.NotBranchError:
            self.dialog.error_dialog('Directory is not a branch.')
            return
        except errors.LocalRequiresBoundBranch:
            self.dialog.error_dialog('Local commit requires a bound branch.')
            return
        except errors.PointlessCommit:
            self.dialog.error_dialog('No changes to commit. Try force commit.')
            return
        except errors.ConflictsInTree:
            self.dialog.error_dialog('Conflicts in tree. Please resolve them first.')
            return
        except errors.StrictCommitFailed:
            self.dialog.error_dialog('Strict commit failed. There are unknown files.')
            return
        except errors.BoundBranchOutOfDate, errmsg:
            self.dialog.error_dialog('Bound branch is out of date: %s' % errmsg)
            return
        except:
            raise
        
        self.close()
        self.comm.refresh_right()
        
    def close(self, widget=None):
        self.window.destroy()
