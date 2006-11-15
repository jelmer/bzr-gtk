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
from bzrlib import osutils

from dialog import error_dialog
from guifiles import GLADEFILENAME


class CommitDialog:
    """ Display Commit dialog and perform the needed actions. """
    def __init__(self, wt, wtpath, notbranch):
        """ Initialize the Commit dialog.
        @param  wt:         bzr WorkingTree object
        @param  wtpath:     path to working tree root
        @param  notbranch:  flag that path is not a brach
        @type   notbranch:  bool
        """
        self.glade = gtk.glade.XML(GLADEFILENAME, 'window_commit', 'olive-gtk')
        
        self.wt = wt
        self.wtpath = wtpath
        self.notbranch = notbranch

        # Get some important widgets
        self.window = self.glade.get_widget('window_commit')
        self.checkbutton_local = self.glade.get_widget('checkbutton_commit_local')
        self.textview = self.glade.get_widget('textview_commit')
        self.file_view = self.glade.get_widget('treeview_commit_select')
        self.pending_label = self.glade.get_widget('label_commit_pending')
        self.pending_view = self.glade.get_widget('treeview_commit_pending')

        if wt is None or notbranch:
            return
        
        # Set the delta
        self.old_tree = self.wt.branch.repository.revision_tree(self.wt.branch.last_revision())
        self.delta = self.wt.changes_from(self.old_tree)
        
        # Get pending merges
        self.pending = self._pending_merges(self.wt)
        
        # Dictionary for signal_autoconnect
        dic = { "on_button_commit_commit_clicked": self.commit,
                "on_button_commit_cancel_clicked": self.close }

        # Connect the signals to the handlers
        self.glade.signal_autoconnect(dic)
        
        # Create the file list
        self._create_file_view()
        # Create the pending merges
        self._create_pending_merges()
    
    def display(self):
        """ Display the Push dialog.
        @return:    True if dialog is shown.
        """
        if self.wt is None and not self.notbranch:
            error_dialog(_('Directory does not have a working tree'),
                         _('Operation aborted.'))
            self.close()
            return False
        if self.notbranch:
            error_dialog(_('Directory is not a branch'),
                         _('You can perform this action only in a branch.'))
            self.close()
            return False
        else:
            if self.wt.branch.get_bound_location() is not None:
                # we have a checkout, so the local commit checkbox must appear
                self.checkbutton_local.show()
            
            if self.pending:
                # There are pending merges, file selection not supported
                self.file_view.set_sensitive(False)
            else:
                # No pending merges
                self.pending_view.set_sensitive(False)
            
            self.textview.modify_font(pango.FontDescription("Monospace"))
            self.window.show()
            return True
    
    def _create_file_view(self):
        self.file_store = gtk.ListStore(gobject.TYPE_BOOLEAN,   # [0] checkbox
                                        gobject.TYPE_STRING,    # [1] path to display
                                        gobject.TYPE_STRING,    # [2] changes type
                                        gobject.TYPE_STRING)    # [3] real path
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
            marker = osutils.kind_marker(kind)
            self.file_store.append([ True, path+marker, _('added'), path ])

        for path, id, kind in self.delta.removed:
            marker = osutils.kind_marker(kind)
            self.file_store.append([ True, path+marker, _('removed'), path ])

        for oldpath, newpath, id, kind, text_modified, meta_modified in self.delta.renamed:
            marker = osutils.kind_marker(kind)
            if text_modified or meta_modified:
                changes = _('renamed and modified')
            else:
                changes = _('renamed')
            self.file_store.append([ True,
                                     oldpath+marker + '  =>  ' + newpath+marker,
                                     changes,
                                     newpath
                                   ])

        for path, id, kind, text_modified, meta_modified in self.delta.modified:
            marker = osutils.kind_marker(kind)
            self.file_store.append([ True, path+marker, _('modified'), path ])
    
    def _create_pending_merges(self):
        if not self.pending:
            # hide unused pending merge part
            scrolled_window = self.glade.get_widget('scrolledwindow_commit_pending')
            parent = scrolled_window.get_parent()
            parent.remove(scrolled_window)
            parent = self.pending_label.get_parent()
            parent.remove(self.pending_label)
            return
        
        liststore = gtk.ListStore(gobject.TYPE_STRING,
                                  gobject.TYPE_STRING,
                                  gobject.TYPE_STRING)
        self.pending_view.set_model(liststore)
        
        self.pending_view.append_column(gtk.TreeViewColumn(_('Date'),
                                        gtk.CellRendererText(), text=0))
        self.pending_view.append_column(gtk.TreeViewColumn(_('Committer'),
                                        gtk.CellRendererText(), text=1))
        self.pending_view.append_column(gtk.TreeViewColumn(_('Summary'),
                                        gtk.CellRendererText(), text=2))
        
        for item in self.pending:
            liststore.append([ item['date'],
                               item['committer'],
                               item['summary'] ])
    
    def _get_specific_files(self):
        ret = []
        it = self.file_store.get_iter_first()
        while it:
            if self.file_store.get_value(it, 0):
                # get real path from hidden column 3
                ret.append(self.file_store.get_value(it, 3))
            it = self.file_store.iter_next(it)

        return ret
    
    def _toggle_commit(self, cell, path, model):
        model[path][0] = not model[path][0]
        return
    
    def _pending_merges(self, wt):
        """ Return a list of pending merges or None if there are none of them. """
        parents = wt.get_parent_ids()
        if len(parents) < 2:
            return None
        
        import re
        from bzrlib.osutils import format_date
        
        pending = parents[1:]
        branch = wt.branch
        last_revision = parents[0]
        
        if last_revision is not None:
            try:
                ignore = set(branch.repository.get_ancestry(last_revision))
            except errors.NoSuchRevision:
                # the last revision is a ghost : assume everything is new 
                # except for it
                ignore = set([None, last_revision])
        else:
            ignore = set([None])
        
        pm = []
        for merge in pending:
            ignore.add(merge)
            try:
                m_revision = branch.repository.get_revision(merge)
                
                rev = {}
                rev['committer'] = re.sub('<.*@.*>', '', m_revision.committer).strip(' ')
                rev['summary'] = m_revision.get_summary()
                rev['date'] = format_date(m_revision.timestamp,
                                          m_revision.timezone or 0, 
                                          'original', date_fmt="%Y-%m-%d",
                                          show_offset=False)
                
                pm.append(rev)
                
                inner_merges = branch.repository.get_ancestry(merge)
                assert inner_merges[0] is None
                inner_merges.pop(0)
                inner_merges.reverse()
                for mmerge in inner_merges:
                    if mmerge in ignore:
                        continue
                    mm_revision = branch.repository.get_revision(mmerge)
                    
                    rev = {}
                    rev['committer'] = re.sub('<.*@.*>', '', mm_revision.committer).strip(' ')
                    rev['summary'] = mm_revision.get_summary()
                    rev['date'] = format_date(mm_revision.timestamp,
                                              mm_revision.timezone or 0, 
                                              'original', date_fmt="%Y-%m-%d",
                                              show_offset=False)
                
                    pm.append(rev)
                    
                    ignore.add(mmerge)
            except errors.NoSuchRevision:
                print "DEBUG: NoSuchRevision:", merge
        
        return pm

    def commit(self, widget):
        textbuffer = self.textview.get_buffer()
        start, end = textbuffer.get_bounds()
        message = textbuffer.get_text(start, end).decode('utf-8')
        
        checkbutton_strict = self.glade.get_widget('checkbutton_commit_strict')
        checkbutton_force = self.glade.get_widget('checkbutton_commit_force')
        
        if not self.pending:
            specific_files = self._get_specific_files()
        else:
            specific_files = None
        
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
