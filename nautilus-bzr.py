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

from gi.repository import Gtk, GObject, Nautilus
from bzrlib.controldir import ControlDir
from bzrlib.errors import (
    NotBranchError,
    NoWorkingTree,
    )
from bzrlib.ignores import tree_ignores_add_patterns
from bzrlib.tree import InterTree

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

    @classmethod
    def _open_tree(cls, vfs_file):
        controldir, path = cls._open_bzrdir(vfs_file)
        return controldir.open_workingtree(), path

    def add_cb(self, menu, tree, path):
        tree.add(path)

    def ignore_cb(self, menu, tree, path):
        # We can only cope with local files
        tree_ignores_add_patterns(tree, [path])
        #FIXME: Add path to ignore file

    def unignore_cb(self, menu, tree, path):
        pass
        # We can only cope with local files
        #FIXME

    def diff_cb(self, menu, tree, path=None):
        from bzrlib.plugins.gtk.diff import DiffWindow
        window = DiffWindow()
        window.set_diff(tree.branch._get_nick(local=True), tree, 
                        tree.branch.basis_tree())
        window.show()

    def newtree_cb(self, menu, vfs_file):
        controldir, path = self._open_bzrdir(vfs_file)
        controldir.create_workingtree()

    def remove_cb(self, menu, tree, path):
        tree.remove(path)

    def annotate_cb(self, menu, tree, path, file_id):
        from bzrlib.plugins.gtk.annotate.gannotate import GAnnotateWindow
        win = GAnnotateWindow()
        win.show()
        win.annotate(tree, tree.branch, file_id)
        Gtk.main()

    def clone_cb(self, menu, vfs_file=None):
        from bzrlib.plugins.gtk.branch import BranchDialog
        controldir, path = self._open_bzrdir(vfs_file)

        dialog = BranchDialog(vfs_file.get_name())
        response = dialog.run()
        if response != Gtk.ResponseType.NONE:
            dialog.hide()
            dialog.destroy()

    def commit_cb(self, menu, tree, path=None):
        from bzrlib.plugins.gtk.commit import CommitDialog
        dialog = CommitDialog(tree, path)
        response = dialog.run()
        if response != Gtk.ResponseType.NONE:
            dialog.hide()
            dialog.destroy()

    def log_cb(self, menu, controldir, path=None):
        from bzrlib.plugins.gtk.viz import BranchWindow
        branch = controldir.open_branch()
        pp = BranchWindow(branch, [branch.last_revision()], None)
        pp.show()
        Gtk.main()

    def pull_cb(self, menu, controldir, path=None):
        from bzrlib.plugins.gtk.pull import PullDialog
        dialog = PullDialog(controldir.open_workingtree(), path)
        dialog.display()
        Gtk.main()

    def merge_cb(self, menu, tree, path=None):
        from bzrlib.plugins.gtk.merge import MergeDialog
        dialog = MergeDialog(tree, path)
        dialog.run()
        dialog.destroy()

    def create_tree_cb(self, menu, controldir):
        controldir.create_workingtree()

    def get_background_items(self, window, vfs_file):
        try:
            controldir, path = self._open_bzrdir(vfs_file)
        except NotBranchError:
            return
        try:
            branch = controldir.open_branch()
        except NotBranchError:
            items = []
            item = Nautilus.MenuItem(name='BzrNautilus::newtree',
                                 label='Make directory versioned',
                                 tip='Create new Bazaar tree in this folder',
                                 icon='')
            item.connect('activate', self.newtree_cb, vfs_file)
            items.append(item)

            item = Nautilus.MenuItem(name='BzrNautilus::clone',
                                 label='Checkout Bazaar branch ...',
                                 tip='Checkout Existing Bazaar Branch',
                                 icon='')
            item.connect('activate', self.clone_cb, vfs_file)
            items.append(item)
            return items

        items = []

        nautilus_integration = self.check_branch_enabled(branch)
        if not nautilus_integration:
            item = Nautilus.MenuItem(name='BzrNautilus::enable',
                                     label='Enable Bazaar Plugin for this Branch',
                                     tip='Enable Bazaar plugin for nautilus',
                                     icon='')
            item.connect('activate', self.toggle_integration, True, branch)
            return [item]
        else:
            item = Nautilus.MenuItem(name='BzrNautilus::disable',
                                     label='Disable Bazaar Plugin this Branch',
                                     tip='Disable Bazaar plugin for nautilus',
                                     icon='')
            item.connect('activate', self.toggle_integration, False, branch)
            items.append(item)

        item = Nautilus.MenuItem(name='BzrNautilus::log',
                             label='History ...',
                             tip='Show Bazaar history',
                             icon='')
        item.connect('activate', self.log_cb, controldir)
        items.append(item)

        item = Nautilus.MenuItem(name='BzrNautilus::pull',
                             label='Pull ...',
                             tip='Pull from another branch',
                             icon='')
        item.connect('activate', self.pull_cb, controldir)
        items.append(item)

        try:
            tree = controldir.open_workingtree()
        except NoWorkingTree:
            item = Nautilus.MenuItem(name='BzrNautilus::create_tree',
                                 label='Create working tree...',
                                 tip='Create a working tree for this branch',
                                 icon='')
            item.connect('activate', self.create_tree_cb, controldir)
            items.append(item)
        else:
            item = Nautilus.MenuItem(name='BzrNautilus::merge',
                                 label='Merge ...',
                                 tip='Merge from another branch',
                                 icon='')
            item.connect('activate', self.merge_cb, tree, path)
            items.append(item)

            item = Nautilus.MenuItem(name='BzrNautilus::commit',
                                 label='Commit ...',
                                 tip='Commit Changes',
                                 icon='')
            item.connect('activate', self.commit_cb, tree, path)
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
                item = Nautilus.MenuItem(name='BzrNautilus::add',
                                     label='Add',
                                     tip='Add as versioned file',
                                     icon='')
                item.connect('activate', self.add_cb, tree, path)
                items.append(item)

                item = Nautilus.MenuItem(name='BzrNautilus::ignore',
                                     label='Ignore',
                                     tip='Ignore file for versioning',
                                     icon='')
                item.connect('activate', self.ignore_cb, tree, path)
                items.append(item)
            elif tree.is_ignored(path):
                item = Nautilus.MenuItem(name='BzrNautilus::unignore',
                                     label='Unignore',
                                     tip='Unignore file for versioning',
                                     icon='')
                item.connect('activate', self.unignore_cb, tree, path)
                items.append(item)
            else:
                item = Nautilus.MenuItem(name='BzrNautilus::log',
                                 label='History ...',
                                 tip='List changes',
                                 icon='')
                item.connect('activate', self.log_cb, controldir, path)
                items.append(item)

                intertree = InterTree.get(tree.basis_tree(), tree)
                if not intertree.file_content_matches(file_id, file_id):
                    item = Nautilus.MenuItem(name='BzrNautilus::diff',
                                     label='View Changes ...',
                                     tip='Show differences',
                                     icon='')
                    item.connect('activate', self.diff_cb, tree, path)
                    items.append(item)

                    item = Nautilus.MenuItem(name='BzrNautilus::commit',
                                 label='Commit ...',
                                 tip='Commit Changes',
                                 icon='')
                    item.connect('activate', self.commit_cb, tree, path)
                    items.append(item)

                item = Nautilus.MenuItem(name='BzrNautilus::remove',
                                     label='Remove',
                                     tip='Remove this file from versioning',
                                     icon='')
                item.connect('activate', self.remove_cb, tree, path)
                items.append(item)

                item = Nautilus.MenuItem(name='BzrNautilus::annotate',
                             label='Annotate ...',
                             tip='Annotate File Data',
                             icon='')
                item.connect('activate', self.annotate_cb, tree, path, file_id)
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

    def _file_summary(self, tree, basis_tree, intertree, path):
        file_revision = ""
        emblem = None

        file_id = tree.path2id(path)
        if file_id is None:
            if tree.is_ignored(path):
                status = 'ignored'
                emblem = 'bzr-ignored'
            else:
                status = 'unversioned'
            file_revision = "N/A"
        elif tree.has_filename(path): # Still present
            if not intertree.file_content_matches(file_id, file_id):
                if not basis_tree.has_id(file_id):
                    emblem = 'bzr-added'
                    status = 'added'
                    file_revision = "new file"
                elif basis_tree.path2id(file_id) != path:
                    status = 'bzr-renamed'
                    status = 'renamed from %s' % basis_tree.path2id(file_id)
                else:
                    emblem = 'bzr-modified'
                    status = 'modified'
            else:
                emblem = 'bzr-controlled'
                status = 'unchanged'
        elif basis_tree.has_filename(path):
            emblem = 'bzr-removed'
            status = 'removed'
        else:
            # FIXME: Check for ignored files
            status = 'unversioned'
        return (status, emblem, file_revision)

    def update_file_info(self, vfs_file):
        try:
            controldir, path = self._open_bzrdir(vfs_file)
        except NotBranchError:
            return

        try:
            tree = controldir.open_workingtree()
        except NoWorkingTree:
            return

        tree.lock_read()
        try:
            nautilus_integration = self.check_branch_enabled(tree.branch)
            if not nautilus_integration:
                return

            basis_tree = tree.basis_tree()
            intertree = InterTree.get(basis_tree, tree)

            basis_tree.lock_read()
            try:
                (status, emblem, file_revision) = self._file_summary(tree, basis_tree, intertree, path)
            finally:
                basis_tree.unlock()
            if emblem is not None:
                vfs_file.add_emblem(emblem)
            vfs_file.add_string_attribute('bzr_status', status)
            vfs_file.add_string_attribute('bzr_revision', file_revision)
        finally:
            tree.unlock()

    def check_branch_enabled(self, branch):
        # Supports global disable, but there is currently no UI to do this
        config = branch.get_config_stack()
        return config.get("nautilus_integration")

    def toggle_integration(self, menu, action, branch):
        config = branch.get_config_stack()
        config.set("nautilus_integration", action)

    def get_property_pages(self, files):
        pages = []
        for vfs_file in files:
            try:
                controldir, path = self._open_bzrdir(vfs_file)
            except NotBranchError:
                continue

            try:
                tree = controldir.open_workingtree()
            except NoWorkingTree:
                continue

            tree.lock_read()
            try:
                property_label = Gtk.Label('Version Control')
                property_label.show()

                file_id = tree.path2id(path)

                table = Gtk.Table(homogeneous=False, columns=2, rows=2)

                table.attach(Gtk.Label('File id:'), 0, 1, 0, 1)
                table.attach(Gtk.Label(file_id), 1, 2, 0, 1)

                table.attach(Gtk.Label('SHA1Sum:'), 0, 1, 1, 2)
                table.attach(Gtk.Label(tree.get_file_sha1(file_id, path)), 1, 1, 1, 2)

                table.show_all()
                pages.append(Nautilus.PropertyPage(name="BzrNautilus::version_info",
                             label=property_label, page=table))
            finally:
                tree.unlock()
        return pages
