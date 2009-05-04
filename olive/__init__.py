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
import time
import errno

# gettext support
import gettext
gettext.install('olive-gtk')

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

import gobject
import gtk
import gtk.gdk

from bzrlib.branch import Branch
import bzrlib.errors as bzrerrors
from bzrlib.lazy_import import lazy_import
from bzrlib.ui import ui_factory
from bzrlib.workingtree import WorkingTree

from bzrlib.plugins.gtk import _i18n
from bzrlib.plugins.gtk.dialog import error_dialog, info_dialog, warning_dialog
from bzrlib.plugins.gtk.errors import show_bzr_error
from bzrlib.plugins.gtk.olive.window import OliveGui

from bzrlib.plugins.gtk.diff import DiffWindow
lazy_import(globals(), """
from bzrlib.plugins.gtk.viz import branchwin
""")
from bzrlib.plugins.gtk.annotate.gannotate import GAnnotateWindow
from bzrlib.plugins.gtk.annotate.config import GAnnotateConfig
from bzrlib.plugins.gtk.commit import CommitDialog
from bzrlib.plugins.gtk.conflicts import ConflictsDialog
from bzrlib.plugins.gtk.initialize import InitDialog
from bzrlib.plugins.gtk.push import PushDialog
from bzrlib.plugins.gtk.revbrowser import RevisionBrowser

def about():
    """ Display the AboutDialog. """
    from bzrlib.plugins.gtk import __version__, icon_path
    
    dialog = gtk.AboutDialog()
    dialog.set_name("Olive")
    dialog.set_version(__version__)
    dialog.set_copyright("Copyright (C) 2006-2008 Szilveszter Farkas (Phanatic)")
    dialog.set_website("https://launchpad.net/bzr-gtk")
    dialog.set_website_label("https://launchpad.net/bzr-gtk")
    dialog.set_icon_from_file(icon_path("oliveicon2.png"))
    dialog.set_logo(gtk.gdk.pixbuf_new_from_file(icon_path("oliveicon2.png")))
    dialog.set_authors([ _i18n("Lead Developer:"),
			 "Szilveszter Farkas <szilveszter.farkas@gmail.com>",
			 _i18n("Contributors:"),
			 "Jelmer Vernooij <jelmer@samba.org>",
			 "Mateusz Korniak <mateusz.korniak@ant.gliwice.pl>",
			 "Gary van der Merwe <garyvdm@gmail.com>" ])
    dialog.set_artists([ "Simon Pascal Klein <klepas@klepas.org>",
			 "Jakub Steiner <jimmac@novell.com>" ])

    dialog.run()
    # Destroy the dialog
    dialog.destroy()


