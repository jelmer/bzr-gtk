"""Difference window.

This module contains the code to manage the diff window which shows
the changes made between two revisions on a branch.
"""

__copyright__ = "Copyright 2005 Canonical Ltd."
__author__ = "Scott James Remnant <scott@ubuntu.com>"


from cStringIO import StringIO

import sys
import inspect

from gi.repository import Gtk
from gi.repository import Pango
try:
    from gi.repository import GtkSource
    have_gtksourceview = True
except ImportError:
    have_gtksourceview = False

from bzrlib import (
    errors,
    merge as _mod_merge,
    osutils,
    urlutils,
    workingtree,
    )
from bzrlib.diff import show_diff_trees
from bzrlib.patches import parse_patches
from bzrlib.plugins.gtk.dialog import (
    error_dialog,
    info_dialog,
    warning_dialog,
    )
from bzrlib.plugins.gtk.i18n import _i18n
from bzrlib.plugins.gtk.window import Window


def fallback_guess_language(slm, content_type):
    for lang_id in slm.get_language_ids():
        lang = slm.get_language(lang_id)
        if "text/x-patch" in lang.get_mime_types():
            return lang
    return None


class SelectCancelled(Exception):

    pass


class DiffFileView(Gtk.ScrolledWindow):
    """Window for displaying diffs from a diff file"""

    SHOW_WIDGETS = True

    def __init__(self):
        super(DiffFileView, self).__init__()
        self.construct()
        self._diffs = {}

    def construct(self):
        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.set_shadow_type(Gtk.ShadowType.IN)

        if have_gtksourceview:
            self.buffer = GtkSource.Buffer()
            lang_manager = GtkSource.LanguageManager.get_default()
            language = lang_manager.guess_language(None, "text/x-patch")
            self.buffer.set_language(language)
            self.buffer.set_highlight_syntax(True)
            self.sourceview = GtkSource.View(buffer=self.buffer)
        else:
            self.buffer = Gtk.TextBuffer()
            self.sourceview = Gtk.TextView(self.buffer)

        self.sourceview.set_editable(False)
        self.sourceview.override_font(Pango.FontDescription("Monospace"))
        self.add(self.sourceview)
        if self.SHOW_WIDGETS:
            self.sourceview.show()

    def set_trees(self, rev_tree, parent_tree):
        self.rev_tree = rev_tree
        self.parent_tree = parent_tree
#        self._build_delta()

#    def _build_delta(self):
#        self.parent_tree.lock_read()
#        self.rev_tree.lock_read()
#        try:
#            self.delta = iter_changes_to_status(
#               self.parent_tree, self.rev_tree)
#            self.path_to_status = {}
#            self.path_to_diff = {}
#            source_inv = self.parent_tree.inventory
#            target_inv = self.rev_tree.inventory
#            for (file_id, real_path, change_type, display_path) in self.delta:
#                self.path_to_status[real_path] = u'=== %s %s' % (
#                    change_type, display_path)
#                if change_type in ('modified', 'renamed and modified'):
#                    source_ie = source_inv[file_id]
#                    target_ie = target_inv[file_id]
#                    sio = StringIO()
#                    source_ie.diff(internal_diff, *old path, *old_tree,
#                                   *new_path, target_ie, self.rev_tree,
#                                   sio)
#                    self.path_to_diff[real_path] =
#
#        finally:
#            self.rev_tree.unlock()
#            self.parent_tree.unlock()

    def show_diff(self, specific_files):
        sections = []
        if specific_files is None:
            self.buffer.set_text(self._diffs[None])
        else:
            for specific_file in specific_files:
                sections.append(self._diffs[specific_file])
            self.buffer.set_text(''.join(sections))


class DiffView(DiffFileView):
    """This is the soft and chewy filling for a DiffWindow."""

    def __init__(self):
        super(DiffView, self).__init__()
        self.rev_tree = None
        self.parent_tree = None

    def show_diff(self, specific_files):
        """Show the diff for the specified files"""
        s = StringIO()
        show_diff_trees(self.parent_tree, self.rev_tree, s, specific_files,
                        old_label='', new_label='',
                        # path_encoding=sys.getdefaultencoding()
                        # The default is utf-8, but we interpret the file
                        # contents as getdefaultencoding(), so we should
                        # probably try to make the paths in the same encoding.
                        )
        # str.decode(encoding, 'replace') doesn't do anything. Because if a
        # character is not valid in 'encoding' there is nothing to replace, the
        # 'replace' is for 'str.encode()'
        try:
            decoded = s.getvalue().decode(sys.getdefaultencoding())
        except UnicodeDecodeError:
            try:
                decoded = s.getvalue().decode('UTF-8')
            except UnicodeDecodeError:
                decoded = s.getvalue().decode('iso-8859-1')
                # This always works, because every byte has a valid
                # mapping from iso-8859-1 to Unicode
        # TextBuffer must contain pure UTF-8 data
        self.buffer.set_text(decoded.encode('UTF-8'))


