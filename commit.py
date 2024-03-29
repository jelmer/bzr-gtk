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

import re

from gi.repository import Gdk
from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import Pango

from bzrlib import (
    bencode,
    errors,
    osutils,
    revision as _mod_revision,
    trace,
    tsort,
    )
from bzrlib.plugins.gtk.dialog import question_dialog
from bzrlib.plugins.gtk.diff import DiffView
from bzrlib.plugins.gtk.errors import show_bzr_error
from bzrlib.plugins.gtk.i18n import _i18n
from bzrlib.plugins.gtk.commitmsgs import SavedCommitMessagesManager

try:
    import dbus
    import dbus.glib
    have_dbus = True
except ImportError:
    have_dbus = False


def _get_sorted_revisions(tip_revision, revision_ids, parent_map):
    """Get an iterator which will return the revisions in merge sorted order.

    This will build up a list of all nodes, such that only nodes in the list
    are referenced. It then uses MergeSorter to return them in 'merge-sorted'
    order.

    :param revision_ids: A set of revision_ids
    :param parent_map: The parent information for each node. Revisions which
        are considered ghosts should not be present in the map.
    :return: iterator from MergeSorter.iter_topo_order()
    """
    # MergeSorter requires that all nodes be present in the graph, so get rid
    # of any references pointing outside of this graph.
    parent_graph = {}
    for revision_id in revision_ids:
        if revision_id not in parent_map: # ghost
            parent_graph[revision_id] = []
        else:
            # Only include parents which are in this sub-graph
            parent_graph[revision_id] = [p for p in parent_map[revision_id]
                                            if p in revision_ids]
    sorter = tsort.MergeSorter(parent_graph, tip_revision)
    return sorter.iter_topo_order()


def pending_revisions(wt):
    """Return a list of pending merges or None if there are none of them.

    Arguably this should be a core function, and
    ``bzrlib.status.show_pending_merges`` should be built on top of it.

    :return: [(rev, [children])]
    """
    parents = wt.get_parent_ids()
    if len(parents) < 2:
        return

    # The basic pending merge algorithm uses the same algorithm as
    # bzrlib.status.show_pending_merges
    pending = parents[1:]
    branch = wt.branch
    last_revision = parents[0]

    graph = branch.repository.get_graph()
    other_revisions = [last_revision]

    pm = []
    for merge in pending:
        try:
            merge_rev = branch.repository.get_revision(merge)
        except errors.NoSuchRevision:
            # If we are missing a revision, just print out the revision id
            trace.mutter("ghost: %r", merge)
            other_revisions.append(merge)
            continue

        # Find all of the revisions in the merge source, which are not in the
        # last committed revision.
        merge_extra = graph.find_unique_ancestors(merge, other_revisions)
        other_revisions.append(merge)
        merge_extra.discard(_mod_revision.NULL_REVISION)

        # Get a handle to all of the revisions we will need
        try:
            revisions = dict((rev.revision_id, rev) for rev in
                             branch.repository.get_revisions(merge_extra))
        except errors.NoSuchRevision:
            # One of the sub nodes is a ghost, check each one
            revisions = {}
            for revision_id in merge_extra:
                try:
                    rev = branch.repository.get_revisions([revision_id])[0]
                except errors.NoSuchRevision:
                    revisions[revision_id] = None
                else:
                    revisions[revision_id] = rev

         # Display the revisions brought in by this merge.
        rev_id_iterator = _get_sorted_revisions(merge, merge_extra,
                            branch.repository.get_parent_map(merge_extra))
        # Skip the first node
        num, first, depth, eom = rev_id_iterator.next()
        if first != merge:
            raise AssertionError('Somehow we misunderstood how'
                ' iter_topo_order works %s != %s' % (first, merge))
        children = []
        for num, sub_merge, depth, eom in rev_id_iterator:
            rev = revisions[sub_merge]
            if rev is None:
                trace.warning("ghost: %r", sub_merge)
                continue
            children.append(rev)
        yield (merge_rev, children)