class OliveGtk:
    """ The main Olive GTK frontend class. This is called when launching the
    program. """
    
    def __init__(self):
        self.window = OliveGui(calling_app = self)
        
        self.pref = Preferences()
        self.path = None

        # Initialize the statusbar
        self.context_id = self.window.statusbar.get_context_id('olive')
        
        # Get the drive selector
        self.combobox_drive = gtk.combo_box_new_text()
        self.combobox_drive.connect("changed", self._refresh_drives)
        
        # Get the navigation widgets
        self.hbox_location = self.window.locationbar
        self.button_location_up = self.window.button_location_up
        self.button_location_jump = self.window.button_location_jump
        self.entry_location = self.window.entry_location
        
        # Get the History widgets
        self.check_history = self.window.checkbutton_history
        self.entry_history = self.window.entry_history_revno
        self.button_history = self.window.button_history_browse
        
        self._just_started = True
        
        # Apply window size and position
        width = self.pref.get_preference('window_width', 'int')
        height = self.pref.get_preference('window_height', 'int')
        self.window.resize(width, height)
        x = self.pref.get_preference('window_x', 'int')
        y = self.pref.get_preference('window_y', 'int')
        self.window.move(x, y)
        # Apply paned position
        pos = self.pref.get_preference('paned_position', 'int')
        self.window.hpaned_main.set_position(pos)
        
        # Now we can show the window
        self.window.show()
        
        # Show drive selector if under Win32
        if sys.platform == 'win32':
            self.hbox_location.pack_start(self.combobox_drive, False, False, 0)
            self.hbox_location.reorder_child(self.combobox_drive, 1)
            self.combobox_drive.show()
            self.gen_hard_selector()
        
        self.refresh_left()

        # Apply menu state
        self.window.mb_view_showhidden.set_active(self.pref.get_preference('dotted_files', 'bool'))
        self.window.mb_view_showignored.set_active(self.pref.get_preference('ignored_files', 'bool'))

        # We're starting local
        self.remote = False
        self.remote_branch = None
        self.remote_path = None
        self.remote_revision = None
        
        self.set_path(os.getcwd())
        self.refresh_right()
        
        self._just_started = False

    def set_path(self, path, force_remote=False):
        self.window.location_status.destroy()
        self.notbranch = False
        
        if force_remote:
            # Forcing remote mode (reading data from inventory)
            self.window.set_location_status(gtk.STOCK_DISCONNECT)
            try:
                br = Branch.open_containing(path)[0]
            except bzrerrors.NotBranchError:
                self.window.set_location_status(gtk.STOCK_DIALOG_ERROR)
                self.check_history.set_active(False)
                self.check_history.set_sensitive(False)
                return False
            except bzrerrors.UnsupportedProtocol:
                self.window.set_location_status(gtk.STOCK_DIALOG_ERROR)
                self.check_history.set_active(False)
                self.check_history.set_sensitive(False)
                return False
            
            self.window.set_location_status(gtk.STOCK_CONNECT)
            
            self.remote = True
           
            # We're remote
            self.remote_branch, self.remote_path = Branch.open_containing(path)
            
            if self.remote_revision is None:
                self.remote_revision = self.remote_branch.last_revision()
            
            self.remote_entries = self.remote_branch.repository.get_inventory(self.remote_revision).entries()
            
            if len(self.remote_path) == 0:
                self.remote_parent = self.remote_branch.repository.get_inventory(self.remote_branch.last_revision()).iter_entries_by_dir().next()[1].file_id
            else:
                for (name, type) in self.remote_entries:
                    if name == self.remote_path:
                        self.remote_parent = type.file_id
                        break
            
            if not path.endswith('/'):
                path += '/'
            
            if self.remote_branch.base == path:
                self.button_location_up.set_sensitive(False)
            else:
                self.button_location_up.set_sensitive(True)
        else:
            if os.path.isdir(path):
                self.remote = False
                
                # We're local
                try:
                    self.wt, self.wtpath = WorkingTree.open_containing(os.path.realpath(path))
                except (bzrerrors.NotBranchError, bzrerrors.NoWorkingTree):
                    self.notbranch = True
                except bzrerrors.PermissionDenied:
                    self.window.set_location_status(gtk.STOCK_DIALOG_WARNING, allowPopup=True)
                    self.window.location_status.connect_object('clicked', warning_dialog, 
                                       *(_i18n('Branch information unreadable'),
                                		_i18n('The current folder is a branch but the .bzr folder is not readable')))
                    self.notbranch = True
                
                # If we're in the root, we cannot go up anymore
                if sys.platform == 'win32':
                    drive, tail = os.path.splitdrive(path)
                    if tail in ('', '/', '\\'):
                        self.button_location_up.set_sensitive(False)
                    else:
                        self.button_location_up.set_sensitive(True)
                else:
                    if self.path == '/':
                        self.button_location_up.set_sensitive(False)
                    else:
                        self.button_location_up.set_sensitive(True)
            elif not os.path.isfile(path):
                # Doesn't seem to be a file nor a directory, trying to open a
                # remote location
                self.window.set_location_status(gtk.STOCK_DISCONNECT)
                try:
                    br = Branch.open_containing(path)[0]
                except bzrerrors.NotBranchError:
                    self.window.set_location_status(gtk.STOCK_DIALOG_ERROR)
                    self.check_history.set_active(False)
                    self.check_history.set_sensitive(False)
                    return False
                except bzrerrors.UnsupportedProtocol:
                    self.window.set_location_status(gtk.STOCK_DIALOG_ERROR)
                    self.check_history.set_active(False)
                    self.check_history.set_sensitive(False)
                    return False
                
                self.window.set_location_status(gtk.STOCK_CONNECT)
                
                self.remote = True
               
                # We're remote
                self.remote_branch, self.remote_path = Branch.open_containing(path)
                
                if self.remote_revision is None:
                    self.remote_revision = self.remote_branch.last_revision()
                
                self.remote_entries = self.remote_branch.repository.get_inventory(self.remote_revision).entries()
                
                if len(self.remote_path) == 0:
                    self.remote_parent = self.remote_branch.repository.get_inventory(self.remote_branch.last_revision()).iter_entries_by_dir().next()[1].file_id
                else:
                    for (name, type) in self.remote_entries:
                        if name == self.remote_path:
                            self.remote_parent = type.file_id
                            break
                
                if not path.endswith('/'):
                    path += '/'
                
                if self.remote_branch.base == path:
                    self.button_location_up.set_sensitive(False)
                else:
                    self.button_location_up.set_sensitive(True)
        
        if self.notbranch:
            self.check_history.set_active(False)
            self.check_history.set_sensitive(False)
        else:
            self.check_history.set_sensitive(True)
        
        self.window.statusbar.push(self.context_id, path)
        self.entry_location.set_text(path)
        self.path = path
        return True

    def get_path(self):
        if not self.remote:
            return self.path
        else:
            # Remote mode
            if len(self.remote_path) > 0:
                return self.remote_branch.base + self.remote_path + '/'
            else:
                return self.remote_branch.base
   
    def on_about_activate(self, widget):
        about()
    
    def on_button_history_browse_clicked(self, widget):
        """ Browse for revision button handler. """
        if self.remote:
            br = self.remote_branch
        else:
            br = self.wt.branch
            
        revb = RevisionBrowser(br, self.window)
        response = revb.run()
        if response != gtk.RESPONSE_NONE:
            revb.hide()
        
            if response == gtk.RESPONSE_OK:
                if revb.selected_revno is not None:
                    self.entry_history.set_text(revb.selected_revno)
                    self.on_entry_history_revno_activate()
            
            revb.destroy()
    
    def on_button_location_jump_clicked(self, widget):
        """ Location Jump button handler. """
        location = self.entry_location.get_text()
        
        if self.set_path(location):
            self.refresh_right()
    
    def on_button_location_up_clicked(self, widget):
        """ Location Up button handler. """
        if not self.remote:
            # Local mode
            self.set_path(os.path.split(self.get_path())[0])
        else:
            # Remote mode
            delim = '/'
            newpath = delim.join(self.get_path().split(delim)[:-2])
            newpath += '/'
            self.set_path(newpath)

        self.refresh_right()
    
    def on_checkbutton_history_toggled(self, widget):
        """ History Mode toggle handler. """
        if self.check_history.get_active():
            # History Mode activated
            self.entry_history.set_sensitive(True)
            self.button_history.set_sensitive(True)
            if self.entry_history.get_text() != "":
                self.on_entry_history_revno_activate()
        else:
            # History Mode deactivated
            self.entry_history.set_sensitive(False)
            self.button_history.set_sensitive(False)
            
            # Return right window to normal view by acting like we jump to it
            self.on_button_location_jump_clicked(widget)
    
    @show_bzr_error
    def on_entry_history_revno_activate(self, widget=None):
        """ Key pressed handler for the history entry. """
        path = self.get_path()
        if not self.remote:
            self.remote = True
            self.remote_branch = self.wt.branch
        
        revno = int(self.entry_history.get_text())
        self.remote_revision = self.remote_branch.get_rev_id(revno)
        if self.set_path(path, True):
            self.refresh_right()

    def on_menuitem_add_files_activate(self, widget):
        """ Add file(s)... menu handler. """
        from bzrlib.plugins.gtk.olive.add import AddDialog
        add = AddDialog(self.wt, self.wtpath, self.get_selected_right(), self.window)
        response = add.run()
        add.destroy()
        if response == gtk.RESPONSE_OK:
            self.refresh_right()

    def on_menuitem_branch_get_activate(self, widget):
        """ Branch/Get... menu handler. """
        from bzrlib.plugins.gtk.branch import BranchDialog
        
        if self.remote:
            branch = BranchDialog(os.getcwd(), self.window, self.remote_branch.base)
        else:
            branch = BranchDialog(self.get_path(), self.window)
        response = branch.run()
        if response != gtk.RESPONSE_NONE:
            branch.hide()
            
            if response == gtk.RESPONSE_OK:
                self.refresh_right()
            
            branch.destroy()
    
    def on_menuitem_branch_checkout_activate(self, widget):
        """ Branch/Checkout... menu handler. """
        from bzrlib.plugins.gtk.checkout import CheckoutDialog
        
        if self.remote:
            checkout = CheckoutDialog(os.getcwd(), self.window, self.remote_branch.base)
        else:
            checkout = CheckoutDialog(self.get_path(), self.window)
        response = checkout.run()
        if response != gtk.RESPONSE_NONE:
            checkout.hide()
        
            if response == gtk.RESPONSE_OK:
                self.refresh_right()
            
            checkout.destroy()
    
    @show_bzr_error
    def on_menuitem_branch_commit_activate(self, widget):
        """ Branch/Commit... menu handler. """
        selected = self.get_selected_right()
        if selected:
            selected = os.path.join(self.wtpath, selected)
        commit = CommitDialog(wt=self.wt,
                              parent=self.window,
                              selected=selected,
                             )
        response = commit.run()
        if response != gtk.RESPONSE_NONE:
            commit.hide()
        
            if response == gtk.RESPONSE_OK:
                self.refresh_right()
            
            commit.destroy()
    
    def on_menuitem_branch_conflicts_activate(self, widget):
        """ Branch/Conflicts... menu handler. """
        conflicts = ConflictsDialog(self.wt, self.window)
        response = conflicts.run()
        if response != gtk.RESPONSE_NONE:
            conflicts.destroy()
    
    def on_menuitem_branch_merge_activate(self, widget):
        """ Branch/Merge... menu handler. """
        from bzrlib.plugins.gtk.merge import MergeDialog
        
        if self.check_for_changes():
            error_dialog(_i18n('There are local changes in the branch'),
                         _i18n('Please commit or revert the changes before merging.'))
        else:
            parent_branch_path = self.wt.branch.get_parent()
            merge = MergeDialog(self.wt, self.wtpath, parent_branch_path, self.window)
            response = merge.run()
            merge.destroy()
            if response == gtk.RESPONSE_OK:
                self.refresh_right()

    @show_bzr_error
    def on_menuitem_branch_missing_revisions_activate(self, widget):
        """ Branch/Missing revisions menu handler. """
        
        from bzrlib.missing import find_unmerged, iter_log_revisions
        
        local_branch = self.wt.branch
        parent_branch_path = local_branch.get_parent()
        if parent_branch_path is None:
            error_dialog(_i18n('Parent location is unknown'),
                         _i18n('Cannot determine missing revisions if no parent location is known.'))
            return
        
        parent_branch = Branch.open(parent_branch_path)
        
        if parent_branch.base == local_branch.base:
            parent_branch = local_branch
        
        local_extra, remote_extra = find_unmerged(local_branch,parent_branch)

        if local_extra or remote_extra:
            
            ## def log_revision_one_line_text(log_revision):
            ##    """ Generates one line description of log_revison ended with end of line."""
            ##    revision = log_revision.rev
            ##    txt =  "- %s (%s)\n" % (revision.get_summary(), revision.committer, )
            ##    txt = txt.replace("<"," ") # Seems < > chars are expected to be xml tags ...
            ##    txt = txt.replace(">"," ")
            ##    return txt
            
            dlg_txt = ""
            if local_extra:
                dlg_txt += _i18n('%d local extra revision(s). \n') % (len(local_extra),) 
                ## NOTE: We do not want such ugly info about missing revisions
                ##       Revision Browser should be used there
                ## max_revisions = 10
                ## for log_revision in iter_log_revisions(local_extra, local_branch.repository, verbose=1):
                ##    dlg_txt += log_revision_one_line_text(log_revision)
                ##    if max_revisions <= 0:
                ##        dlg_txt += _i18n("more ... \n")
                ##        break
                ## max_revisions -= 1
            ## dlg_txt += "\n"
            if remote_extra:
                dlg_txt += _i18n('%d local missing revision(s).\n') % (len(remote_extra),) 
                ## max_revisions = 10
                ## for log_revision in iter_log_revisions(remote_extra, parent_branch.repository, verbose=1):
                ##    dlg_txt += log_revision_one_line_text(log_revision)
                ##    if max_revisions <= 0:
                ##        dlg_txt += _i18n("more ... \n")
                ##        break
                ##    max_revisions -= 1
                
            info_dialog(_i18n('There are missing revisions'),
                        dlg_txt)
        else:
            info_dialog(_i18n('Local branch up to date'),
                        _i18n('There are no missing revisions.'))

    @show_bzr_error
    def on_menuitem_branch_pull_activate(self, widget):
        """ Branch/Pull menu handler. """
        branch_to = self.wt.branch

        location = branch_to.get_parent()
        if location is None:
            error_dialog(_i18n('Parent location is unknown'),
                                     _i18n('Pulling is not possible until there is a parent location.'))
            return

        branch_from = Branch.open(location)

        if branch_to.get_parent() is None:
            branch_to.set_parent(branch_from.base)

        ret = branch_to.pull(branch_from)
        
        info_dialog(_i18n('Pull successful'), _i18n('%d revision(s) pulled.') % ret)
        
    @show_bzr_error
    def on_menuitem_branch_update_activate(self, widget):
        """ Branch/checkout update menu handler. """
        
        ret = self.wt.update()
        conflicts = self.wt.conflicts()
        if conflicts:
            info_dialog(_i18n('Update successful but conflicts generated'), _i18n('Number of conflicts generated: %d.') % (len(conflicts),) )
        else:
            info_dialog(_i18n('Update successful'), _i18n('No conflicts generated.') )
        self.refresh_right()
    
    def on_menuitem_branch_push_activate(self, widget):
        """ Branch/Push... menu handler. """
        push = PushDialog(repository=None,revid=None,branch=self.wt.branch, parent=self.window)
        response = push.run()
        if response != gtk.RESPONSE_NONE:
            push.destroy()
    
    @show_bzr_error
    def on_menuitem_branch_revert_activate(self, widget):
        """ Branch/Revert all changes menu handler. """
        ret = self.wt.revert(None)
        if ret:
            warning_dialog(_i18n('Conflicts detected'),
                           _i18n('Please have a look at the working tree before continuing.'))
        else:
            info_dialog(_i18n('Revert successful'),
                        _i18n('All files reverted to last revision.'))
        self.refresh_right()
    
    def on_menuitem_branch_status_activate(self, widget):
        """ Branch/Status... menu handler. """
        from bzrlib.plugins.gtk.status import StatusDialog
        status = StatusDialog(self.wt, self.wtpath)
        response = status.run()
        if response != gtk.RESPONSE_NONE:
            status.destroy()
    
    def on_menuitem_branch_initialize_activate(self, widget):
        """ Initialize current directory. """
        init = InitDialog(self.path, self.window)
        response = init.run()
        if response != gtk.RESPONSE_NONE:
            init.hide()
        
            if response == gtk.RESPONSE_OK:
                self.refresh_right()
            
            init.destroy()
        
    def on_menuitem_branch_tags_activate(self, widget):
        """ Branch/Tags... menu handler. """
        from bzrlib.plugins.gtk.tags import TagsWindow
        if not self.remote:
            window = TagsWindow(self.wt.branch, self.window)
        else:
            window = TagsWindow(self.remote_branch, self.window)
        window.show()
    
    def on_menuitem_file_annotate_activate(self, widget):
        """ File/Annotate... menu handler. """
        if self.get_selected_right() is None:
            error_dialog(_i18n('No file was selected'),
                         _i18n('Please select a file from the list.'))
            return
        
        branch = self.wt.branch
        file_id = self.wt.path2id(self.wt.relpath(os.path.join(self.path, self.get_selected_right())))
        
        window = GAnnotateWindow(all=False, plain=False, parent=self.window)
        window.set_title(os.path.join(self.path, self.get_selected_right()) + " - Annotate")
        config = GAnnotateConfig(window)
        window.show()
        branch.lock_read()
        try:
            window.annotate(self.wt, branch, file_id)
        finally:
            branch.unlock()
    
    def on_menuitem_file_bookmark_activate(self, widget):
        """ File/Bookmark current directory menu handler. """
        if self.pref.add_bookmark(self.path):
            info_dialog(_i18n('Bookmark successfully added'),
                        _i18n('The current directory was bookmarked. You can reach\nit by selecting it from the left panel.'))
            self.pref.write()
        else:
            warning_dialog(_i18n('Location already bookmarked'),
                           _i18n('The current directory is already bookmarked.\nSee the left panel for reference.'))
        
        self.refresh_left()
    
    def on_menuitem_file_make_directory_activate(self, widget):
        """ File/Make directory... menu handler. """
        from bzrlib.plugins.gtk.olive.mkdir import MkdirDialog
        mkdir = MkdirDialog(self.wt, self.wtpath, self.window)
        response = mkdir.run()
        mkdir.destroy()
        if response == gtk.RESPONSE_OK:
            self.refresh_right()
    
    def on_menuitem_file_move_activate(self, widget):
        """ File/Move... menu handler. """
        from bzrlib.plugins.gtk.olive.move import MoveDialog
        move = MoveDialog(self.wt, self.wtpath, self.get_selected_right(), self.window)
        response = move.run()
        move.destroy()
        if response == gtk.RESPONSE_OK:
            self.refresh_right()
    
    def on_menuitem_file_rename_activate(self, widget):
        """ File/Rename... menu handler. """
        from bzrlib.plugins.gtk.olive.rename import RenameDialog
        rename = RenameDialog(self.wt, self.wtpath, self.get_selected_right(), self.window)
        response = rename.run()
        rename.destroy()
        if response == gtk.RESPONSE_OK:
            self.refresh_right()

    def on_menuitem_remove_file_activate(self, widget):
        """ Remove (unversion) selected file. """
        from bzrlib.plugins.gtk.olive.remove import RemoveDialog
        remove = RemoveDialog(self.wt, self.wtpath,
                                   selected=self.get_selected_right(),
                                   parent=self.window)
        response = remove.run()
        
        if response != gtk.RESPONSE_NONE:
            remove.hide()
        
            if response == gtk.RESPONSE_OK:
                self.refresh_right()
            
            remove.destroy()
    
    def on_menuitem_stats_diff_activate(self, widget):
        """ Statistics/Differences... menu handler. """
        window = DiffWindow(parent=self.window)
        parent_tree = self.wt.branch.repository.revision_tree(self.wt.branch.last_revision())
        window.set_diff(self.wt.branch._get_nick(local=True), self.wt, 
                        parent_tree)
        window.show()
    
    def on_menuitem_stats_infos_activate(self, widget):
        """ Statistics/Informations... menu handler. """
        from bzrlib.plugins.gtk.olive.info import InfoDialog
        if self.remote:
            info = InfoDialog(self.remote_branch)
        else:
            info = InfoDialog(self.wt.branch)
        info.display()
    
    def on_menuitem_stats_log_activate(self, widget):
        """ Statistics/Log... menu handler. """

        if not self.remote:
            branch = self.wt.branch
        else:
            branch = self.remote_branch

        window = branchwin.BranchWindow(branch, [branch.last_revision()], None, 
                                        parent=self.window)
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
        self.pref.write()
        if self.path is not None:
            self.refresh_right()

    def on_menuitem_view_show_ignored_files_activate(self, widget):
        """ Hide/Show ignored files menu handler. """
        self.pref.set_preference('ignored_files', widget.get_active())
        self.pref.write()
        if self.path is not None:
            self.refresh_right()
            
    def on_treeview_left_button_press_event(self, widget, event):
        """ Occurs when somebody clicks in the bookmark list. """
        treepathpos = widget.get_path_at_pos(int(event.x), int(event.y))
        treeselection = widget.get_selection()
        if treepathpos is not None:
            treeselection.select_path(treepathpos[0])
            if event.button == 1:
                newdir = self.get_selected_left()
                if newdir == None:
                    return

                if self.set_path(newdir):
                    self.refresh_right()
            elif event.button == 3:
                # Don't show context with nothing selected
                if self.get_selected_left() == None:
                    return

                # Create a menu
                from menu import OliveMenu
                menu = OliveMenu(path=self.get_path(),
                                 selected=self.get_selected_left(),
                                 app=self)
                
                menu.left_context_menu().popup(None, None, None, 0,
                                               event.time)
        else:
            if treeselection is not None:
                treeselection.unselect_all()

    def on_treeview_left_row_activated(self, treeview, path, view_column):
        """ Occurs when somebody double-clicks or enters an item in the
        bookmark list. """

        newdir = self.get_selected_left()
        if newdir == None:
            return

        if self.set_path(newdir):
            self.refresh_right()

    def on_treeview_right_button_press_event(self, widget, event):
        """ Occurs when somebody clicks in the file list. """
        treepathpos = widget.get_path_at_pos(int(event.x), int(event.y))
        if event.button == 1:
            if treepathpos is None and widget.get_selection is not None:
                treeselection = widget.get_selection()
                treeselection.unselect_all()
        elif event.button == 3:
            treeselection = widget.get_selection()
            if treepathpos is not None:
                treeselection.select_path(treepathpos[0])
            else:
                if treeselection is not None:
                    treeselection.unselect_all()
            # Create a menu
            from menu import OliveMenu
            menu = OliveMenu(path=self.get_path(),
                             selected=self.get_selected_right(),
                             app=self)
            # get the menu items
            m_open = menu.ui.get_widget('/context_right/open')
            m_add = menu.ui.get_widget('/context_right/add')
            m_remove = menu.ui.get_widget('/context_right/remove')
            m_remove_and_delete = menu.ui.get_widget('/context_right/remove_and_delete')
            m_rename = menu.ui.get_widget('/context_right/rename')
            m_revert = menu.ui.get_widget('/context_right/revert')
            m_commit = menu.ui.get_widget('/context_right/commit')
            m_annotate = menu.ui.get_widget('/context_right/annotate')
            m_diff = menu.ui.get_widget('/context_right/diff')
            # check if we're in a branch
            try:
                from bzrlib.branch import Branch
                Branch.open_containing(self.get_path())
                if self.remote:
                    m_open.set_sensitive(False)
                    m_add.set_sensitive(False)
                    m_remove.set_sensitive(False)
                    m_remove_and_delete.set_sensitive(False)
                    m_rename.set_sensitive(False)
                    m_revert.set_sensitive(False)
                    m_commit.set_sensitive(False)
                    m_annotate.set_sensitive(False)
                    m_diff.set_sensitive(False)
                else:
                    if treepathpos is None:
                        m_open.set_sensitive(False)
                        m_add.set_sensitive(False)
                        m_remove.set_sensitive(False)
                        m_remove_and_delete.set_sensitive(False)
                        m_rename.set_sensitive(False)
                        m_annotate.set_sensitive(False)
                        m_diff.set_sensitive(False)
                        m_revert.set_sensitive(False)
                    else:
                        m_open.set_sensitive(True)
                        m_add.set_sensitive(True)
                        m_remove.set_sensitive(True)
                        m_remove_and_delete.set_sensitive(True)
                        m_rename.set_sensitive(True)
                        m_annotate.set_sensitive(True)
                        m_diff.set_sensitive(True)
                        m_revert.set_sensitive(True)
                    m_commit.set_sensitive(True)
            except bzrerrors.NotBranchError:
                if treepathpos is None:
                    m_open.set_sensitive(False)
                else:
                    m_open.set_sensitive(True)
                m_add.set_sensitive(False)
                m_remove.set_sensitive(False)
                m_remove_and_delete.set_sensitive(False)
                m_rename.set_sensitive(False)
                m_revert.set_sensitive(False)
                m_commit.set_sensitive(False)
                m_annotate.set_sensitive(False)
                m_diff.set_sensitive(False)

            if not self.remote:
                menu.right_context_menu().popup(None, None, None, 0,
                                                event.time)
            else:
                menu.remote_context_menu().popup(None, None, None, 0,
                                                 event.time)
        
    def on_treeview_right_row_activated(self, treeview, path, view_column):
        """ Occurs when somebody double-clicks or enters an item in the
        file list. """
        from launch import launch
        
        newdir = self.get_selected_right()
        
        if not self.remote:
            # We're local
            if newdir == '..':
                self.set_path(os.path.split(self.get_path())[0])
            else:
                fullpath = os.path.join(self.get_path(), newdir)
                if os.path.isdir(fullpath):
                    # selected item is an existant directory
                    self.set_path(fullpath)
                else:
                    launch(fullpath)
        else:
            # We're remote
            if self._is_remote_dir(self.get_path() + newdir):
                self.set_path(self.get_path() + newdir)
        
        self.refresh_right()
    
    def on_window_main_delete_event(self, widget, event=None):
        """ Do some stuff before exiting. """
        width, height = self.window.get_size()
        self.pref.set_preference('window_width', width)
        self.pref.set_preference('window_height', height)
        x, y = self.window.get_position()
        self.pref.set_preference('window_x', x)
        self.pref.set_preference('window_y', y)
        self.pref.set_preference('paned_position',
                                 self.window.hpaned_main.get_position())
        
        self.pref.write()
        self.window.destroy()

    def get_selected_fileid(self):
        """ Get the file_id of the selected file. """
        treeselection = self.window.treeview_right.get_selection()
        (model, iter) = treeselection.get_selected()
        
        if iter is None:
            return None
        else:
            return model.get_value(iter, 9)
    
    def get_selected_right(self):
        """ Get the selected filename. """
        treeselection = self.window.treeview_right.get_selection()
        (model, iter) = treeselection.get_selected()
        
        if iter is None:
            return None
        else:
            return model.get_value(iter, 2)
    
    def get_selected_left(self):
        """ Get the selected bookmark. """
        treeselection = self.window.treeview_left.get_selection()
        (model, iter) = treeselection.get_selected()
        
        if iter is None:
            return None
        else:
            return model.get_value(iter, 1)

    def set_statusbar(self, message):
        """ Set the statusbar message. """
        self.window.statusbar.push(self.context_id, message)
    
    def clear_statusbar(self):
        """ Clean the last message from the statusbar. """
        self.window.statusbar.pop(self.context_id)
    
    def set_sensitivity(self):
        """ Set menu and toolbar sensitivity. """
        if not self.remote:
            self.window.set_view_to_localbranch(self.notbranch)
        else:
            self.window.set_view_to_remotebranch()
    
    def refresh_left(self):
        """ Refresh the bookmark list. """
        
        # Get ListStore and clear it
        liststore = self.window.bookmarklist
        liststore.clear()

        # Re-read preferences
        self.pref.read()
        
        # Get bookmarks
        bookmarks = self.pref.get_bookmarks()

        # Get titles and sort by title
        bookmarks = [[self.pref.get_bookmark_title(item), item, gtk.STOCK_DIRECTORY] for item in bookmarks]
        bookmarks.sort()
        for title_item in bookmarks:
            liststore.append(title_item)
        
        # Add the ListStore to the TreeView and refresh column width
        self.window.treeview_left.set_model(liststore)
        self.window.treeview_left.columns_autosize()

    def refresh_right(self):
        """ Refresh the file list. """
        if not self.remote:
            # We're local
            from bzrlib.workingtree import WorkingTree
            
            path = self.get_path()
            
            # Get ListStore and clear it
            liststore = self.window.filelist
            liststore.clear()
            
            dirs = []
            files = []
            
            # Fill the appropriate lists
            dotted_files = self.pref.get_preference('dotted_files', 'bool')
            ignored_files = self.pref.get_preference('ignored_files', 'bool')
            
            for item in os.listdir(path):
                if not dotted_files and item[0] == '.':
                    continue
                if os.path.isdir(os.path.join(path, item)):
                    dirs.append(item)
                else:
                    files.append(item)
            
            self.window.col_status.set_visible(False)
            if not self.notbranch:
                try:
                    tree1 = WorkingTree.open_containing(os.path.realpath(path))[0]
                    branch = tree1.branch
                    tree2 = tree1.branch.repository.revision_tree(branch.last_revision())
                    
                    delta = tree1.changes_from(tree2, want_unchanged=True)
                    
                    # Show Status column
                    self.window.col_status.set_visible(True)
                except bzrerrors.LockContention:
                    self.window.set_location_status(gtk.STOCK_DIALOG_ERROR, allowPopup=True)
                    self.window.location_status.connect_object('clicked', error_dialog, 
                                       *(_i18n('Branch is locked'),
                                		_i18n('The branch in the current folder is locked by another Bazaar program')))
                    self.notbranch = True
                    self.window.set_view_to_localbranch(False) 
            
            # Add'em to the ListStore
            for item in dirs:
                status = ''
                st = ''
                fileid = ''
                if not self.notbranch:
                    filename = tree1.relpath(os.path.join(os.path.realpath(path), item))
                    
                    st, status = self.statusmapper(filename, delta)
                    if not ignored_files and status == 'ignored':
                        continue
                
                statinfo = os.lstat(os.path.join(self.path, item))
                liststore.append([ gtk.STOCK_DIRECTORY,
                                   True,
                                   item,
                                   st,
                                   status,
                                   "<DIR>",
                                   "<DIR>",
                                   statinfo.st_mtime,
                                   self._format_date(statinfo.st_mtime),
                                   ''])
            for item in files:
                status = ''
                st = ''
                fileid = ''
                if not self.notbranch:
                    filename = tree1.relpath(os.path.join(os.path.realpath(path), item))
                    
                    st, status = self.statusmapper(filename, delta)
                    if not ignored_files and status == 'ignored':
                        continue
                
                statinfo = os.lstat(os.path.join(self.path, item))
                liststore.append([gtk.STOCK_FILE,
                                  False,
                                  item,
                                  st,
                                  status,
                                  str(statinfo.st_size),
                                  self._format_size(statinfo.st_size),
                                  statinfo.st_mtime,
                                  self._format_date(statinfo.st_mtime),
                                  fileid])
        else:
            # We're remote
            
            # Get ListStore and clear it
            liststore = self.window.filelist
            liststore.clear()
            
            # Hide Status column
            self.window.col_status.set_visible(False)
            
            dirs = []
            files = []
            
            self.window.set_location_status(gtk.STOCK_REFRESH)
            
            for (name, type) in self.remote_entries:
                if type.kind == 'directory':
                    dirs.append(type)
                elif type.kind == 'file':
                    files.append(type)
            
            class HistoryCache:
                """ Cache based on revision history. """
                def __init__(self, history):
                    self._history = history
                
                def _lookup_revision(self, revid):
                    for r in self._history:
                        if r.revision_id == revid:
                            return r
                    rev = repo.get_revision(revid)
                    self._history.append(rev)
                    return rev
            
            repo = self.remote_branch.repository
            
            revhistory = self.remote_branch.revision_history()
            try:
                revs = repo.get_revisions(revhistory)
                cache = HistoryCache(revs)
            except bzrerrors.InvalidHttpResponse:
                # Fallback to dummy algorithm, because of LP: #115209
                cache = HistoryCache([])
            
            for item in dirs:
                if item.parent_id == self.remote_parent:
                    rev = cache._lookup_revision(item.revision)
                    liststore.append([ gtk.STOCK_DIRECTORY,
                                       True,
                                       item.name,
                                       '',
                                       '',
                                       "<DIR>",
                                       "<DIR>",
                                       rev.timestamp,
                                       self._format_date(rev.timestamp),
                                       ''
                                   ])
                while gtk.events_pending():
                    gtk.main_iteration()
            
            for item in files:
                if item.parent_id == self.remote_parent:
                    rev = cache._lookup_revision(item.revision)
                    liststore.append([ gtk.STOCK_FILE,
                                       False,
                                       item.name,
                                       '',
                                       '',
                                       str(item.text_size),
                                       self._format_size(item.text_size),
                                       rev.timestamp,
                                       self._format_date(rev.timestamp),
                                       item.file_id
                                   ])
                while gtk.events_pending():
                    gtk.main_iteration()
            
            self.window.location_status.destroy()

        # Columns should auto-size
        self.window.treeview_right.columns_autosize()
        
        # Set sensitivity
        self.set_sensitivity()
    
    def statusmapper(self, filename, delta):
        status = 'unknown'
        try:
            self.wt.lock_read()
            
            for rpath, rpathnew, id, kind, text_modified, meta_modified in delta.renamed:
                if rpathnew == filename:
                    status = 'renamed'
                    fileid = id
            for rpath, id, kind in delta.added:
                if rpath == filename:
                    status = 'added'
                    fileid = id
            for rpath, id, kind in delta.removed:
                if rpath == filename:
                    status = 'removed'
                    fileid = id
            for rpath, id, kind, text_modified, meta_modified in delta.modified:
                if rpath == filename:
                    status = 'modified'
                    fileid = id
            for rpath, id, kind in delta.unchanged:
                if rpath == filename:
                    status = 'unchanged'
                    fileid = id
            for rpath, file_class, kind, id, entry in self.wt.list_files():
                if rpath == filename and file_class == 'I':
                    status = 'ignored'
        finally:
            self.wt.unlock()
    
        if status == 'renamed':
            st = _i18n('renamed')
        elif status == 'removed':
            st = _i18n('removed')
        elif status == 'added':
            st = _i18n('added')
        elif status == 'modified':
            st = _i18n('modified')
        elif status == 'unchanged':
            st = _i18n('unchanged')
        elif status == 'ignored':
            st = _i18n('ignored')
        else:
            st = _i18n('unknown')
        return st, status

    def _harddisks(self):
        """ Returns hard drive letters under Win32. """
        try:
            import win32file
            import string
        except ImportError:
            if sys.platform == 'win32':
                print "pyWin32 modules needed to run Olive on Win32."
                sys.exit(1)
        
        driveletters = []
        for drive in string.ascii_uppercase:
            if win32file.GetDriveType(drive+':') == win32file.DRIVE_FIXED or\
                win32file.GetDriveType(drive+':') == win32file.DRIVE_REMOTE or\
                win32file.GetDriveType(drive+':') == win32file.DRIVE_REMOVABLE:
                driveletters.append(drive+':')
        return driveletters
    
    def gen_hard_selector(self):
        """ Generate the hard drive selector under Win32. """
        drives = self._harddisks()
        for drive in drives:
            self.combobox_drive.append_text(drive)
        self.combobox_drive.set_active(drives.index(os.getcwd()[0:2]))
    
    def _refresh_drives(self, combobox):
        if self._just_started:
            return
        model = combobox.get_model()
        active = combobox.get_active()
        if active >= 0:
            drive = model[active][0]
            self.set_path(drive + '\\')
            self.refresh_right()
    
    def check_for_changes(self):
        """ Check whether there were changes in the current working tree. """
        old_tree = self.wt.branch.repository.revision_tree(self.wt.branch.last_revision())
        delta = self.wt.changes_from(old_tree)

        changes = False
        
        if len(delta.added) or len(delta.removed) or len(delta.renamed) or len(delta.modified):
            changes = True
        
        return changes
    
    def _sort_filelist_callback(self, model, iter1, iter2, data):
        """ The sort callback for the file list, return values:
        -1: iter1 < iter2
        0: iter1 = iter2
        1: iter1 > iter2
        """
        name1 = model.get_value(iter1, 2)
        name2 = model.get_value(iter2, 2)
        
        if model.get_value(iter1, 1):
            # item1 is a directory
            if not model.get_value(iter2, 1):
                # item2 isn't
                return -1
            else:
                # both of them are directories, we compare their names
                if name1 < name2:
                    return -1
                elif name1 == name2:
                    return 0
                else:
                    return 1
        else:
            # item1 is not a directory
            if model.get_value(iter2, 1):
                # item2 is
                return 1
            else:
                # both of them are files, compare them
                if name1 < name2:
                    return -1
                elif name1 == name2:
                    return 0
                else:
                    return 1
    
    def _format_size(self, size):
        """ Format size to a human readable format. """
        if size < 1000:
            return "%d[B]" % (size,)
        size = size / 1000.0
        
        for metric in ["kB","MB","GB","TB"]:
            if size < 1000:
                break
            size = size / 1000.0
        return "%.1f[%s]" % (size,metric) 
    
    def _format_date(self, timestamp):
        """ Format the time (given in secs) to a human readable format. """
        return time.ctime(timestamp)
    
    def _is_remote_dir(self, location):
        """ Determine whether the given location is a directory or not. """
        if not self.remote:
            # We're in local mode
            return False
        else:
            branch, path = Branch.open_containing(location)
            for (name, type) in self.remote_entries:
                if name == path and type.kind == 'directory':
                    # We got it
                    return True
            # Either it's not a directory or not in the inventory
            return False

