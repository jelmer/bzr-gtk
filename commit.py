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
import gobject
import pango

import os.path
import re

from bzrlib import errors, osutils
from bzrlib.trace import mutter

from dialog import error_dialog, question_dialog
from errors import show_bzr_error

try:
    import dbus
    import dbus.glib
    have_dbus = True
except ImportError:
    have_dbus = False


def pending_revisions(wt):
    """Return a list of pending merges or None if there are none of them.

    Arguably this should be a core function, and
    ``bzrlib.status.show_pending_merges`` should be built on top of it.

    :return: [(rev, [children])]
    """
    parents = wt.get_parent_ids()
    if len(parents) < 2:
        return None

    # The basic pending merge algorithm uses the same algorithm as
    # bzrlib.status.show_pending_merges
    pending = parents[1:]
    branch = wt.branch
    last_revision = parents[0]

    if last_revision is not None:
        try:
            ignore = set(branch.repository.get_ancestry(last_revision,
                                                        topo_sorted=False))
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
            rev = branch.repository.get_revision(merge)
            children = []
            pm.append((rev, children))

            # This does need to be topo sorted, so we search backwards
            inner_merges = branch.repository.get_ancestry(merge)
            assert inner_merges[0] is None
            inner_merges.pop(0)
            for mmerge in reversed(inner_merges):
                if mmerge in ignore:
                    continue
                rev = branch.repository.get_revision(mmerge)
                children.append(rev)

                ignore.add(mmerge)
        except errors.NoSuchRevision:
            print "DEBUG: NoSuchRevision:", merge

    return pm