class DiffWidget(Gtk.HPaned):
    """Diff widget

    """

    SHOW_WIDGETS = True

    def __init__(self):
        super(DiffWidget, self).__init__()

        # The file hierarchy: a scrollable treeview
        scrollwin = Gtk.ScrolledWindow()
        scrollwin.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrollwin.set_shadow_type(Gtk.ShadowType.IN)
        self.pack1(scrollwin)
        if self.SHOW_WIDGETS:
            scrollwin.show()

        self.model = Gtk.TreeStore(str, str)
        self.treeview = Gtk.TreeView(model=self.model)
        self.treeview.set_headers_visible(False)
        self.treeview.set_search_column(1)
        self.treeview.connect("cursor-changed", self._treeview_cursor_cb)
        scrollwin.add(self.treeview)
        if self.SHOW_WIDGETS:
            self.treeview.show()

        cell = Gtk.CellRendererText()
        cell.set_property("width-chars", 20)
        column = Gtk.TreeViewColumn()
        column.pack_start(cell, True)
        column.add_attribute(cell, "text", 0)
        self.treeview.append_column(column)

    def set_diff_text(self, lines):
        """Set the current diff from a list of lines

        :param lines: The diff to show, in unified diff format
        """
        # The diffs of the  selected file: a scrollable source or
        # text view

    def set_diff_text_sections(self, sections):
        if getattr(self, 'diff_view', None) is None:
            self.diff_view = DiffFileView()
            self.pack2(self.diff_view)
        if self.SHOW_WIDGETS:
            self.diff_view.show()
        for oldname, newname, patch in sections:
            self.diff_view._diffs[newname] = str(patch)
            if newname is None:
                newname = ''
            self.model.append(None, [oldname, newname])
        self.diff_view.show_diff(None)

    def set_diff(self, rev_tree, parent_tree):
        """Set the differences showed by this window.

        Compares the two trees and populates the window with the
        differences.
        """
        if getattr(self, 'diff_view', None) is None:
            self.diff_view = DiffView()
            self.pack2(self.diff_view)
        if self.SHOW_WIDGETS:
            self.diff_view.show()
        self.diff_view.set_trees(rev_tree, parent_tree)
        self.rev_tree = rev_tree
        self.parent_tree = parent_tree

        self.model.clear()
        delta = self.rev_tree.changes_from(self.parent_tree)

        self.model.append(None, ["Complete Diff", ""])

        if len(delta.added):
            titer = self.model.append(None, ["Added", None])
            for path, id, kind in delta.added:
                self.model.append(titer, [path, path])

        if len(delta.removed):
            titer = self.model.append(None, ["Removed", None])
            for path, id, kind in delta.removed:
                self.model.append(titer, [path, path])

        if len(delta.renamed):
            titer = self.model.append(None, ["Renamed", None])
            for oldpath, newpath, id, kind, text_modified, meta_modified \
                    in delta.renamed:
                self.model.append(titer, [oldpath, newpath])

        if len(delta.modified):
            titer = self.model.append(None, ["Modified", None])
            for path, id, kind, text_modified, meta_modified in delta.modified:
                self.model.append(titer, [path, path])

        self.treeview.expand_all()
        self.diff_view.show_diff(None)

    def set_file(self, file_path):
        """Select the current file to display"""
        tv_path = None
        for data in self.model:
            for child in data.iterchildren():
                if child[0] == file_path or child[1] == file_path:
                    tv_path = child.path
                    break
        if tv_path is None:
            raise errors.NoSuchFile(file_path)
        self.treeview.set_cursor(tv_path, None, False)
        self.treeview.scroll_to_cell(tv_path)

    def _treeview_cursor_cb(self, *args):
        """Callback for when the treeview cursor changes."""
        (path, col) = self.treeview.get_cursor()
        if path is None:
            return
        specific_files = [self.model[path][1]]
        if specific_files == [None]:
            return
        elif specific_files == [""]:
            specific_files = None

        self.diff_view.show_diff(specific_files)

    def _on_wraplines_toggled(self, widget=None, wrap=False):
        """Callback for when the wrap lines checkbutton is toggled"""
        if wrap or widget.get_active():
            self.diff_view.sourceview.set_wrap_mode(Gtk.WrapMode.WORD)
        else:
            self.diff_view.sourceview.set_wrap_mode(Gtk.WrapMode.NONE)