import ConfigParser

class Preferences:
    """ A class which handles Olive's preferences. """
    def __init__(self, path=None):
        """ Initialize the Preferences class. """
        # Some default options
        self.defaults = { 'strict_commit' : False,
                          'dotted_files'  : False,
                          'ignored_files' : True,
                          'window_width'  : 700,
                          'window_height' : 400,
                          'window_x'      : 40,
                          'window_y'      : 40,
                          'paned_position': 200 }

        # Create a config parser object
        self.config = ConfigParser.RawConfigParser()

        # Set filename
        if path is None:
            if sys.platform == 'win32':
                # Windows - no dotted files
                self._filename = os.path.expanduser('~/olive.conf')
            else:
                self._filename = os.path.expanduser('~/.olive.conf')
        else:
            self._filename = path
        
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
        # Re-initialize the config parser object to avoid some bugs
        self.config = ConfigParser.RawConfigParser()
        self.config.read([self._filename])
    
    def write(self):
        """ Write the configuration to the appropriate files. """
        fp = open(self._filename, 'w')
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
        # FIXME: What if path isn't listed yet?
        # FIXME: Canonicalize paths first?
        self.config.set(path, 'title', title)
    
    def remove_bookmark(self, path):
        """ Remove bookmark. """
        return self.config.remove_section(path)

    def set_preference(self, option, value):
        """ Set the value of the given option. """
        if value is True:
            value = 'yes'
        elif value is False:
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
