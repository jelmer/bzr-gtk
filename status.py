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

from gi.repository import Gtk
from bzrlib.plugins.gtk import window
from bzrlib.plugins.gtk.i18n import _i18n


class StatusWindow(window.Window):
    """ Display Status window and perform the needed actions. """

    def __init__(self, wt, wtpath, revision=None):
        """ Initialize the Status window. """
        super(StatusWindow, self).__init__()
        self.set_title("Working tree changes")
        self._create()
        self.wt = wt
        self.wtpath = wtpath

        if revision is None:
            revision = self.wt.branch.last_revision()

        # Set the old working tree
        self.old_tree = self.wt.branch.repository.revision_tree(revision)
        # Generate status output
        self._generate_status()

    def _create(self):
        self.set_default_size(400, 300)
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.set_shadow_type(Gtk.ShadowType.IN)
        self.treeview = Gtk.TreeView()
        sw.add(self.treeview)
        self.add(sw)

        # sane border and spacing widths (as recommended by GNOME HIG) 
        self.set_border_width(5)
        sw.set_border_width(5)
        self.show_all()


    def row_diff(self, tv, path, tvc):
        file = self.model[path][1]
        if file is None:
            return
        from bzrlib.plugins.gtk.diff import DiffWindow
        window = DiffWindow()
        window.set_diff("Working tree changes", self.wt, self.old_tree)
        window.set_file(file)
        window.show()


    def _generate_status(self):
        """ Generate 'bzr status' output. """
        self.model = Gtk.TreeStore(str, str)
        self.treeview.set_headers_visible(False)
        self.treeview.set_model(self.model)
        self.treeview.connect("row-activated", self.row_diff)

        cell = Gtk.CellRendererText()
        cell.set_property("width-chars", 20)
        column = Gtk.TreeViewColumn()
        column.pack_start(cell, True)
        column.add_attribute(cell, "text", 0)
        self.treeview.append_column(column)

        delta = self.wt.changes_from(self.old_tree)

        changes = False

        if len(delta.added):
            changes = True
            titer = self.model.append(None, [ _i18n('Added'), None ])
            for path, id, kind in delta.added:
                self.model.append(titer, [ path, path ])

        if len(delta.removed):
            changes = True
            titer = self.model.append(None, [ _i18n('Removed'), None ])
            for path, id, kind in delta.removed:
                self.model.append(titer, [ path, path ])

        if len(delta.renamed):
            changes = True
            titer = self.model.append(None, [ _i18n('Renamed'), None ])
            for oldpath, newpath, id, kind, text_modified, meta_modified \
                    in delta.renamed:
                self.model.append(titer, [ oldpath, newpath ])

        if len(delta.modified):
            changes = True
            titer = self.model.append(None, [ _i18n('Modified'), None ])
            for path, id, kind, text_modified, meta_modified in delta.modified:
                self.model.append(titer, [ path, path ])

        done_unknown = False
        for path in self.wt.unknowns():
            changes = True
            if not done_unknown:
                titer = self.model.append(None, [ _i18n('Unknown'), None ])
                done_unknown = True
            self.model.append(titer, [ path, path ])

        if not changes:
            self.model.append(None, [ _i18n('No changes.'), None ])

        self.treeview.expand_all()

    def close(self, widget=None):
        self.window.destroy()