class DiffWindow(Window):
    """Diff window.

    This object represents and manages a single window containing the
    differences between two revisions on a branch.
    """

    SHOW_WIDGETS = True

    def __init__(self, parent=None, operations=None):
        super(DiffWindow, self).__init__(parent=parent)
        self.set_border_width(0)
        self.set_title("bzr diff")

        # Use two thirds of the screen by default
        screen = self.get_screen()
        monitor = screen.get_monitor_geometry(0)
        width = int(monitor.width * 0.66)
        height = int(monitor.height * 0.66)
        self.set_default_size(width, height)
        self.construct(operations)

    def construct(self, operations):
        """Construct the window contents."""
        self.vbox = Gtk.VBox()
        self.add(self.vbox)
        if self.SHOW_WIDGETS:
            self.vbox.show()
        self.diff = DiffWidget()
        self.vbox.pack_end(self.diff, True, True, 0)
        if self.SHOW_WIDGETS:
            self.diff.show_all()
        # Build after DiffWidget to connect signals
        menubar = self._get_menu_bar()
        self.vbox.pack_start(menubar, False, False, 0)
        hbox = self._get_button_bar(operations)
        if hbox is not None:
            self.vbox.pack_start(hbox, False, True, 0)

    def _get_menu_bar(self):
        menubar = Gtk.MenuBar()
        # View menu
        mb_view = Gtk.MenuItem.new_with_mnemonic(_i18n("_View"))
        mb_view_menu = Gtk.Menu()
        mb_view_wrapsource = Gtk.CheckMenuItem.new_with_mnemonic(
            _i18n("Wrap _Long Lines"))
        mb_view_wrapsource.connect('activate', self.diff._on_wraplines_toggled)
        mb_view_menu.append(mb_view_wrapsource)
        mb_view.set_submenu(mb_view_menu)
        menubar.append(mb_view)
        if self.SHOW_WIDGETS:
            menubar.show_all()
        return menubar

    def _get_button_bar(self, operations):
        """Return a button bar to use.

        :return: None, meaning that no button bar will be used.
        """
        if operations is None:
            return None
        hbox = Gtk.HButtonBox()
        hbox.set_layout(Gtk.ButtonBoxStyle.START)
        for title, method in operations:
            merge_button = Gtk.Button(title)
            if self.SHOW_WIDGETS:
                merge_button.show()
            merge_button.set_relief(Gtk.ReliefStyle.NONE)
            merge_button.connect("clicked", method)
            hbox.pack_start(merge_button, False, True, 0)
        if self.SHOW_WIDGETS:
            hbox.show()
        return hbox

    def _get_merge_target(self):
        d = Gtk.FileChooserDialog('Merge branch', self,
                                  Gtk.FileChooserAction.SELECT_FOLDER,
                                  buttons=(Gtk.STOCK_OK, Gtk.ResponseType.OK,
                                           Gtk.STOCK_CANCEL,
                                           Gtk.ResponseType.CANCEL,))
        try:
            result = d.run()
            if result != Gtk.ResponseType.OK:
                raise SelectCancelled()
            return d.get_current_folder_uri()
        finally:
            d.destroy()

    def _merge_successful(self):
        # No conflicts found.
        info_dialog(_i18n('Merge successful'),
                    _i18n('All changes applied successfully.'))

    def _conflicts(self):
        warning_dialog(_i18n('Conflicts encountered'),
                       _i18n('Please resolve the conflicts manually'
                             ' before committing.'))

    def _handle_error(self, e):
        error_dialog('Error', str(e))

    def _get_save_path(self, basename):
        d = Gtk.FileChooserDialog('Save As', self,
                                  Gtk.FileChooserAction.SAVE,
                                  buttons=(Gtk.STOCK_OK, Gtk.ResponseType.OK,
                                           Gtk.STOCK_CANCEL,
                                           Gtk.ResponseType.CANCEL,))
        d.set_current_name(basename)
        try:
            result = d.run()
            if result != Gtk.ResponseType.OK:
                raise SelectCancelled()
            return urlutils.local_path_from_url(d.get_uri())
        finally:
            d.destroy()

    def set_diff(self, description, rev_tree, parent_tree):
        """Set the differences showed by this window.

        Compares the two trees and populates the window with the
        differences.
        """
        self.diff.set_diff(rev_tree, parent_tree)
        self.set_title(description + " - bzrk diff")

    def set_file(self, file_path):
        self.diff.set_file(file_path)


