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
    import pango
except:
    sys.exit(1)

import bzrlib
import bzrlib.errors as errors

from bzrlib.status import show_tree_status
from bzrlib.workingtree import WorkingTree

from dialog import OliveDialog

class OliveStatus:
    """ Display Status window and perform the needed actions. """
    def __init__(self, gladefile, wt, wtpath):
        """ Initialize the Status window. """
        self.gladefile = gladefile
        self.glade = gtk.glade.XML(self.gladefile, 'window_status')
        
        # Get the Status window widget
        self.window = self.glade.get_widget('window_status')
        self.wt = wt
        self.wtpath = wtpath
        
        # Check if current location is a branch
        try:
            branch = wt.branch
        except errors.NotBranchError:
            self.notbranch = True
            return
        except:
            raise
        
        file_id = self.wt.path2id(wtpath)

        self.notbranch = False
        if file_id is None:
            self.notbranch = True
            return
        
        # Set the old working tree
        self.old_tree = self.wt.branch.repository.revision_tree(self.wt.branch.last_revision())
        
        # Dictionary for signal_autoconnect
        dic = { "on_button_status_close_clicked": self.close }
        
        # Connect the signals to the handlers
        self.glade.signal_autoconnect(dic)
        
        # Generate status output
        self._generate_status()

    def _generate_status(self):
        """ Generate 'bzr status' output. """
        self.model = gtk.TreeStore(str, str)
        self.treeview = self.glade.get_widget('treeview_status')
        self.treeview.set_model(self.model)
        
        cell = gtk.CellRendererText()
        cell.set_property("width-chars", 20)
        column = gtk.TreeViewColumn()
        column.pack_start(cell, expand=True)
        column.add_attribute(cell, "text", 0)
        self.treeview.append_column(column)
        
        delta = self.wt.changes_from(self.old_tree)

        changes = False
        
        if len(delta.added):
            changes = True
            titer = self.model.append(None, [ _('Added'), None ])
            for path, id, kind in delta.added:
                self.model.append(titer, [ path, path ])

        if len(delta.removed):
            changes = True
            titer = self.model.append(None, [ _('Removed'), None ])
            for path, id, kind in delta.removed:
                self.model.append(titer, [ path, path ])

        if len(delta.renamed):
            changes = True
            titer = self.model.append(None, [ _('Renamed'), None ])
            for oldpath, newpath, id, kind, text_modified, meta_modified \
                    in delta.renamed:
                self.model.append(titer, [ oldpath, newpath ])

        if len(delta.modified):
            changes = True
            titer = self.model.append(None, [ _('Modified'), None ])
            for path, id, kind, text_modified, meta_modified in delta.modified:
                self.model.append(titer, [ path, path ])
        
        done_unknown = False
        for path in self.wt.unknowns():
            changes = True
            if not done_unknown:
                titer = self.model.append(None, [ _('Unknown'), None ])
                done_unknown = True
            self.model.append(titer, [ path, path ])

        if not changes:
            self.model.append(None, [ _('No changes.'), None ])

        self.treeview.expand_all()
    
    def display(self):
        """ Display the Diff window. """
        if self.notbranch:
            error_dialog(_('Directory is not a branch'),
                                     _('You can perform this action only in a branch.'))
            self.close()
        else:
            self.window.show_all()

    def close(self, widget=None):
        self.window.destroy()
