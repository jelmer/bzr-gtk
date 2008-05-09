# -*- coding: UTF-8 -*-
"""Difference window.

This module contains the code to manage the diff window which shows
the changes made between two revisions on a branch.
"""

__copyright__ = "Copyright © 2005 Canonical Ltd."
__author__    = "Scott James Remnant <scott@ubuntu.com>"


from cStringIO import StringIO

import pygtk
pygtk.require("2.0")
import gtk
import pango
import os
import re
import sys

try:
    import gtksourceview
    have_gtksourceview = True
except ImportError:
    have_gtksourceview = False
try:
    import gconf
    have_gconf = True
except ImportError:
    have_gconf = False

from bzrlib import (
    merge as _mod_merge,
    osutils,
    progress,
    urlutils,
    workingtree,
)
from bzrlib.diff import show_diff_trees, internal_diff
from bzrlib.errors import NoSuchFile
from bzrlib.patches import parse_patches
from bzrlib.trace import warning
from bzrlib.plugins.gtk.window import Window
from dialog import error_dialog, info_dialog, warning_dialog


class SelectCancelled(Exception):

    pass


class DiffFileView(gtk.ScrolledWindow):
    """Window for displaying diffs from a diff file"""

    def __init__(self):
        gtk.ScrolledWindow.__init__(self)
        self.construct()
        self._diffs = {}

    def construct(self):
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.set_shadow_type(gtk.SHADOW_IN)

        if have_gtksourceview:
            self.buffer = gtksourceview.SourceBuffer()
            slm = gtksourceview.SourceLanguagesManager()
            gsl = slm.get_language_from_mime_type("text/x-patch")
            if have_gconf:
                self.apply_gedit_colors(gsl)
            self.apply_colordiff_colors(gsl)
            self.buffer.set_language(gsl)
            self.buffer.set_highlight(True)

            sourceview = gtksourceview.SourceView(self.buffer)
        else:
            self.buffer = gtk.TextBuffer()
            sourceview = gtk.TextView(self.buffer)

        sourceview.set_editable(False)
        sourceview.modify_font(pango.FontDescription("Monospace"))
        self.add(sourceview)
        sourceview.show()

    @staticmethod
    def apply_gedit_colors(lang):
        """Set style for lang to that specified in gedit configuration.

        This method needs the gconf module.

        :param lang: a gtksourceview.SourceLanguage object.
        """
        GEDIT_SYNTAX_PATH = '/apps/gedit-2/preferences/syntax_highlighting'
        GEDIT_LANG_PATH = GEDIT_SYNTAX_PATH + '/' + lang.get_id()

        client = gconf.client_get_default()
        client.add_dir(GEDIT_LANG_PATH, gconf.CLIENT_PRELOAD_NONE)

        for tag in lang.get_tags():
            tag_id = tag.get_id()
            gconf_key = GEDIT_LANG_PATH + '/' + tag_id
            style_string = client.get_string(gconf_key)

            if style_string is None:
                continue

            # function to get a bool from a string that's either '0' or '1'
            string_bool = lambda x: bool(int(x))

            # style_string is a string like "2/#FFCCAA/#000000/0/1/0/0"
            # values are: mask, fg, bg, italic, bold, underline, strike
            # this packs them into (str_value, attr_name, conv_func) tuples
            items = zip(style_string.split('/'), ['mask', 'foreground',
                'background', 'italic', 'bold', 'underline', 'strikethrough' ],
                [ int, gtk.gdk.color_parse, gtk.gdk.color_parse, string_bool,
                    string_bool, string_bool, string_bool ]
            )

            style = gtksourceview.SourceTagStyle()

            # XXX The mask attribute controls whether the present values of
            # foreground and background color should in fact be used. Ideally
            # (and that's what gedit does), one could set all three attributes,
            # and let the TagStyle object figure out which colors to use.
            # However, in the GtkSourceview python bindings, the mask attribute
            # is read-only, and it's derived instead from the colors being
            # set or not. This means that we have to sometimes refrain from
            # setting fg or bg colors, depending on the value of the mask.
            # This code could go away if mask were writable.
            mask = int(items[0][0])
            if not (mask & 1): # GTK_SOURCE_TAG_STYLE_USE_BACKGROUND
                items[2:3] = []
            if not (mask & 2): # GTK_SOURCE_TAG_STYLE_USE_FOREGROUND
                items[1:2] = []
            items[0:1] = [] # skip the mask unconditionally

            for value, attr, func in items:
                try:
                    value = func(value)
                except ValueError:
                    warning('gconf key %s contains an invalid value: %s'
                            % gconf_key, value)
                else:
                    setattr(style, attr, value)

            lang.set_tag_style(tag_id, style)

    @classmethod
    def apply_colordiff_colors(klass, lang):
        """Set style colors for lang using the colordiff configuration file.

        Both ~/.colordiffrc and ~/.colordiffrc.bzr-gtk are read.

        :param lang: a "Diff" gtksourceview.SourceLanguage object.
        """
        colors = {}

        for f in ('~/.colordiffrc', '~/.colordiffrc.bzr-gtk'):
            f = os.path.expanduser(f)
            if os.path.exists(f):
                try:
                    f = file(f)
                except IOError, e:
                    warning('could not open file %s: %s' % (f, str(e)))
                else:
                    colors.update(klass.parse_colordiffrc(f))
                    f.close()

        if not colors:
            # ~/.colordiffrc does not exist
            return

        mapping = {
                # map GtkSourceView tags to colordiff names
                # since GSV is richer, accept new names for extra bits,
                # defaulting to old names if they're not present
                'Added@32@line': ['newtext'],
                'Removed@32@line': ['oldtext'],
                'Location': ['location', 'diffstuff'],
                'Diff@32@file': ['file', 'diffstuff'],
                'Special@32@case': ['specialcase', 'diffstuff'],
        }

        for tag in lang.get_tags():
            tag_id = tag.get_id()
            keys = mapping.get(tag_id, [])
            color = None

            for key in keys:
                color = colors.get(key, None)
                if color is not None:
                    break

            if color is None:
                continue

            style = gtksourceview.SourceTagStyle()
            try:
                style.foreground = gtk.gdk.color_parse(color)
            except ValueError:
                warning('not a valid color: %s' % color)
            else:
                lang.set_tag_style(tag_id, style)

    @staticmethod
    def parse_colordiffrc(fileobj):
        """Parse fileobj as a colordiff configuration file.

        :return: A dict with the key -> value pairs.
        """
        colors = {}
        for line in fileobj:
            if re.match(r'^\s*#', line):
                continue
            if '=' not in line:
                continue
            key, val = line.split('=', 1)
            colors[key.strip()] = val.strip()
        return colors

    def set_trees(self, rev_tree, parent_tree):
        self.rev_tree = rev_tree
        self.parent_tree = parent_tree