_newline_variants_re = re.compile(r'\r\n?')
def _sanitize_and_decode_message(utf8_message):
    """Turn a utf-8 message into a sanitized Unicode message."""
    fixed_newline = _newline_variants_re.sub('\n', utf8_message)
    return osutils.safe_unicode(fixed_newline)


class CommitDialog(Gtk.Dialog):
    """Implementation of Commit."""

    def __init__(self, wt, selected=None, parent=None):
        super(CommitDialog, self).__init__(
            title="Commit to %s" % wt.basedir, parent=parent, flags=0)
        self.connect('delete-event', self._on_delete_window)
        self._question_dialog = question_dialog

        self.set_type_hint(Gdk.WindowTypeHint.NORMAL)

        self._wt = wt
        # TODO: Do something with this value, it is used by Olive
        #       It used to set all changes but this one to False
        self._selected = selected
        self._enable_per_file_commits = True
        self._commit_all_changes = True
        self.committed_revision_id = None # Nothing has been committed yet
        self._last_selected_file = None
        self._saved_commit_messages_manager = SavedCommitMessagesManager(
            self._wt, self._wt.branch)

        self.setup_params()
        self.construct()
        self.fill_in_data()

    def setup_params(self):
        """Setup the member variables for state."""
        self._basis_tree = self._wt.basis_tree()
        self._delta = None
        self._wt.lock_read()
        try:
            self._pending = list(pending_revisions(self._wt))
        finally:
            self._wt.unlock()

        self._is_checkout = (self._wt.branch.get_bound_location() is not None)

    def fill_in_data(self):
        # Now that we are built, handle changes to the view based on the state
        self._fill_in_pending()
        self._fill_in_diff()
        self._fill_in_files()
        self._fill_in_checkout()
        self._fill_in_per_file_info()

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
        # We should really use add a progress bar of some kind.
        # While we fill in the view, hide the store
        store = self._files_store
        self._treeview_files.set_model(None)

        added = _i18n('added')
        removed = _i18n('removed')
        renamed = _i18n('renamed')
        renamed_and_modified = _i18n('renamed and modified')
        modified = _i18n('modified')
        kind_changed = _i18n('kind changed')

        # The store holds:
        # [file_id, real path, checkbox, display path, changes type, message]
        # iter_changes returns:
        # (file_id, (path_in_source, path_in_target),
        #  changed_content, versioned, parent, name, kind,
        #  executable)

        all_enabled = (self._selected is None)
        # The first entry is always the 'whole tree'
        all_iter = store.append(["", "", all_enabled, 'All Files', '', ''])
        initial_cursor = store.get_path(all_iter)
        # should we pass specific_files?
        self._wt.lock_read()
        self._basis_tree.lock_read()
        try:
            from diff import iter_changes_to_status
            saved_file_messages = self._saved_commit_messages_manager.get()[1]
            for (file_id, real_path, change_type, display_path
                ) in iter_changes_to_status(self._basis_tree, self._wt):
                if self._selected and real_path != self._selected:
                    enabled = False
                else:
                    enabled = True
                try:
                    default_message = saved_file_messages[file_id]
                except KeyError:
                    default_message = ''
                item_iter = store.append([
                    file_id,
                    real_path.encode('UTF-8'),
                    enabled,
                    display_path.encode('UTF-8'),
                    change_type,
                    default_message, # Initial comment
                    ])
                if self._selected and enabled:
                    initial_cursor = store.get_path(item_iter)
        finally:
            self._basis_tree.unlock()
            self._wt.unlock()

        self._treeview_files.set_model(store)
        self._last_selected_file = None
        # This sets the cursor, which causes the expander to close, which
        # causes the _file_message_text_view to never get realized. So we have
        # to give it a little kick, or it warns when we try to grab the focus
        self._treeview_files.set_cursor(initial_cursor, None, False)

        def _realize_file_message_tree_view(*args):
            self._file_message_text_view.realize()
        self.connect_after('realize', _realize_file_message_tree_view)

    def _fill_in_diff(self):
        self._diff_view.set_trees(self._wt, self._basis_tree)

    def _fill_in_checkout(self):
        if not self._is_checkout:
            self._check_local.hide()
            return
        if have_dbus:
            try:
                bus = dbus.SystemBus()
            except dbus.DBusException:
                trace.mutter("DBus system bus not available")
                self._check_local.show()
                return
            try:
                proxy_obj = bus.get_object('org.freedesktop.NetworkManager',
                                           '/org/freedesktop/NetworkManager')
            except dbus.DBusException:
                trace.mutter("networkmanager not available.")
                self._check_local.show()
                return

            dbus_iface = dbus.Interface(proxy_obj,
                                        'org.freedesktop.NetworkManager')
            try:
                # 3 is the enum value for STATE_CONNECTED
                self._check_local.set_active(dbus_iface.state() != 3)
            except dbus.DBusException, e:
                # Silently drop errors. While DBus may be
                # available, NetworkManager doesn't necessarily have to be
                trace.mutter("unable to get networkmanager state: %r" % e)
        self._check_local.show()

    def _fill_in_per_file_info(self):
        config = self._wt.branch.get_config()
        enable_per_file_commits = config.get_user_option('per_file_commits')
        if (enable_per_file_commits is None
            or enable_per_file_commits.lower()
                not in ('y', 'yes', 'on', 'enable', '1', 't', 'true')):
            self._enable_per_file_commits = False
        else:
            self._enable_per_file_commits = True
        if not self._enable_per_file_commits:
            self._file_message_expander.hide()
            self._global_message_label.set_markup(_i18n('<b>Commit Message</b>'))

    def _compute_delta(self):
        self._delta = self._wt.changes_from(self._basis_tree)

    def construct(self):
        """Build up the dialog widgets."""
        # The primary pane which splits it into left and right (adjustable)
        # sections.
        self._hpane = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)

        self._construct_left_pane()
        self._construct_right_pane()
        self._construct_action_pane()

        self.get_content_area().pack_start(self._hpane, True, True, 0)
        self._hpane.show()
        self.set_focus(self._global_message_text_view)

        self._construct_accelerators()
        self._set_sizes()

    def _set_sizes(self):
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

    def _construct_accelerators(self):
        group = Gtk.AccelGroup()
        group.connect(Gdk.keyval_from_name('N'),
                      Gdk.ModifierType.CONTROL_MASK, 0, self._on_accel_next)
        self.add_accel_group(group)

        # ignore the escape key (avoid closing the window)
        self.connect_object('close', self.emit_stop_by_name, 'close')

    def _construct_left_pane(self):
        self._left_pane_box = Gtk.VBox(homogeneous=False, spacing=5)
        self._construct_file_list()
        self._construct_pending_list()

        self._check_local = Gtk.CheckButton(_i18n("_Only commit locally"),
                                            use_underline=True)
        self._left_pane_box.pack_end(self._check_local, False, False, 0)
        self._check_local.set_active(False)

        self._hpane.pack1(self._left_pane_box, resize=False, shrink=False)
        self._left_pane_box.show()

    def _construct_right_pane(self):
        # TODO: I really want to make it so the diff view gets more space than
        # the global commit message, and the per-file commit message gets even
        # less. When I did it with wxGlade, I set it to 4 for diff, 2 for
        # commit, and 1 for file commit, and it looked good. But I don't seem
        # to have a way to do that with the gtk boxes... :( (Which is extra
        # weird since wx uses gtk on Linux...)
        self._right_pane_table = Gtk.Table(rows=10, columns=1, homogeneous=False)
        self._right_pane_table.set_row_spacings(5)
        self._right_pane_table.set_col_spacings(5)
        self._right_pane_table_row = 0
        self._construct_diff_view()
        self._construct_file_message()
        self._construct_global_message()

        self._right_pane_table.show()
        self._hpane.pack2(self._right_pane_table, resize=True, shrink=True)

    def _construct_action_pane(self):
        self._button_cancel = Gtk.Button(stock=Gtk.STOCK_CANCEL)
        self._button_cancel.connect('clicked', self._on_cancel_clicked)
        self._button_cancel.show()
        self.get_action_area().pack_end(
            self._button_cancel, True, True, 0)
        self._button_commit = Gtk.Button(_i18n("Comm_it"), use_underline=True)
        self._button_commit.connect('clicked', self._on_commit_clicked)
        self._button_commit.set_can_default(True)
        self._button_commit.show()
        self.get_action_area().pack_end(
            self._button_commit, True, True, 0)
        self._button_commit.grab_default()

    def _add_to_right_table(self, widget, weight, expanding=False):
        """Add another widget to the table

        :param widget: The object to add
        :param weight: How many rows does this widget get to request
        :param expanding: Should expand|fill|shrink be set?
        """
        end_row = self._right_pane_table_row + weight
        options = 0
        expand_opts = Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL | Gtk.AttachOptions.SHRINK
        if expanding:
            options = expand_opts
        self._right_pane_table.attach(widget, 0, 1,
                                      self._right_pane_table_row, end_row,
                                      xoptions=expand_opts, yoptions=options)
        self._right_pane_table_row = end_row

    def _construct_file_list(self):
        self._files_box = Gtk.VBox(homogeneous=False, spacing=0)
        file_label = Gtk.Label(label=_i18n('Files'))
        # file_label.show()
        self._files_box.pack_start(file_label, False, True, 0)

        self._commit_all_files_radio = Gtk.RadioButton.new_with_label(
            None, _i18n("Commit all changes"))
        self._files_box.pack_start(self._commit_all_files_radio, False, True, 0)
        self._commit_all_files_radio.show()
        self._commit_all_files_radio.connect('toggled',
            self._toggle_commit_selection)
        self._commit_selected_radio = Gtk.RadioButton.new_with_label_from_widget(
            self._commit_all_files_radio, _i18n("Only commit selected changes"))
        self._files_box.pack_start(self._commit_selected_radio, False, True, 0)
        self._commit_selected_radio.show()
        self._commit_selected_radio.connect('toggled',
            self._toggle_commit_selection)
        if self._pending:
            self._commit_all_files_radio.set_label(_i18n('Commit all changes*'))
            self._commit_all_files_radio.set_sensitive(False)
            self._commit_selected_radio.set_sensitive(False)

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self._treeview_files = Gtk.TreeView()
        self._treeview_files.show()
        scroller.add(self._treeview_files)
        scroller.set_shadow_type(Gtk.ShadowType.IN)
        scroller.show()
        self._files_box.pack_start(scroller, True, True, 0)
        self._files_box.show()
        self._left_pane_box.pack_start(self._files_box, True, True, 0)

        # Keep note that all strings stored in a ListStore must be UTF-8
        # strings. GTK does not support directly setting and restoring Unicode
        # objects.
        liststore = Gtk.ListStore(
            GObject.TYPE_STRING,  # [0] file_id
            GObject.TYPE_STRING,  # [1] real path
            GObject.TYPE_BOOLEAN, # [2] checkbox
            GObject.TYPE_STRING,  # [3] display path
            GObject.TYPE_STRING,  # [4] changes type
            GObject.TYPE_STRING,  # [5] commit message
            )
        self._files_store = liststore
        self._treeview_files.set_model(liststore)
        crt = Gtk.CellRendererToggle()
        crt.set_property('activatable', not bool(self._pending))
        crt.connect("toggled", self._toggle_commit, self._files_store)
        if self._pending:
            name = _i18n('Commit*')
        else:
            name = _i18n('Commit')
        commit_col = Gtk.TreeViewColumn(name, crt, active=2)
        commit_col.set_visible(False)
        self._treeview_files.append_column(commit_col)
        self._treeview_files.append_column(Gtk.TreeViewColumn(_i18n('Path'),
                                           Gtk.CellRendererText(), text=3))
        self._treeview_files.append_column(Gtk.TreeViewColumn(_i18n('Type'),
                                           Gtk.CellRendererText(), text=4))
        self._treeview_files.connect('cursor-changed',
                                     self._on_treeview_files_cursor_changed)

    def _toggle_commit(self, cell, path, model):
        if model[path][0] == "": # No file_id means 'All Files'
            new_val = not model[path][2]
            for node in model:
                node[2] = new_val
        else:
            model[path][2] = not model[path][2]

    def _toggle_commit_selection(self, button):
        all_files = self._commit_all_files_radio.get_active()
        if self._commit_all_changes != all_files:
            checked_col = self._treeview_files.get_column(0)
            self._commit_all_changes = all_files
            if all_files:
                checked_col.set_visible(False)
            else:
                checked_col.set_visible(True)
            renderer = checked_col.get_cells()[0]
            renderer.set_property('activatable', not all_files)

    def _construct_pending_list(self):
        # Pending information defaults to hidden, we put it all in 1 box, so
        # that we can show/hide all of them at once
        self._pending_box = Gtk.VBox()
        self._pending_box.hide()

        pending_message = Gtk.Label()
        pending_message.set_markup(
            _i18n('<i>* Cannot select specific files when merging</i>'))
        self._pending_box.pack_start(pending_message, False, True, 5)
        pending_message.show()

        pending_label = Gtk.Label(label=_i18n('Pending Revisions'))
        self._pending_box.pack_start(pending_label, False, True, 0)
        pending_label.show()

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self._treeview_pending = Gtk.TreeView()
        scroller.add(self._treeview_pending)
        scroller.set_shadow_type(Gtk.ShadowType.IN)
        scroller.show()
        self._pending_box.pack_start(scroller, True, True, 5)
        self._treeview_pending.show()
        self._left_pane_box.pack_start(self._pending_box, True, True, 0)

        liststore = Gtk.ListStore(GObject.TYPE_STRING, # revision_id
                                  GObject.TYPE_STRING, # date
                                  GObject.TYPE_STRING, # committer
                                  GObject.TYPE_STRING, # summary
                                 )
        self._pending_store = liststore
        self._treeview_pending.set_model(liststore)
        self._treeview_pending.append_column(Gtk.TreeViewColumn(_i18n('Date'),
                                             Gtk.CellRendererText(), text=1))
        self._treeview_pending.append_column(Gtk.TreeViewColumn(_i18n('Committer'),
                                             Gtk.CellRendererText(), text=2))
        self._treeview_pending.append_column(Gtk.TreeViewColumn(_i18n('Summary'),
                                             Gtk.CellRendererText(), text=3))

    def _construct_diff_view(self):
        # TODO: jam 2007-10-30 The diff label is currently disabled. If we
        #       decide that we really don't ever want to display it, we should
        #       actually remove it, and other references to it, along with the
        #       tests that it is set properly.
        self._diff_label = Gtk.Label(label=_i18n('Diff for whole tree'))
        self._diff_label.set_alignment(0, 0)
        self._right_pane_table.set_row_spacing(self._right_pane_table_row, 0)
        self._add_to_right_table(self._diff_label, 1, False)
        # self._diff_label.show()

        self._diff_view = DiffView()
        self._add_to_right_table(self._diff_view, 4, True)
        self._diff_view.show()

    @staticmethod
    def get_line_height(widget):
        pango_layout = widget.create_pango_layout("X");
        ink_rectangle, logical_rectangle = pango_layout.get_pixel_extents()
        return logical_rectangle.height

    def _construct_file_message(self):
        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self._file_message_text_view = Gtk.TextView()
        scroller.add(self._file_message_text_view)
        scroller.set_shadow_type(Gtk.ShadowType.IN)
        scroller.show()

        self._file_message_text_view.modify_font(Pango.FontDescription("Monospace"))
        self._file_message_text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self._file_message_text_view.set_accepts_tab(False)
        line_height = self.get_line_height(self._file_message_text_view)
        self._file_message_text_view.set_size_request(-1, line_height * 2)
        self._file_message_text_view.show()

        self._file_message_expander = Gtk.Expander(
            label=_i18n('File commit message'))
        self._file_message_expander.set_expanded(True)
        self._file_message_expander.add(scroller)
        self._add_to_right_table(self._file_message_expander, 1, False)
        self._file_message_expander.show()

    def _construct_global_message(self):
        self._global_message_label = Gtk.Label(label=_i18n('Global Commit Message'))
        self._global_message_label.set_markup(
            _i18n('<b>Global Commit Message</b>'))
        self._global_message_label.set_alignment(0, 0)
        self._right_pane_table.set_row_spacing(self._right_pane_table_row, 0)
        self._add_to_right_table(self._global_message_label, 1, False)
        # Can we remove the spacing between the label and the box?
        self._global_message_label.show()

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self._global_message_text_view = Gtk.TextView()
        self._set_global_commit_message(self._saved_commit_messages_manager.get()[0])
        self._global_message_text_view.modify_font(Pango.FontDescription("Monospace"))
        scroller.add(self._global_message_text_view)
        scroller.set_shadow_type(Gtk.ShadowType.IN)
        scroller.show()
        self._add_to_right_table(scroller, 2, True)
        self._file_message_text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self._file_message_text_view.set_accepts_tab(False)
        self._global_message_text_view.show()

    def _on_treeview_files_cursor_changed(self, treeview):
        treeselection = treeview.get_selection()
        if treeselection is None:
            # The treeview was probably destroyed as the dialog closes.
            return
        (model, selection) = treeselection.get_selected()

        if selection is not None:
            path, display_path = model.get(selection, 1, 3)
            self._diff_label.set_text(_i18n('Diff for ') + display_path)
            if path == "":
                self._diff_view.show_diff(None)
            else:
                self._diff_view.show_diff([osutils.safe_unicode(path)])
            self._update_per_file_info(selection)

    def _on_accel_next(self, accel_group, window, keyval, modifier):
        # We don't really care about any of the parameters, because we know
        # where this message came from
        tree_selection = self._treeview_files.get_selection()
        (model, selection) = tree_selection.get_selected()
        if selection is None:
            next = None
        else:
            next = model.iter_next(selection)

        if next is None:
            # We have either made it to the end of the list, or nothing was
            # selected. Either way, select All Files, and jump to the global
            # commit message.
            self._treeview_files.set_cursor(
                Gtk.TreePath(path=0), "", False)
            self._global_message_text_view.grab_focus()
        else:
            # Set the cursor to this entry, and jump to the per-file commit
            # message
            self._treeview_files.set_cursor(model.get_path(next), None, False)
            self._file_message_text_view.grab_focus()

    def _save_current_file_message(self):
        if self._last_selected_file is None:
            return # Nothing to save
        text_buffer = self._file_message_text_view.get_buffer()
        cur_text = text_buffer.get_text(text_buffer.get_start_iter(),
                                        text_buffer.get_end_iter(), True)
        last_selected = self._files_store.get_iter(self._last_selected_file)
        self._files_store.set_value(last_selected, 5, cur_text)

    def _update_per_file_info(self, selection):
        # The node is changing, so cache the current message
        if not self._enable_per_file_commits:
            return

        self._save_current_file_message()
        text_buffer = self._file_message_text_view.get_buffer()
        file_id, display_path, message = self._files_store.get(selection, 0, 3, 5)
        if file_id == "": # Whole tree
            self._file_message_expander.set_label(_i18n('File commit message'))
            self._file_message_expander.set_expanded(False)
            self._file_message_expander.set_sensitive(False)
            text_buffer.set_text('')
            self._last_selected_file = None
        else:
            self._file_message_expander.set_label(_i18n('Commit message for ')
                                                  + display_path)
            self._file_message_expander.set_expanded(True)
            self._file_message_expander.set_sensitive(True)
            text_buffer.set_text(message)
            self._last_selected_file = self._files_store.get_path(selection)

    def _get_specific_files(self):
        """Return the list of selected paths, and file info.

        :return: ([unicode paths], [{utf-8 file info}]
        """
        self._save_current_file_message()
        files = []
        records = iter(self._files_store)
        rec = records.next() # Skip the All Files record
        assert rec[0] == "", "Are we skipping the wrong record?"

        file_info = []
        for record in records:
            if self._commit_all_changes or record[2]:# [2] checkbox
                file_id = osutils.safe_utf8(record[0]) # [0] file_id
                path = osutils.safe_utf8(record[1])    # [1] real path
                # [5] commit message
                file_message = _sanitize_and_decode_message(record[5])
                files.append(path.decode('UTF-8'))
                if self._enable_per_file_commits and file_message:
                    # All of this needs to be utf-8 information
                    file_message = file_message.encode('UTF-8')
                    file_info.append({'path':path, 'file_id':file_id,
                                     'message':file_message})
        file_info.sort(key=lambda x:(x['path'], x['file_id']))
        if self._enable_per_file_commits:
            return files, file_info
        else:
            return files, []

    @show_bzr_error
    def _on_cancel_clicked(self, button):
        """ Cancel button clicked handler. """
        self._do_cancel()

    @show_bzr_error
    def _on_delete_window(self, source, event):
        """ Delete window handler. """
        self._do_cancel()

    def _do_cancel(self):
        """If requested, saves commit messages when cancelling gcommit; they are re-used by a next gcommit"""
        mgr = SavedCommitMessagesManager()
        self._saved_commit_messages_manager = mgr
        mgr.insert(self._get_global_commit_message(),
                   self._get_specific_files()[1])
        if mgr.is_not_empty(): # maybe worth saving
            response = self._question_dialog(
                _i18n('Commit cancelled'),
                _i18n('Do you want to save your commit messages ?'),
                parent=self)
            if response == Gtk.ResponseType.NO:
                 # save nothing and destroy old comments if any
                mgr = SavedCommitMessagesManager()
        mgr.save(self._wt, self._wt.branch)
        self.response(Gtk.ResponseType.CANCEL) # close window

    @show_bzr_error
    def _on_commit_clicked(self, button):
        """ Commit button clicked handler. """
        self._do_commit()

    def _do_commit(self):
        message = self._get_global_commit_message()

        if message == '':
            response = self._question_dialog(
                _i18n('Commit with an empty message?'),
                _i18n('You can describe your commit intent in the message.'),
                parent=self)
            if response == Gtk.ResponseType.NO:
                # Kindly give focus to message area
                self._global_message_text_view.grab_focus()
                return

        specific_files, file_info = self._get_specific_files()
        if self._pending:
            specific_files = None

        local = self._check_local.get_active()

        # All we care about is if there is a single unknown, so if this loop is
        # entered, then there are unknown files.
        # TODO: jam 20071002 It seems like this should cancel the dialog
        #       entirely, since there isn't a way for them to add the unknown
        #       files at this point.
        for path in self._wt.unknowns():
            response = self._question_dialog(
                _i18n("Commit with unknowns?"),
                _i18n("Unknown files exist in the working tree. Commit anyway?"),
                parent=self)
                # Doesn't set a parent for the dialog..
            if response == Gtk.ResponseType.NO:
                return
            break

        rev_id = None
        revprops = {}
        if file_info:
            revprops['file-info'] = bencode.bencode(file_info).decode('UTF-8')
        try:
            rev_id = self._wt.commit(message,
                       allow_pointless=False,
                       strict=False,
                       local=local,
                       specific_files=specific_files,
                       revprops=revprops)
        except errors.PointlessCommit:
            response = self._question_dialog(
                _i18n('Commit with no changes?'),
                _i18n('There are no changes in the working tree.'
                      ' Do you want to commit anyway?'),
                parent=self)
            if response == Gtk.ResponseType.YES:
                rev_id = self._wt.commit(message,
                               allow_pointless=True,
                               strict=False,
                               local=local,
                               specific_files=specific_files,
                               revprops=revprops)
        self.committed_revision_id = rev_id
        # destroy old comments if any
        SavedCommitMessagesManager().save(self._wt, self._wt.branch)
        self.response(Gtk.ResponseType.OK)

    def _get_global_commit_message(self):
        buf = self._global_message_text_view.get_buffer()
        start, end = buf.get_bounds()
        text = buf.get_text(start, end, True)
        return _sanitize_and_decode_message(text)

    def _set_global_commit_message(self, message):
        """Just a helper for the test suite."""
        if isinstance(message, unicode):
            message = message.encode('UTF-8')
        self._global_message_text_view.get_buffer().set_text(message)

    def _set_file_commit_message(self, message):
        """Helper for the test suite."""
        if isinstance(message, unicode):
            message = message.encode('UTF-8')
        self._file_message_text_view.get_buffer().set_text(message)

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