class CommitDialog(gtk.Dialog):
    """Implementation of Commit."""

    def __init__(self, wt, selected=None, parent=None):
         gtk.Dialog.__init__(self, title="Commit - Olive",
                                   parent=parent,
                                   flags=0,
                                   buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
         self._wt = wt
         self._selected = selected

         self.setup_params()
         self.construct()
         self.set_default_size(800, 600)

    def setup_params(self):
        """Setup the member variables for state."""
        self._basis_tree = self._wt.basis_tree()
        self._delta = self._wt.changes_from(self._basis_tree)

        self._pending = pending_revisions(self._wt)

        self._is_checkout = (self._wt.branch.get_bound_location() is not None)

    def construct(self):
        """Build up the dialog widgets."""
        # The primary pane which splits it into left and right (adjustable)
        # sections.
        self._hpane = gtk.HPaned()

        self._construct_left_pane()
        self._construct_right_pane()

        self.vbox.pack_start(self._hpane)
        self._hpane.show()
        self.set_focus(self._global_message_text_view)

    def _construct_left_pane(self):
        self._left_pane_box = gtk.VBox(homogeneous=False, spacing=3)
        self._construct_file_list()
        self._construct_pending_list()

        self._pending_box.show()
        self._hpane.pack1(self._left_pane_box, resize=False, shrink=True)
        self._left_pane_box.show()

    def _construct_right_pane(self):
        # TODO: I really want to make it so the diff view gets more space than
        # the global commit message, and the per-file commit message gets even
        # less. When I did it with wxGlade, I set it to 4 for diff, 2 for
        # commit, and 1 for file commit, and it looked good. But I don't seem
        # to have a way to do that with the gtk boxes... :( (Which is extra
        # weird since wx uses gtk on Linux...)
        self._right_pane_box = gtk.VBox(homogeneous=False, spacing=3)
        self._construct_diff_view()
        self._construct_file_message()
        self._construct_global_message()

        self._right_pane_box.show()
        self._hpane.pack2(self._right_pane_box, resize=True, shrink=True)

    def _construct_file_list(self):
        self._files_box = gtk.VBox()
        file_label = gtk.Label()
        file_label.set_markup(_('<b>Files</b>'))
        file_label.show()
        self._files_box.pack_start(file_label, expand=False)

        scroller = gtk.ScrolledWindow()
        scroller.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self._treeview_files = gtk.TreeView()
        self._treeview_files.show()
        scroller.add(self._treeview_files)
        scroller.show()
        scroller.set_shadow_type(gtk.SHADOW_IN)
        self._files_box.pack_start(scroller,
                                   expand=True, fill=True)
        self._files_box.show()
        self._left_pane_box.pack_start(self._files_box)

    def _construct_pending_list(self):
        # Pending information defaults to hidden, we put it all in 1 box, so
        # that we can show/hide all of them at once
        self._pending_box = gtk.VBox()
        self._pending_box.hide()

        # TODO: This message should be centered
        pending_message = gtk.Label()
        pending_message.set_markup(
            _('<i>Cannot select specific files when merging</i>'))
        self._pending_box.pack_start(pending_message, expand=False)
        pending_message.show()

        pending_label = gtk.Label()
        pending_label.set_markup(_('<b>Pending Revisions</b>'))
        self._pending_box.pack_start(pending_label, expand=False)
        pending_label.show()

        scroller = gtk.ScrolledWindow()
        scroller.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self._treeview_pending = gtk.TreeView()
        scroller.add(self._treeview_pending)
        scroller.show()
        scroller.set_shadow_type(gtk.SHADOW_IN)
        self._pending_box.pack_start(scroller,
                                     expand=True, fill=True)
        self._treeview_pending.show()
        self._left_pane_box.pack_start(self._pending_box)

    def _construct_diff_view(self):
        from diff import DiffDisplay

        self._diff_label = gtk.Label(_('Diff for whole tree'))
        self._right_pane_box.pack_start(self._diff_label, expand=False)
        self._diff_label.show()

        self._diff_view = DiffDisplay()
        # self._diff_display.set_trees(self.wt, self.wt.basis_tree())
        # self._diff_display.show_diff(None)
        self._right_pane_box.pack_start(self._diff_view,
                                        expand=True, fill=True)
        self._diff_view.show()

    def _construct_file_message(self):
        file_message_box = gtk.VBox()
        scroller = gtk.ScrolledWindow()
        scroller.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        self._file_message_text_view = gtk.TextView()
        scroller.add(self._file_message_text_view)
        scroller.show()
        scroller.set_shadow_type(gtk.SHADOW_IN)
        file_message_box.pack_start(scroller, expand=True, fill=True)

        self._file_message_text_view.modify_font(pango.FontDescription("Monospace"))
        self._file_message_text_view.set_wrap_mode(gtk.WRAP_WORD)
        self._file_message_text_view.set_accepts_tab(False)
        self._file_message_text_view.show()

        self._file_message_expander = gtk.Expander(_('Message for XXX'))
        self._file_message_expander.add(file_message_box)
        file_message_box.show()
        # When expanded, we want to change expand=True, so that the message box
        # gets more space. But when it is shrunk, it has nothing to do with
        # that space, so we start it at expand=False
        self._right_pane_box.pack_start(self._file_message_expander,
                                        expand=False, fill=True)
        self._file_message_expander.connect('notify::expanded',
                                            self._expand_file_message_callback)
        self._file_message_expander.show()

    def _expand_file_message_callback(self, expander, param_spec):
        if expander.get_expanded():
            self._right_pane_box.set_child_packing(expander,
                expand=True, fill=True, padding=0, pack_type=gtk.PACK_START)
        else:
            self._right_pane_box.set_child_packing(expander,
                expand=False, fill=True, padding=0, pack_type=gtk.PACK_START)

    def _construct_global_message(self):
        self._global_message_label = gtk.Label(_('Global Commit Message'))
        self._right_pane_box.pack_start(self._global_message_label, expand=False)
        self._global_message_label.show()

        scroller = gtk.ScrolledWindow()
        scroller.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        self._global_message_text_view = gtk.TextView()
        self._global_message_text_view.modify_font(pango.FontDescription("Monospace"))
        scroller.add(self._global_message_text_view)
        scroller.show()
        scroller.set_shadow_type(gtk.SHADOW_IN)
        self._right_pane_box.pack_start(scroller,
                                        expand=True, fill=True)
        self._file_message_text_view.set_wrap_mode(gtk.WRAP_WORD)
        self._file_message_text_view.set_accepts_tab(False)
        self._global_message_text_view.show()

    @staticmethod
    def _rev_to_pending_info(rev):
        """Get the information from a pending merge."""
        from bzrlib.osutils import format_date

        rev_dict = {}
        rev_dict['committer'] = re.sub('<.*@.*>', '', rev.committer).strip(' ')
        rev_dict['summary'] = rev.get_summary()
        rev_dict['date'] = format_date(rev.timestamp,
                                       rev.timezone or 0,
                                       'original', date_fmt="%Y-%m-%d",
                                       show_offset=False)
        rev_dict['revision_id'] = rev.revision_id
        return rev_dict


# class CommitDialog(gtk.Dialog):
#     """ New implementation of the Commit dialog. """
#     def __init__(self, wt, wtpath, notbranch, selected=None, parent=None):
#         """ Initialize the Commit Dialog. """
#         gtk.Dialog.__init__(self, title="Commit - Olive",
#                                   parent=parent,
#                                   flags=0,
#                                   buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
#         
#         # Get arguments
#         self.wt = wt
#         self.wtpath = wtpath
#         self.notbranch = notbranch
#         self.selected = selected
#         
#         # Set the delta
#         self.old_tree = self.wt.branch.repository.revision_tree(self.wt.branch.last_revision())
#         self.delta = self.wt.changes_from(self.old_tree)
#         
#         # Get pending merges
#         self.pending = self._pending_merges(self.wt)
#         
#         # Do some preliminary checks
#         self._is_checkout = False
#         self._is_pending = False
#         if self.wt is None and not self.notbranch:
#             error_dialog(_('Directory does not have a working tree'),
#                          _('Operation aborted.'))
#             self.close()
#             return
# 
#         if self.notbranch:
#             error_dialog(_('Directory is not a branch'),
#                          _('You can perform this action only in a branch.'))
#             self.close()
#             return
#         else:
#             if self.wt.branch.get_bound_location() is not None:
#                 # we have a checkout, so the local commit checkbox must appear
#                 self._is_checkout = True
#             
#             if self.pending:
#                 # There are pending merges, file selection not supported
#                 self._is_pending = True
#         
#         # Create the widgets
#         # This is the main horizontal box, which is used to separate the commit
#         # info from the diff window.
#         self._hpane = gtk.HPaned()
#         self._button_commit = gtk.Button(_("Comm_it"), use_underline=True)
#         self._expander_files = gtk.Expander(_("File(s) to commit"))
#         self._vpaned_main = gtk.VPaned()
#         self._scrolledwindow_files = gtk.ScrolledWindow()
#         self._scrolledwindow_message = gtk.ScrolledWindow()
#         self._treeview_files = gtk.TreeView()
#         self._vbox_message = gtk.VBox()
#         self._label_message = gtk.Label(_("Commit message:"))
#         self._textview_message = gtk.TextView()
#         
#         if self._is_pending:
#             self._expander_merges = gtk.Expander(_("Pending merges"))
#             self._vpaned_list = gtk.VPaned()
#             self._scrolledwindow_merges = gtk.ScrolledWindow()
#             self._treeview_merges = gtk.TreeView()
# 
#         # Set callbacks
#         self._button_commit.connect('clicked', self._on_commit_clicked)
#         self._treeview_files.connect('cursor-changed', self._on_treeview_files_cursor_changed)
#         self._treeview_files.connect('row-activated', self._on_treeview_files_row_activated)
#         
#         # Set properties
#         self._scrolledwindow_files.set_policy(gtk.POLICY_AUTOMATIC,
#                                               gtk.POLICY_AUTOMATIC)
#         self._scrolledwindow_message.set_policy(gtk.POLICY_AUTOMATIC,
#                                                 gtk.POLICY_AUTOMATIC)
#         self._textview_message.modify_font(pango.FontDescription("Monospace"))
#         self.set_default_size(500, 500)
#         self._vpaned_main.set_position(200)
#         self._button_commit.set_flags(gtk.CAN_DEFAULT)
# 
#         if self._is_pending:
#             self._scrolledwindow_merges.set_policy(gtk.POLICY_AUTOMATIC,
#                                                    gtk.POLICY_AUTOMATIC)
#             self._treeview_files.set_sensitive(False)
#         
#         # Construct the dialog
#         self.action_area.pack_end(self._button_commit)
#         
#         self._scrolledwindow_files.add(self._treeview_files)
#         self._scrolledwindow_message.add(self._textview_message)
#         
#         self._expander_files.add(self._scrolledwindow_files)
#         
#         self._vbox_message.pack_start(self._label_message, False, False)
#         self._vbox_message.pack_start(self._scrolledwindow_message, True, True)
#         
#         if self._is_pending:        
#             self._expander_merges.add(self._scrolledwindow_merges)
#             self._scrolledwindow_merges.add(self._treeview_merges)
#             self._vpaned_list.add1(self._expander_files)
#             self._vpaned_list.add2(self._expander_merges)
#             self._vpaned_main.add1(self._vpaned_list)
#         else:
#             self._vpaned_main.add1(self._expander_files)
# 
#         self._vpaned_main.add2(self._vbox_message)
#         
#         self._hpane.pack1(self._vpaned_main)
#         self.vbox.pack_start(self._hpane, expand=True, fill=True)
#         if self._is_checkout: 
#             self._check_local = gtk.CheckButton(_("_Only commit locally"),
#                                                 use_underline=True)
#             self.vbox.pack_start(self._check_local, False, False)
#             if have_dbus:
#                 bus = dbus.SystemBus()
#                 proxy_obj = bus.get_object('org.freedesktop.NetworkManager', 
#                               '/org/freedesktop/NetworkManager')
#                 dbus_iface = dbus.Interface(
#                         proxy_obj, 'org.freedesktop.NetworkManager')
#                 try:
#                     # 3 is the enum value for STATE_CONNECTED
#                     self._check_local.set_active(dbus_iface.state() != 3)
#                 except dbus.DBusException, e:
#                     # Silently drop errors. While DBus may be 
#                     # available, NetworkManager doesn't necessarily have to be
#                     mutter("unable to get networkmanager state: %r" % e)
#                 
#         # Create the file list
#         self._create_file_view()
#         # Create the pending merges
#         self._create_pending_merges()
#         self._create_diff_view()
#         
#         # Expand the corresponding expander
#         if self._is_pending:
#             self._expander_merges.set_expanded(True)
#         else:
#             self._expander_files.set_expanded(True)
#         
#         # Display dialog
#         self.vbox.show_all()
#         
#         # Default to Commit button
#         self._button_commit.grab_default()
#     
#     def _show_diff_view(self, treeview):
#         # FIXME: the diff window freezes for some reason
#         treeselection = treeview.get_selection()
#         (model, iter) = treeselection.get_selected()
# 
#         if iter is not None:
#             selected = model.get_value(iter, 3) # Get the real_path attribute
#             self._diff_display.show_diff([selected])
# 
#     def _on_treeview_files_cursor_changed(self, treeview):
#         self._show_diff_view(treeview)
#         
#     def _on_treeview_files_row_activated(self, treeview, path, view_column):
#         self._show_diff_view(treeview)
#     
#     @show_bzr_error
#     def _on_commit_clicked(self, button):
#         """ Commit button clicked handler. """
#         textbuffer = self._textview_message.get_buffer()
#         start, end = textbuffer.get_bounds()
#         message = textbuffer.get_text(start, end).decode('utf-8')
#         
#         if not self.pending:
#             specific_files = self._get_specific_files()
#         else:
#             specific_files = None
# 
#         if message == '':
#             response = question_dialog(_('Commit with an empty message?'),
#                                        _('You can describe your commit intent in the message.'))
#             if response == gtk.RESPONSE_NO:
#                 # Kindly give focus to message area
#                 self._textview_message.grab_focus()
#                 return
# 
#         if self._is_checkout:
#             local = self._check_local.get_active()
#         else:
#             local = False
# 
#         if list(self.wt.unknowns()) != []:
#             response = question_dialog(_("Commit with unknowns?"),
#                _("Unknown files exist in the working tree. Commit anyway?"))
#             if response == gtk.RESPONSE_NO:
#                 return
#         
#         try:
#             self.wt.commit(message,
#                        allow_pointless=False,
#                        strict=False,
#                        local=local,
#                        specific_files=specific_files)
#         except errors.PointlessCommit:
#             response = question_dialog(_('Commit with no changes?'),
#                                        _('There are no changes in the working tree.'))
#             if response == gtk.RESPONSE_YES:
#                 self.wt.commit(message,
#                                allow_pointless=True,
#                                strict=False,
#                                local=local,
#                                specific_files=specific_files)
#         self.response(gtk.RESPONSE_OK)
# 
#     def _pending_merges(self, wt):
#         """ Return a list of pending merges or None if there are none of them. """
#         parents = wt.get_parent_ids()
#         if len(parents) < 2:
#             return None
#         
#         import re
#         from bzrlib.osutils import format_date
#         
#         pending = parents[1:]
#         branch = wt.branch
#         last_revision = parents[0]
#         
#         if last_revision is not None:
#             try:
#                 ignore = set(branch.repository.get_ancestry(last_revision))
#             except errors.NoSuchRevision:
#                 # the last revision is a ghost : assume everything is new 
#                 # except for it
#                 ignore = set([None, last_revision])
#         else:
#             ignore = set([None])
#         
#         pm = []
#         for merge in pending:
#             ignore.add(merge)
#             try:
#                 m_revision = branch.repository.get_revision(merge)
#                 
#                 rev = {}
#                 rev['committer'] = re.sub('<.*@.*>', '', m_revision.committer).strip(' ')
#                 rev['summary'] = m_revision.get_summary()
#                 rev['date'] = format_date(m_revision.timestamp,
#                                           m_revision.timezone or 0, 
#                                           'original', date_fmt="%Y-%m-%d",
#                                           show_offset=False)
#                 
#                 pm.append(rev)
#                 
#                 inner_merges = branch.repository.get_ancestry(merge)
#                 assert inner_merges[0] is None
#                 inner_merges.pop(0)
#                 inner_merges.reverse()
#                 for mmerge in inner_merges:
#                     if mmerge in ignore:
#                         continue
#                     mm_revision = branch.repository.get_revision(mmerge)
#                     
#                     rev = {}
#                     rev['committer'] = re.sub('<.*@.*>', '', mm_revision.committer).strip(' ')
#                     rev['summary'] = mm_revision.get_summary()
#                     rev['date'] = format_date(mm_revision.timestamp,
#                                               mm_revision.timezone or 0, 
#                                               'original', date_fmt="%Y-%m-%d",
#                                               show_offset=False)
#                 
#                     pm.append(rev)
#                     
#                     ignore.add(mmerge)
#             except errors.NoSuchRevision:
#                 print "DEBUG: NoSuchRevision:", merge
#         
#         return pm
# 
#     def _create_file_view(self):
#         self._file_store = gtk.ListStore(gobject.TYPE_BOOLEAN,   # [0] checkbox
#                                          gobject.TYPE_STRING,    # [1] path to display
#                                          gobject.TYPE_STRING,    # [2] changes type
#                                          gobject.TYPE_STRING)    # [3] real path
#         self._treeview_files.set_model(self._file_store)
#         crt = gtk.CellRendererToggle()
#         crt.set_property("activatable", True)
#         crt.connect("toggled", self._toggle_commit, self._file_store)
#         self._treeview_files.append_column(gtk.TreeViewColumn(_('Commit'),
#                                      crt, active=0))
#         self._treeview_files.append_column(gtk.TreeViewColumn(_('Path'),
#                                      gtk.CellRendererText(), text=1))
#         self._treeview_files.append_column(gtk.TreeViewColumn(_('Type'),
#                                      gtk.CellRendererText(), text=2))
# 
#         for path, id, kind in self.delta.added:
#             marker = osutils.kind_marker(kind)
#             if self.selected is not None:
#                 if path == os.path.join(self.wtpath, self.selected):
#                     self._file_store.append([ True, path+marker, _('added'), path ])
#                 else:
#                     self._file_store.append([ False, path+marker, _('added'), path ])
#             else:
#                 self._file_store.append([ True, path+marker, _('added'), path ])
# 
#         for path, id, kind in self.delta.removed:
#             marker = osutils.kind_marker(kind)
#             if self.selected is not None:
#                 if path == os.path.join(self.wtpath, self.selected):
#                     self._file_store.append([ True, path+marker, _('removed'), path ])
#                 else:
#                     self._file_store.append([ False, path+marker, _('removed'), path ])
#             else:
#                 self._file_store.append([ True, path+marker, _('removed'), path ])
# 
#         for oldpath, newpath, id, kind, text_modified, meta_modified in self.delta.renamed:
#             marker = osutils.kind_marker(kind)
#             if text_modified or meta_modified:
#                 changes = _('renamed and modified')
#             else:
#                 changes = _('renamed')
#             if self.selected is not None:
#                 if newpath == os.path.join(self.wtpath, self.selected):
#                     self._file_store.append([ True,
#                                               oldpath+marker + '  =>  ' + newpath+marker,
#                                               changes,
#                                               newpath
#                                             ])
#                 else:
#                     self._file_store.append([ False,
#                                               oldpath+marker + '  =>  ' + newpath+marker,
#                                               changes,
#                                               newpath
#                                             ])
#             else:
#                 self._file_store.append([ True,
#                                           oldpath+marker + '  =>  ' + newpath+marker,
#                                           changes,
#                                           newpath
#                                         ])
# 
#         for path, id, kind, text_modified, meta_modified in self.delta.modified:
#             marker = osutils.kind_marker(kind)
#             if self.selected is not None:
#                 if path == os.path.join(self.wtpath, self.selected):
#                     self._file_store.append([ True, path+marker, _('modified'), path ])
#                 else:
#                     self._file_store.append([ False, path+marker, _('modified'), path ])
#             else:
#                 self._file_store.append([ True, path+marker, _('modified'), path ])
#     
#     def _create_pending_merges(self):
#         if not self.pending:
#             return
#         
#         liststore = gtk.ListStore(gobject.TYPE_STRING,
#                                   gobject.TYPE_STRING,
#                                   gobject.TYPE_STRING)
#         self._treeview_merges.set_model(liststore)
#         
#         self._treeview_merges.append_column(gtk.TreeViewColumn(_('Date'),
#                                             gtk.CellRendererText(), text=0))
#         self._treeview_merges.append_column(gtk.TreeViewColumn(_('Committer'),
#                                             gtk.CellRendererText(), text=1))
#         self._treeview_merges.append_column(gtk.TreeViewColumn(_('Summary'),
#                                             gtk.CellRendererText(), text=2))
#         
#         for item in self.pending:
#             liststore.append([ item['date'],
#                                item['committer'],
#                                item['summary'] ])
#     
# 
#     def _create_diff_view(self):
#         from diff import DiffDisplay
# 
#         self._diff_display = DiffDisplay()
#         self._diff_display.set_trees(self.wt, self.wt.basis_tree())
#         self._diff_display.show_diff(None)
#         self._diff_display.show()
#         self._hpane.pack2(self._diff_display)
# 
#     def _get_specific_files(self):
#         ret = []
#         it = self._file_store.get_iter_first()
#         while it:
#             if self._file_store.get_value(it, 0):
#                 # get real path from hidden column 3
#                 ret.append(self._file_store.get_value(it, 3))
#             it = self._file_store.iter_next(it)
# 
#         return ret
#     
#     def _toggle_commit(self, cell, path, model):
#         model[path][0] = not model[path][0]
#         return