class DiffController(object):

    def __init__(self, path, patch, window=None, allow_dirty=False):
        self.path = path
        self.patch = patch
        self.allow_dirty = allow_dirty
        if window is None:
            window = DiffWindow(operations=self._provide_operations())
            self.initialize_window(window)
        self.window = window

    def initialize_window(self, window):
        window.diff.set_diff_text_sections(self.get_diff_sections())
        window.set_title(self.path + " - diff")

    def get_diff_sections(self):
        yield "Complete Diff", None, ''.join(self.patch)
        # allow_dirty was added to parse_patches in bzrlib 2.2b1
        if 'allow_dirty' in inspect.getargspec(parse_patches).args:
            patches = parse_patches(self.patch, allow_dirty=self.allow_dirty)
        else:
            patches = parse_patches(self.patch)
        for patch in patches:
            oldname = patch.oldname.split('\t')[0]
            newname = patch.newname.split('\t')[0]
            yield oldname, newname, str(patch)

    def perform_save(self, window):
        try:
            save_path = self.window._get_save_path(osutils.basename(self.path))
        except SelectCancelled:
            return
        source = open(self.path, 'rb')
        try:
            target = open(save_path, 'wb')
            try:
                osutils.pumpfile(source, target)
            finally:
                target.close()
        finally:
            source.close()

    def _provide_operations(self):
        return [('Save', self.perform_save)]


class MergeDirectiveController(DiffController):

    def __init__(self, path, directive, window=None):
        super(MergeDirectiveController, self).__init__(
            path, directive.patch.splitlines(True), window)
        self.directive = directive
        self.merge_target = None

    def _provide_operations(self):
        return [('Merge', self.perform_merge), ('Save', self.perform_save)]

    def perform_merge(self, window):
        if self.merge_target is None:
            try:
                self.merge_target = self.window._get_merge_target()
            except SelectCancelled:
                return
        tree = workingtree.WorkingTree.open(self.merge_target)
        tree.lock_write()
        try:
            try:
                if tree.has_changes():
                    raise errors.UncommittedChanges(tree)
                merger, verified = _mod_merge.Merger.from_mergeable(
                    tree, self.directive, pb=None)
                merger.merge_type = _mod_merge.Merge3Merger
                conflict_count = merger.do_merge()
                merger.set_pending()
                if conflict_count == 0:
                    self.window._merge_successful()
                else:
                    self.window._conflicts()
                    # There are conflicts to be resolved.
                self.window.destroy()
            except Exception, e:
                self.window._handle_error(e)
        finally:
            tree.unlock()


def iter_changes_to_status(source, target):
    """Determine the differences between trees.

    This is a wrapper around iter_changes which just yields more
    understandable results.

    :param source: The source tree (basis tree)
    :param target: The target tree
    :return: A list of (file_id, real_path, change_type, display_path)
    """
    added = 'added'
    removed = 'removed'
    renamed = 'renamed'
    renamed_and_modified = 'renamed and modified'
    modified = 'modified'
    kind_changed = 'kind changed'
    missing = 'missing'

    # TODO: Handle metadata changes

    status = []
    target.lock_read()
    try:
        source.lock_read()
        try:
            for (file_id, paths, changed_content, versioned, parent_ids, names,
                 kinds, executables) in target.iter_changes(source):

                # Skip the root entry if it isn't very interesting
                if parent_ids == (None, None):
                    continue

                change_type = None
                if kinds[0] is None:
                    source_marker = ''
                else:
                    source_marker = osutils.kind_marker(kinds[0])

                if kinds[1] is None:
                    if kinds[0] is None:
                        # We assume bzr will flag only files in that case,
                        # there may be a bzr bug there as only files seems to
                        # not receive any kind.
                        marker = osutils.kind_marker('file')
                    else:
                        marker = osutils.kind_marker(kinds[0])
                else:
                    marker = osutils.kind_marker(kinds[1])

                real_path = paths[1]
                if real_path is None:
                    real_path = paths[0]
                assert real_path is not None

                present_source = versioned[0] and kinds[0] is not None
                present_target = versioned[1] and kinds[1] is not None

                if kinds[0] is None and kinds[1] is None:
                    change_type = missing
                    display_path = real_path + marker
                elif present_source != present_target:
                    if present_target:
                        change_type = added
                    else:
                        assert present_source
                        change_type = removed
                    display_path = real_path + marker
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
                elif changed_content or executables[0] != executables[1]:
                    change_type = modified
                    display_path = real_path + marker
                else:
                    assert False, "How did we get here?"

                status.append((file_id, real_path, change_type, display_path))
        finally:
            source.unlock()
    finally:
        target.unlock()

    return status
