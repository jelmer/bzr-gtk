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

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

import gtk
import gtk.glade
import gobject
import pango

import bzrlib.errors as errors

from dialog import error_dialog
from olive import gladefile

class OliveCommit:
    """ Display Commit dialog and perform the needed actions. """
    def __init__(self, wt, wtpath):
        """ Initialize the Commit dialog. """
        self.glade = gtk.glade.XML(gladefile, 'window_commit', 'olive-gtk')
        
        self.wt = wt
        self.wtpath = wtpath

        # Get some important widgets
        self.window = self.glade.get_widget('window_commit')
        self.checkbutton_local = self.glade.get_widget('checkbutton_commit_local')
        self.textview = self.glade.get_widget('textview_commit')
        self.file_view = self.glade.get_widget('treeview_commit_select')

        file_id = self.wt.path2id(wtpath)

        self.notbranch = False
        if file_id is None:
            self.notbranch = True
            return
        
        # Set the delta
        self.old_tree = self.wt.branch.repository.revision_tree(self.wt.branch.last_revision())
        self.delta = self.wt.changes_from(self.old_tree)
        
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
            error_dialog(_('Directory is not a branch'),
                         _('You can perform this action only in a branch.'))
            self.close()
        else:
            if self.wt.branch.get_bound_location() is not None:
                # we have a checkout, so the local commit checkbox must appear
                self.checkbutton_local.show()
            
            self.textview.modify_font(pango.FontDescription("Monospace"))
            self.window.show()
            
    
    def _create_file_view(self):
        self.file_store = gtk.ListStore(gobject.TYPE_BOOLEAN,
                                        gobject.TYPE_STRING,
                                        gobject.TYPE_STRING)
        self.file_view.set_model(self.file_store)
        crt = gtk.CellRendererToggle()
        crt.set_property("activatable", True)
        crt.connect("toggled", self._toggle_commit, self.file_store)
        self.file_view.append_column(gtk.TreeViewColumn(_('Commit'),
                                     crt, active=0))
        self.file_view.append_column(gtk.TreeViewColumn(_('Path'),
                                     gtk.CellRendererText(), text=1))
        self.file_view.append_column(gtk.TreeViewColumn(_('Type'),
                                     gtk.CellRendererText(), text=2))

        for path, id, kind in self.delta.added:
            self.file_store.append([ True, path, _('added') ])

        for path, id, kind in self.delta.removed:
            self.file_store.append([ True, path, _('removed') ])

        for oldpath, newpath, id, kind, text_modified, meta_modified in self.delta.renamed:
            self.file_store.append([ True, oldpath, _('renamed') ])

        for path, id, kind, text_modified, meta_modified in self.delta.modified:
            self.file_store.append([ True, path, _('modified') ])
    
    def _get_specific_files(self):
        ret = []
        it = self.file_store.get_iter_first()
        while it:
            if self.file_store.get_value(it, 0):
                ret.append(self.file_store.get_value(it, 1))
            it = self.file_store.iter_next(it)

        return ret
    
    def _toggle_commit(self, cell, path, model):
        model[path][0] = not model[path][0]
        return
    
    def commit(self, widget):
        textbuffer = self.textview.get_buffer()
        start, end = textbuffer.get_bounds()
        message = textbuffer.get_text(start, end)
        
        checkbutton_strict = self.glade.get_widget('checkbutton_commit_strict')
        checkbutton_force = self.glade.get_widget('checkbutton_commit_force')
        
        specific_files = self._get_specific_files()
        
        try:
            self.wt.commit(message, 
                           allow_pointless=checkbutton_force.get_active(),
                           strict=checkbutton_strict.get_active(),
                           local=self.checkbutton_local.get_active(),
                           specific_files=specific_files)
        except errors.NotBranchError:
            error_dialog(_('Directory is not a branch'),
                         _('You can perform this action only in a branch.'))
            return
        except errors.LocalRequiresBoundBranch:
            error_dialog(_('Directory is not a checkout'),
                         _('You can perform local commit only on checkouts.'))
            return
        except errors.PointlessCommit:
            error_dialog(_('No changes to commit'),
                         _('Try force commit if you want to commit anyway.'))
            return
        except errors.ConflictsInTree:
            error_dialog(_('Conflicts in tree'),
                         _('You need to resolve the conflicts before committing.'))
            return
        except errors.StrictCommitFailed:
            error_dialog(_('Strict commit failed'),
                         _('There are unknown files in the working tree.\nPlease add or delete them.'))
            return
        except errors.BoundBranchOutOfDate, errmsg:
            error_dialog(_('Bound branch is out of date'),
                         _('%s') % errmsg)
            return
        except errors.BzrError, msg:
            error_dialog(_('Unknown bzr error'), str(msg))
            return
        except Exception, msg:
            error_dialog(_('Unknown error'), str(msg))
            return
        
        self.close()
        
    def close(self, widget=None):
        self.window.destroy()
