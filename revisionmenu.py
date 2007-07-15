# Copyright (C) 2007 by Jelmer Vernooij <jelmer@samba.org>
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
"""Simple popup menu for revisions."""

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

import bzrlib
import gtk

class RevisionPopupMenu(gtk.Menu):
    def __init__(self, repository, revids, branch=None):
        super(RevisionPopupMenu, self).__init__()
        self.branch = branch
        self.repository = repository
        self.revids = revids
        self.create_items()

    def create_items(self):
        if len(self.revids) == 1:
            item = gtk.MenuItem("View _Diff")
            item.connect('activate', self.show_diff)
            self.append(item)
            self.show_all()

            item = gtk.MenuItem("_Push")
            item.connect('activate', self.show_push)
            self.append(item)
            self.show_all()

    def show_diff(self, item):
        from bzrlib.plugins.gtk.diff import DiffWindow
        window = DiffWindow()
        parentid = self.repository.revision_parents(self.revids[0])[0]
        (parent_tree, rev_tree) = self.repository.revision_trees(
            [parentid, self.revids[0]])
        window.set_diff(self.revids[0], rev_tree, parent_tree)
        window.show()

    def show_push(self, item):
        from bzrlib.plugins.gtk.push import PushDialog
        dialog = PushDialog(self.repository, self.revids[0], self.branch)
        dialog.run()
