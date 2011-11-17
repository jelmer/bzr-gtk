# Trivial Bazaar plugin for Nautilus
#
# Copyright (C) 2006 Jeff Bailey
# Copyright (C) 2006 Wouter van Heyst
# Copyright (C) 2006-2011 Jelmer Vernooij <jelmer@samba.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# Installation:
# setup.py can install nautilus-bzr to the right system folder, if pkg-config
# is present.
#
# You can also install nautilus-bzr manually by copying it (or linking it from)
# ~/.local/share/nautilus-python/extensions/nautilus-bzr.py

from gi.repository import Gtk, Nautilus, GObject
from bzrlib.controldir import ControlDir
from bzrlib.errors import (
    NotBranchError,
    NoWorkingTree,
    )
from bzrlib.tree import InterTree
from bzrlib.workingtree import WorkingTree

from bzrlib.plugin import load_plugins
load_plugins()


class BazaarExtension(Nautilus.MenuProvider, Nautilus.ColumnProvider,
        Nautilus.InfoProvider, Nautilus.PropertyPageProvider, GObject.GObject):
    """Nautilus extension providing Bazaar integration."""

    def __init__(self):
        pass

    @classmethod
    def _open_bzrdir(cls, vfs_file):
        uri = vfs_file.get_uri()
        controldir, path = ControlDir.open_containing(uri)
        return controldir, path

    def add_cb(self, menu, vfs_file):
        controldir, path = self._open_bzrdir(vfs_file)
        tree = controldir.open_workingtree()
        tree.add(path)

    def ignore_cb(self, menu, vfs_file):
        # We can only cope with local files
        controldir, path = self._open_bzrdir(vfs_file)
        tree = controldir.open_workingtree()
        #FIXME: Add path to ignore file
        return

    def unignore_cb(self, menu, vfs_file):
        # We can only cope with local files
        controldir, path = self._open_bzrdir(vfs_file)
        tree = controldir.open_workingtree()
        #FIXME
        return

    def diff_cb(self, menu, vfs_file):
        controldir, path = self._open_bzrdir(vfs_file)
        tree = controldir.open_workingtree()
        from bzrlib.plugins.gtk.diff import DiffWindow
        window = DiffWindow()
        window.set_diff(tree.branch._get_nick(local=True), tree, 
                        tree.branch.basis_tree())
        window.show()

        return

    def newtree_cb(self, menu, vfs_file):
        controldir, path = self._open_bzrdir(vfs_file)
        controldir.create_workingtree()

    def remove_cb(self, menu, vfs_file):
        controldir, path = self._open_bzrdir(vfs_file)
        tree = controldir.open_workingtree()
        tree.remove(path)

    def annotate_cb(self, menu, vfs_file):
        from bzrlib.plugins.gtk.annotate.gannotate import GAnnotateWindow
        controldir, path = self._open_bzrdir(vfs_file)
        win = GAnnotateWindow()
        win.annotate(controldir.open_workingtree(), controldir.open_branch(), path)
        Gtk.main()

    def clone_cb(self, menu, vfs_file=None):
        from bzrlib.plugins.gtk.branch import BranchDialog
        controldir, path = self._open_bzrdir(vfs_file)

        dialog = BranchDialog(vfs_file.get_name())
        response = dialog.run()
        if response != Gtk.ResponseType.NONE:
            dialog.hide()
            dialog.destroy()

    def commit_cb(self, menu, vfs_file=None):
        controldir, path = self._open_bzrdir(vfs_file)
        tree = controldir.open_workingtree()

        from bzrlib.plugins.gtk.commit import CommitDialog
        dialog = CommitDialog(tree, path)
        response = dialog.run()
        if response != Gtk.ResponseType.NONE:
            dialog.hide()
            dialog.destroy()

    def log_cb(self, menu, vfs_file):
        controldir, path = self._open_bzrdir(vfs_file)
        branch = controldir.open_branch()
        pp = start_viz_window(branch, [branch.last_revision()])
        pp.show()
        Gtk.main()

    def pull_cb(self, menu, vfs_file):
        controldir, path = self._open_bzrdir(vfs_file)
        tree = controldir.open_workingtree()
        from bzrlib.plugins.gtk.pull import PullDialog
        dialog = PullDialog(tree, path)
        dialog.display()
        Gtk.main()

    def merge_cb(self, menu, vfs_file):
        controldir, path = self._open_bzrdir(vfs_file)
        tree = controldir.open_workingtree()
        from bzrlib.plugins.gtk.merge import MergeDialog
        dialog = MergeDialog(tree, path)
        dialog.run()
        dialog.destroy()

    def get_background_items(self, window, vfs_file):
        try:
            controldir, path = self._open_bzrdir(vfs_file)
        except NotBranchError:
            return
        try:
            branch = controldir.open_branch()
        except NotBranchError:
            items = []
            item = Nautilus.MenuItem('BzrNautilus::newtree',
                                 'Make directory versioned',
                                 'Create new Bazaar tree in this folder')
            item.connect('activate', self.newtree_cb, vfs_file)
            items.append(item)

            item = Nautilus.MenuItem('BzrNautilus::clone',
                                 'Checkout Bazaar branch ...',
                                 'Checkout Existing Bazaar Branch')
            item.connect('activate', self.clone_cb, vfs_file)
            items.append(item)
            return items

        items = []

        nautilus_integration = self.check_branch_enabled(branch)
        if not nautilus_integration:
            item = Nautilus.MenuItem('BzrNautilus::enable',
                                     'Enable Bazaar Plugin for this Branch',
                                     'Enable Bazaar plugin for nautilus')
            item.connect('activate', self.toggle_integration, True, vfs_file)
            return [item]
        else:
            item = Nautilus.MenuItem('BzrNautilus::disable',
                                     'Disable Bazaar Plugin this Branch',
                                     'Disable Bazaar plugin for nautilus')
            item.connect('activate', self.toggle_integration, False, vfs_file)
            items.append(item)

        item = Nautilus.MenuItem('BzrNautilus::log',
                             'History ...',
                             'Show Bazaar history')
        item.connect('activate', self.log_cb, vfs_file)
        items.append(item)

        item = Nautilus.MenuItem('BzrNautilus::pull',
                             'Pull ...',
                             'Pull from another branch')
        item.connect('activate', self.pull_cb, vfs_file)
        items.append(item)

        try:
            tree = controldir.open_workingtree()
        except NoWorkingTree:
            item = Nautilus.MenuItem('BzrNautilus::create_tree',
                                 'Create working tree...',
                                 'Create a working tree for this branch')
            item.connect('activate', self.create_tree_cb, vfs_file)
            items.append(item)
        else:
            item = Nautilus.MenuItem('BzrNautilus::merge',
                                 'Merge ...',
                                 'Merge from another branch')
            item.connect('activate', self.merge_cb, vfs_file)
            items.append(item)

            item = Nautilus.MenuItem('BzrNautilus::commit',
                                 'Commit ...',
                                 'Commit Changes')
            item.connect('activate', self.commit_cb, vfs_file)
            items.append(item)

        return items

    def get_file_items(self, window, files):
        items = []

        for vfs_file in files:
            controldir, path = self._open_bzrdir(vfs_file)

            try:
                tree = controldir.open_workingtree()
            except NoWorkingTree:
                continue

            nautilus_integration = self.check_branch_enabled(tree.branch)
            if not nautilus_integration:
                continue

            file_id = tree.path2id(path)
            if file_id is None:
                item = Nautilus.MenuItem('BzrNautilus::add',
                                     'Add',
                                     'Add as versioned file')
                item.connect('activate', self.add_cb, vfs_file)
                items.append(item)

                item = Nautilus.MenuItem('BzrNautilus::ignore',
                                     'Ignore',
                                     'Ignore file for versioning')
                item.connect('activate', self.ignore_cb, vfs_file)
                items.append(item)
            elif tree.is_ignored(path):
                item = Nautilus.MenuItem('BzrNautilus::unignore',
                                     'Unignore',
                                     'Unignore file for versioning')
                item.connect('activate', self.unignore_cb, vfs_file)
                items.append(item)
            else:
                item = Nautilus.MenuItem('BzrNautilus::log',
                                 'History ...',
                                 'List changes')
                item.connect('activate', self.log_cb, vfs_file)
                items.append(item)

                intertree = InterTree.get(tree.basis_tree(), tree)
                if not intertree.file_content_matches(file_id, file_id):
                    item = Nautilus.MenuItem('BzrNautilus::diff',
                                     'View Changes ...',
                                     'Show differences')
                    item.connect('activate', self.diff_cb, vfs_file)
                    items.append(item)

                    item = Nautilus.MenuItem('BzrNautilus::commit',
                                 'Commit ...',
                                 'Commit Changes')
                    item.connect('activate', self.commit_cb, vfs_file)
                    items.append(item)

                item = Nautilus.MenuItem('BzrNautilus::remove',
                                     'Remove',
                                     'Remove this file from versioning')
                item.connect('activate', self.remove_cb, vfs_file)
                items.append(item)

                item = Nautilus.MenuItem('BzrNautilus::annotate',
                             'Annotate ...',
                             'Annotate File Data')
                item.connect('activate', self.annotate_cb, vfs_file)
                items.append(item)
        return items

    def get_columns(self):
        return [
            Nautilus.Column(name="BzrNautilus::bzr_status",
                            attribute="bzr_status",
                            label="Status",
                            description="Version control status"),
            Nautilus.Column(name="BzrNautilus::bzr_revision",
                            attribute="bzr_revision",
                            label="Revision",
                            description="Last change revision"),
            ]

    def update_file_info(self, file):

        if file.get_uri_scheme() != 'file':
            return
        
        try:
            tree, path = WorkingTree.open_containing(file.get_uri())
        except NotBranchError:
            return
        except NoWorkingTree:
            return   

        nautilus_integration = self.check_branch_enabled(tree.branch)
        if not nautilus_integration:
            return

        emblem = None
        status = None

        id = tree.path2id(path)
        if id == None:
            if tree.is_ignored(path):
                status = 'ignored'
                emblem = 'bzr-ignored'
            else:
                status = 'unversioned'
                        
        elif tree.has_filename(path):
            emblem = 'bzr-controlled'
            status = 'unchanged'

            delta = tree.changes_from(tree.branch.basis_tree())
            if delta.touches_file_id(id):
                emblem = 'bzr-modified'
                status = 'modified'
            for f, _, _ in delta.added:
                if f == path:
                    emblem = 'bzr-added'
                    status = 'added'

            for of, f, _, _, _, _ in delta.renamed:
                if f == path:
                    status = 'renamed from %s' % f

        elif tree.branch.basis_tree().has_filename(path):
            emblem = 'bzr-removed'
            status = 'removed'
        else:
            # FIXME: Check for ignored files
            status = 'unversioned'

        if emblem is not None:
            file.add_emblem(emblem)
        file.add_string_attribute('bzr_status', status)

    def check_branch_enabled(self, branch):
        # Supports global disable, but there is currently no UI to do this
        config = branch.get_config_stack()
        return config.get("nautilus_integration")

    def toggle_integration(self, menu, action, vfs_file):
        controldir = self._open_bzrdir(vfs_file)
        branch = controldir.open_branch()
        config = branch.get_config_stack()
        config.set("nautilus_integration", action)