#        self._build_delta()

#    def _build_delta(self):
#        self.parent_tree.lock_read()
#        self.rev_tree.lock_read()
#        try:
#            self.delta = iter_changes_to_status(self.parent_tree, self.rev_tree)
#            self.path_to_status = {}
#            self.path_to_diff = {}
#            source_inv = self.parent_tree.inventory
#            target_inv = self.rev_tree.inventory
#            for (file_id, real_path, change_type, display_path) in self.delta:
#                self.path_to_status[real_path] = u'=== %s %s' % (change_type, display_path)
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
        DiffFileView.__init__(self)
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


class DiffWidget(gtk.HPaned):
    """Diff widget

    """
    def __init__(self):
        super(DiffWidget, self).__init__()

        # The file hierarchy: a scrollable treeview
        scrollwin = gtk.ScrolledWindow()
        scrollwin.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scrollwin.set_shadow_type(gtk.SHADOW_IN)
        self.pack1(scrollwin)
        scrollwin.show()

        self.model = gtk.TreeStore(str, str)
        self.treeview = gtk.TreeView(self.model)
        self.treeview.set_headers_visible(False)
        self.treeview.set_search_column(1)
        self.treeview.connect("cursor-changed", self._treeview_cursor_cb)
        scrollwin.add(self.treeview)
        self.treeview.show()

        cell = gtk.CellRendererText()
        cell.set_property("width-chars", 20)
        column = gtk.TreeViewColumn()
        column.pack_start(cell, expand=True)
        column.add_attribute(cell, "text", 0)
        self.treeview.append_column(column)

    def set_diff_text(self, lines):
        """Set the current diff from a list of lines

        :param lines: The diff to show, in unified diff format
        """
        # The diffs of the  selected file: a scrollable source or
        # text view

    def set_diff_text_sections(self, sections):
        self.diff_view = DiffFileView()
        self.diff_view.show()
        self.pack2(self.diff_view)
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
        self.diff_view = DiffView()
        self.pack2(self.diff_view)
        self.diff_view.show()
        self.diff_view.set_trees(rev_tree, parent_tree)
        self.rev_tree = rev_tree
        self.parent_tree = parent_tree

        self.model.clear()
        delta = self.rev_tree.changes_from(self.parent_tree)

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

    def set_file(self, file_path):
        """Select the current file to display"""
        tv_path = None
        for data in self.model:
            for child in data.iterchildren():
                if child[0] == file_path or child[1] == file_path:
                    tv_path = child.path
                    break
        if tv_path is None:
            raise NoSuchFile(file_path)
        self.treeview.set_cursor(tv_path)
        self.treeview.scroll_to_cell(tv_path)

    def _treeview_cursor_cb(self, *args):
        """Callback for when the treeview cursor changes."""
        (path, col) = self.treeview.get_cursor()
        specific_files = [ self.model[path][1] ]
        if specific_files == [ None ]:
            return
        elif specific_files == [ "" ]:
            specific_files = None

        self.diff_view.show_diff(specific_files)


