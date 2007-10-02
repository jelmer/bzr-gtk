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
        self.fill_in_data()

    def setup_params(self):
        """Setup the member variables for state."""
        self._basis_tree = self._wt.basis_tree()
        self._delta = None
        self._pending = pending_revisions(self._wt)

        self._is_checkout = (self._wt.branch.get_bound_location() is not None)

    def fill_in_data(self):
        # Now that we are built, handle changes to the view based on the state
        self._fill_in_pending()
        self._fill_in_diff()
        self._fill_in_files()

    def _fill_in_pending(self):
        if not self._pending:
            self._pending_box.hide()
            return

        # TODO: We'd really prefer this to be a nested list
        for rev, children in self._pending:
            rev_info = self._rev_to_pending_info(rev)
            self._pending_store.append([
                rev_info['revision_id'],
                rev_info['date'],
                rev_info['committer'],
                rev_info['summary'],
                ])
            for child in children:
                rev_info = self._rev_to_pending_info(child)
                self._pending_store.append([
                    rev_info['revision_id'],
                    rev_info['date'],
                    rev_info['committer'],
                    rev_info['summary'],
                    ])
        self._pending_box.show()

    def _fill_in_files(self):
        # We should really use _iter_changes, and then add a progress bar of
        # some kind.
        # While we fill in the view, hide the store
        store = self._files_store
        self._treeview_files.set_model(None)

        added = _('added')
        removed = _('removed')
        renamed = _('renamed')
        renamed_and_modified = _('renamed and modified')
        modified = _('modified')
        kind_changed = _('kind changed')

        # The store holds:
        # [file_id, real path, checkbox, display path, changes type, message]
        # _iter_changes returns:
        # (file_id, (path_in_source, path_in_target),
        #  changed_content, versioned, parent, name, kind,
        #  executable)

        # The first entry is always the 'whole tree'
        store.append([None, None, True, 'All Files', '', ''])
        # should we pass specific_files?
        self._wt.lock_read()
        self._basis_tree.lock_read()
        try:
            for (file_id, paths, changed_content, versioned, parent_ids, names,
                 kinds, executables) in self._wt._iter_changes(self._basis_tree):

                # Skip the root entry.
                if parent_ids == (None, None):
                    continue

                change_type = None
                if kinds[0] is None:
                    source_marker = ''
                else:
                    source_marker = osutils.kind_marker(kinds[0])
                if kinds[1] is None:
                    assert kinds[0] is not None
                    marker = osutils.kind_marker(kinds[0])
                else:
                    marker = osutils.kind_marker(kinds[1])

                real_path = paths[1]
                if real_path is None:
                    real_path = paths[0]
                assert real_path is not None
                display_path = real_path + marker

                present_source = versioned[0] and kinds[0] is not None
                present_target = versioned[1] and kinds[1] is not None

                if present_source != present_target:
                    if present_target:
                        change_type = added
                    else:
                        change_type = removed
                elif names[0] != names[1] or parent_ids[0] != parent_ids[1]:
                    # Renamed
                    if changed_content or executables[0] != executables[1]:
                        # and modified
                        change_type = renamed_and_modified
                    else:
                        change_type = renamed
                    display_path = (paths[0] + source_marker
                                    + ' => ' + paths[1] + marker)
                elif kinds[0] != kinds[1]:
                    change_type = kind_changed
                    display_path = (paths[0] + source_marker
                                    + ' => ' + paths[1] + marker)
                elif changed_content is True or executables[0] != executables[1]:
                    change_type = modified
                else:
                    assert False, "How did we get here?"

                store.append([file_id, real_path, True, display_path,
                              change_type, ''])
        finally:
            self._basis_tree.unlock()
            self._wt.unlock()

        self._treeview_files.set_model(store)
        self._last_selected_file = None
        self._treeview_files.set_cursor(0)

    def _fill_in_diff(self):
        self._diff_view.set_trees(self._wt, self._basis_tree)

    def _compute_delta(self):
        self._delta = self._wt.changes_from(self._basis_tree)

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

        # This seems like a reasonable default, we might like it to
        # be a bit wider, so that by default we can fit an 80-line diff in the
        # diff window.
        # Alternatively, we should be saving the last position/size rather than
        # setting it to a fixed value every time we start up.
        screen = self.get_screen()
        monitor = 0 # We would like it to be the monitor we are going to
                    # display on, but I don't know how to figure that out
                    # Only really useful for freaks like me that run dual
                    # monitor, with different sizes on the monitors
        monitor_rect = screen.get_monitor_geometry(monitor)
        width = int(monitor_rect.width * 0.66)
        height = int(monitor_rect.height * 0.66)
        self.set_default_size(width, height)
        self._hpane.set_position(300)

    def _construct_left_pane(self):
        self._left_pane_box = gtk.VBox(homogeneous=False, spacing=5)
        self._construct_file_list()
        self._construct_pending_list()

        self._hpane.pack1(self._left_pane_box, resize=False, shrink=False)
        self._left_pane_box.show()

    def _construct_right_pane(self):
        # TODO: I really want to make it so the diff view gets more space than
        # the global commit message, and the per-file commit message gets even
        # less. When I did it with wxGlade, I set it to 4 for diff, 2 for
        # commit, and 1 for file commit, and it looked good. But I don't seem
        # to have a way to do that with the gtk boxes... :( (Which is extra
        # weird since wx uses gtk on Linux...)
        self._right_pane_table = gtk.Table(rows=10, columns=1, homogeneous=False)
        self._right_pane_table.set_row_spacings(5)
        self._right_pane_table.set_col_spacings(5)
        self._right_pane_table_row = 0
        self._construct_diff_view()
        self._construct_file_message()
        self._construct_global_message()

        self._right_pane_table.show()
        self._hpane.pack2(self._right_pane_table, resize=True, shrink=True)

    def _add_to_right_table(self, widget, weight, expanding=False):
        """Add another widget to the table

        :param widget: The object to add
        :param weight: How many rows does this widget get to request
        :param expanding: Should expand|fill|shrink be set?
        """
        end_row = self._right_pane_table_row + weight
        options = 0
        expand_opts = gtk.EXPAND | gtk.FILL | gtk.SHRINK
        if expanding:
            options = expand_opts
        self._right_pane_table.attach(widget, 0, 1,
                                      self._right_pane_table_row, end_row,
                                      xoptions=expand_opts, yoptions=options)
        self._right_pane_table_row = end_row

    def _construct_file_list(self):
        self._files_box = gtk.VBox(homogeneous=False, spacing=0)
        file_label = gtk.Label(_('Files'))
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

        liststore = gtk.ListStore(
            gobject.TYPE_STRING,  # [0] file_id
            gobject.TYPE_STRING,  # [1] real path
            gobject.TYPE_BOOLEAN, # [2] checkbox
            gobject.TYPE_STRING,  # [3] display path
            gobject.TYPE_STRING,  # [4] changes type
            gobject.TYPE_STRING,  # [5] commit message
            )
        self._files_store = liststore
        self._treeview_files.set_model(liststore)
        crt = gtk.CellRendererToggle()
        crt.set_active(not bool(self._pending))
        crt.connect("toggled", self._toggle_commit, self._files_store)
        if self._pending:
            name = _('Commit*')
        else:
            name = _('Commit')
        self._treeview_files.append_column(gtk.TreeViewColumn(name,
                                           crt, active=2))
        self._treeview_files.append_column(gtk.TreeViewColumn(_('Path'),
                                           gtk.CellRendererText(), text=3))
        self._treeview_files.append_column(gtk.TreeViewColumn(_('Type'),
                                           gtk.CellRendererText(), text=4))
        self._treeview_files.connect('cursor-changed',
                                     self._on_treeview_files_cursor_changed)

    def _toggle_commit(self, cell, path, model):
        if model[path][0] is None: # No file_id means 'All Files'
            new_val = not model[path][2]
            for node in model:
                node[2] = new_val
        else:
            model[path][2] = not model[path][2]

    def _construct_pending_list(self):
        # Pending information defaults to hidden, we put it all in 1 box, so
        # that we can show/hide all of them at once
        self._pending_box = gtk.VBox()
        self._pending_box.hide()

        pending_message = gtk.Label()
        pending_message.set_markup(
            _('<i>* Cannot select specific files when merging</i>'))
        self._pending_box.pack_start(pending_message, expand=False, padding=5)
        pending_message.show()

        pending_label = gtk.Label(_('Pending Revisions'))
        self._pending_box.pack_start(pending_label, expand=False, padding=0)
        pending_label.show()

        scroller = gtk.ScrolledWindow()
        scroller.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self._treeview_pending = gtk.TreeView()
        scroller.add(self._treeview_pending)
        scroller.show()
        scroller.set_shadow_type(gtk.SHADOW_IN)
        self._pending_box.pack_start(scroller,
                                     expand=True, fill=True, padding=5)
        self._treeview_pending.show()
        self._left_pane_box.pack_start(self._pending_box)

        liststore = gtk.ListStore(gobject.TYPE_STRING, # revision_id
                                  gobject.TYPE_STRING, # date
                                  gobject.TYPE_STRING, # committer
                                  gobject.TYPE_STRING, # summary
                                 )
        self._pending_store = liststore
        self._treeview_pending.set_model(liststore)
        self._treeview_pending.append_column(gtk.TreeViewColumn(_('Date'),
                                             gtk.CellRendererText(), text=1))
        self._treeview_pending.append_column(gtk.TreeViewColumn(_('Committer'),
                                             gtk.CellRendererText(), text=2))
        self._treeview_pending.append_column(gtk.TreeViewColumn(_('Summary'),
                                             gtk.CellRendererText(), text=3))

    def _construct_diff_view(self):
        from diff import DiffView

        self._diff_label = gtk.Label(_('Diff for whole tree'))
        self._diff_label.set_alignment(0, 0)
        self._right_pane_table.set_row_spacing(self._right_pane_table_row, 0)
        self._add_to_right_table(self._diff_label, 1, False)
        self._diff_label.show()

        self._diff_view = DiffView()
        self._add_to_right_table(self._diff_view, 4, True)
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

        self._file_message_expander = gtk.Expander(_('File commit message'))
        self._file_message_expander.add(file_message_box)
        file_message_box.show()
        self._add_to_right_table(self._file_message_expander, 1, False)
        self._file_message_expander.show()

    def _construct_global_message(self):
        self._global_message_label = gtk.Label(_('Global Commit Message'))
        self._global_message_label.set_alignment(0, 0)
        self._right_pane_table.set_row_spacing(self._right_pane_table_row, 0)
        self._add_to_right_table(self._global_message_label, 1, False)
        # Can we remove the spacing between the label and the box?
        self._global_message_label.show()

        scroller = gtk.ScrolledWindow()
        scroller.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        self._global_message_text_view = gtk.TextView()
        self._global_message_text_view.modify_font(pango.FontDescription("Monospace"))
        scroller.add(self._global_message_text_view)
        scroller.show()
        scroller.set_shadow_type(gtk.SHADOW_IN)
        self._add_to_right_table(scroller, 2, True)
        self._file_message_text_view.set_wrap_mode(gtk.WRAP_WORD)
        self._file_message_text_view.set_accepts_tab(False)
        self._global_message_text_view.show()

    def _on_treeview_files_cursor_changed(self, treeview):
        treeselection = treeview.get_selection()
        (model, selection) = treeselection.get_selected()

        if selection is not None:
            path, display_path = model.get(selection, 1, 3)
            self._diff_label.set_text(_('Diff for ') + display_path)
            if path is None:
                self._diff_view.show_diff(None)
            else:
                self._diff_view.show_diff([path])
            self._update_per_file_info(selection)

    def _save_current_file_message(self):
        if self._last_selected_file is None:
            return # Nothing to save
        text_buffer = self._file_message_text_view.get_buffer()
        cur_text = text_buffer.get_text(text_buffer.get_start_iter(),
                                        text_buffer.get_end_iter())
        last_selected = self._files_store.get_iter(self._last_selected_file)
        self._files_store.set_value(last_selected, 5, cur_text)

    def _update_per_file_info(self, selection):
        # The node is changing, so cache the current message
        self._save_current_file_message()
        text_buffer = self._file_message_text_view.get_buffer()
        file_id, display_path, message = self._files_store.get(selection, 0, 3, 5)
        if file_id is None: # Whole tree
            self._file_message_expander.set_label(_('File commit message'))
            self._file_message_expander.set_expanded(False)
            self._file_message_expander.set_sensitive(False)
            text_buffer.set_text('')
            self._last_selected_file = None
        else:
            self._file_message_expander.set_label(_('Commit message for ')
                                                  + display_path)
            self._file_message_expander.set_expanded(True)
            self._file_message_expander.set_sensitive(True)
            text_buffer.set_text(message)
            self._last_selected_file = self._files_store.get_path(selection)

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
#         from diff import DiffView
# 
#         self._diff_display = DiffView()
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