class DiffWindow(Window):
    """Diff window.

    This object represents and manages a single window containing the
    differences between two revisions on a branch.
    """

    def __init__(self, parent=None, operations=None):
        Window.__init__(self, parent)
        self.set_border_width(0)
        self.set_title("bzrk diff")

        # Use two thirds of the screen by default
        screen = self.get_screen()
        monitor = screen.get_monitor_geometry(0)
        width = int(monitor.width * 0.66)
        height = int(monitor.height * 0.66)
        self.set_default_size(width, height)
        self.construct(operations)

    def construct(self, operations):
        """Construct the window contents."""
        self.vbox = gtk.VBox()
        self.add(self.vbox)
        self.vbox.show()
        hbox = self._get_button_bar(operations)
        if hbox is not None:
            self.vbox.pack_start(hbox, expand=False, fill=True)
        self.diff = DiffWidget()
        self.vbox.add(self.diff)
        self.diff.show_all()

    def _get_button_bar(self, operations):
        """Return a button bar to use.

        :return: None, meaning that no button bar will be used.
        """
        if operations is None:
            return None
        hbox = gtk.HButtonBox()
        hbox.set_layout(gtk.BUTTONBOX_START)
        for title, method in operations:
            merge_button = gtk.Button(title)
            merge_button.show()
            merge_button.set_relief(gtk.RELIEF_NONE)
            merge_button.connect("clicked", method)
            hbox.pack_start(merge_button, expand=False, fill=True)
        hbox.show()
        return hbox

    def _get_merge_target(self):
        d = gtk.FileChooserDialog('Merge branch', self,
                                  gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                  buttons=(gtk.STOCK_OK, gtk.RESPONSE_OK,
                                           gtk.STOCK_CANCEL,
                                           gtk.RESPONSE_CANCEL,))
        try:
            result = d.run()
            if result != gtk.RESPONSE_OK:
                raise SelectCancelled()
            return d.get_current_folder_uri()
        finally:
            d.destroy()

    def _merge_successful(self):
        # No conflicts found.
        info_dialog(_('Merge successful'),
                    _('All changes applied successfully.'))

    def _get_save_path(self, basename):
        d = gtk.FileChooserDialog('Save As', self,
                                  gtk.FILE_CHOOSER_ACTION_SAVE,
                                  buttons=(gtk.STOCK_OK, gtk.RESPONSE_OK,
                                           gtk.STOCK_CANCEL,
                                           gtk.RESPONSE_CANCEL,))
        d.set_current_name(basename)
        try:
            result = d.run()
            if result != gtk.RESPONSE_OK:
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

    def __init__(self, path, patch, window=None):
        self.path = path
        self.patch = patch
        if window is None:
            window = DiffWindow(operations=self._provide_operations())
            self.initialize_window(window)
        self.window = window

    def initialize_window(self, window):
        window.diff.set_diff_text_sections(self.get_diff_sections())
        window.set_title(self.path + " - diff")

    def get_diff_sections(self):
        yield "Complete Diff", None, ''.join(self.patch)
        for patch in parse_patches(self.patch):
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

    def __init__(self, path, directive, window):
        DiffController.__init__(self, path, directive.patch.splitlines(True),
                                window)
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
                merger, verified = _mod_merge.Merger.from_mergeable(tree,
                    self.directive, progress.DummyProgress())
                merger.check_basis(True)
                merger.merge_type = _mod_merge.Merge3Merger
                conflict_count = merger.do_merge()
                merger.set_pending()
                if conflict_count == 0:
                    self.window._merge_successful()
                else:
                    # There are conflicts to be resolved.
                    warning_dialog(_('Conflicts encountered'),
                                   _('Please resolve the conflicts manually'
                                     ' before committing.'))
                self.window.destroy()
            except Exception, e:
                error_dialog('Error', str(e))
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
                        assert present_source
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

                status.append((file_id, real_path, change_type, display_path))
        finally:
            source.unlock()
    finally:
        target.unlock()

    return status
