# Trivial Bazaar plugin for Nautilus
#
# Copyright (C) 2006 Jeff Bailey
# Copyright (C) 2006 Wouter van Heyst
# Copyright (C) 2006-2008 Jelmer Vernooij <jelmer@samba.org>
#
# Published under the GNU GPL

import sys
import gtk
import nautilus
import bzrlib
from bzrlib.branch import Branch
from bzrlib.bzrdir import BzrDir
from bzrlib.errors import NotBranchError, NoWorkingTree, UnsupportedProtocol
from bzrlib.tree import file_status
from bzrlib.workingtree import WorkingTree
from bzrlib.config import GlobalConfig
config = GlobalConfig()
disabled_flag = config.get_user_option('nautilus_integration')

from bzrlib.plugin import load_plugins
load_plugins()

from bzrlib.plugins.gtk import cmd_visualise, cmd_gannotate

class BzrExtension(nautilus.MenuProvider, nautilus.ColumnProvider, nautilus.InfoProvider):
    def __init__(self):
        pass

    def add_cb(self, menu, vfs_file):
        # We can only cope with local files
        if vfs_file.get_uri_scheme() != 'file':
            return

        file = vfs_file.get_uri()
        try:
            tree, path = WorkingTree.open_containing(file)
        except NotBranchError:
            return

        tree.add(path)

        return

    def ignore_cb(self, menu, vfs_file):
        # We can only cope with local files
        if vfs_file.get_uri_scheme() != 'file':
            return

        file = vfs_file.get_uri()
        try:
            tree, path = WorkingTree.open_containing(file)
        except NotBranchError:
            return

        #FIXME

        return

    def unignore_cb(self, menu, vfs_file):
        # We can only cope with local files
        if vfs_file.get_uri_scheme() != 'file':
            return

        file = vfs_file.get_uri()
        try:
            tree, path = WorkingTree.open_containing(file)
        except NotBranchError:
            return

        #FIXME

        return

    def diff_cb(self, menu, vfs_file):
        # We can only cope with local files
        if vfs_file.get_uri_scheme() != 'file':
            return

        file = vfs_file.get_uri()
        try:
            tree, path = WorkingTree.open_containing(file)
        except NotBranchError:
            return

        from bzrlib.plugins.gtk.diff import DiffWindow
        window = DiffWindow()
        window.set_diff(tree.branch.nick, tree, tree.branch.basis_tree())
        window.show()

        return

    def newtree_cb(self, menu, vfs_file):
        # We can only cope with local files
        if vfs_file.get_uri_scheme() != 'file':
            return

        file = vfs_file.get_uri()

        # We only want to continue here if we get a NotBranchError
        try:
            tree, path = WorkingTree.open_containing(file)
        except NotBranchError:
            BzrDir.create_standalone_workingtree(file)

    def remove_cb(self, menu, vfs_file):
        # We can only cope with local files
        if vfs_file.get_uri_scheme() != 'file':
            return

        file = vfs_file.get_uri()
        try:
            tree, path = WorkingTree.open_containing(file)
        except NotBranchError:
            return

        tree.remove(path)

    def annotate_cb(self, menu, vfs_file):
        # We can only cope with local files
        if vfs_file.get_uri_scheme() != 'file':
            return

        file = vfs_file.get_uri()

        vis = cmd_gannotate()
        vis.run(file)

    def clone_cb(self, menu, vfs_file=None):
        # We can only cope with local files
        if vfs_file.get_uri_scheme() != 'file':
            return

        from bzrlib.plugins.gtk.branch import BranchDialog
        
        dialog = BranchDialog(vfs_file.get_name())
        response = dialog.run()
        if response != gtk.RESPONSE_NONE:
            dialog.hide()
            dialog.destroy()
 
    def commit_cb(self, menu, vfs_file=None):
        # We can only cope with local files
        if vfs_file.get_uri_scheme() != 'file':
            return

        file = vfs_file.get_uri()
        tree = None
        branch = None
        try:
            tree, path = WorkingTree.open_containing(file)
            branch = tree.branch
        except NotBranchError, e:
            path = e.path
            #return
        except NoWorkingTree, e:
            path = e.base
            try:
                (branch, path) = Branch.open_containing(path)
            except NotBranchError, e:
                path = e.path

        from bzrlib.plugins.gtk.commit import CommitDialog
        dialog = CommitDialog(tree, path)
        response = dialog.run()
        if response != gtk.RESPONSE_NONE:
            dialog.hide()
            dialog.destroy()

    def log_cb(self, menu, vfs_file):
        # We can only cope with local files
        if vfs_file.get_uri_scheme() != 'file':
            return

        file = vfs_file.get_uri()

        # We only want to continue here if we get a NotBranchError
        try:
            tree, path = WorkingTree.open_containing(file)
        except NotBranchError:
            return

        vis = cmd_visualise()
        vis.run(file)

        return

    def pull_cb(self, menu, vfs_file):
        # We can only cope with local files
        if vfs_file.get_uri_scheme() != 'file':
            return

        file = vfs_file.get_uri()

        # We only want to continue here if we get a NotBranchError
        try:
            tree, path = WorkingTree.open_containing(file)
        except NotBranchError:
            return

        from bzrlib.plugins.gtk.pull import PullDialog
        dialog = PullDialog(tree, path)
        dialog.display()
        gtk.main()

    def merge_cb(self, menu, vfs_file):
        # We can only cope with local files
        if vfs_file.get_uri_scheme() != 'file':
            return

        file = vfs_file.get_uri()

        # We only want to continue here if we get a NotBranchError
        try:
            tree, path = WorkingTree.open_containing(file)
        except NotBranchError:
            return

        from bzrlib.plugins.gtk.merge import MergeDialog
        dialog = MergeDialog(tree, path)
        dialog.display()
        gtk.main()

    def get_background_items(self, window, vfs_file):
        if disabled_flag == 'False':
            return

        items = []
        file = vfs_file.get_uri()
        try:
            tree, path = WorkingTree.open_containing(file)
        except UnsupportedProtocol:
            return
        except NotBranchError:
            item = nautilus.MenuItem('BzrNautilus::newtree',
                                 'Make directory versioned',
                                 'Create new Bazaar tree in this folder')
            item.connect('activate', self.newtree_cb, vfs_file)
            items.append(item)

            item = nautilus.MenuItem('BzrNautilus::clone',
                                 'Checkout Bazaar branch',
                                 'Checkout Existing Bazaar Branch')
            item.connect('activate', self.clone_cb, vfs_file)
            items.append(item)

            return items
        except NoWorkingTree:
            return

        item = nautilus.MenuItem('BzrNautilus::log',
                             'Log',
                             'Show Bazaar history')
        item.connect('activate', self.log_cb, vfs_file)
        items.append(item)

        item = nautilus.MenuItem('BzrNautilus::pull',
                             'Pull',
                             'Pull from another branch')
        item.connect('activate', self.pull_cb, vfs_file)
        items.append(item)

        item = nautilus.MenuItem('BzrNautilus::merge',
                             'Merge',
                             'Merge from another branch')
        item.connect('activate', self.merge_cb, vfs_file)
        items.append(item)

        item = nautilus.MenuItem('BzrNautilus::commit',
                             'Commit',
                             'Commit Changes')
        item.connect('activate', self.commit_cb, vfs_file)
        items.append(item)

        return items

    def get_file_items(self, window, files):
        if disabled_flag == 'False':
            return

        items = []

        wtfiles = {}
        for vfs_file in files:
            # We can only cope with local files
            if vfs_file.get_uri_scheme() != 'file':
                continue

            file = vfs_file.get_uri()
            try:
                tree, path = WorkingTree.open_containing(file)
            except NotBranchError:
                if not vfs_file.is_directory():
                    continue
                item = nautilus.MenuItem('BzrNautilus::newtree',
                                     'Make directory versioned',
                                     'Create new Bazaar tree in %s' % vfs_file.get_name())
                item.connect('activate', self.newtree_cb, vfs_file)
                return item,
            except NoWorkingTree:
                continue
            # Refresh the list of filestatuses in the working tree
            if path not in wtfiles.keys():
                tree.lock_read()
                for rpath, file_class, kind, id, entry in tree.list_files():
                    wtfiles[rpath] = file_class
                tree.unlock()
                wtfiles[u''] = 'V'

            if wtfiles[path] == '?':
                item = nautilus.MenuItem('BzrNautilus::add',
                                     'Add',
                                     'Add as versioned file')
                item.connect('activate', self.add_cb, vfs_file)
                items.append(item)

                item = nautilus.MenuItem('BzrNautilus::ignore',
                                     'Ignore',
                                     'Ignore file for versioning')
                item.connect('activate', self.ignore_cb, vfs_file)
                items.append(item)
            elif wtfiles[path] == 'I':
                item = nautilus.MenuItem('BzrNautilus::unignore',
                                     'Unignore',
                                     'Unignore file for versioning')
                item.connect('activate', self.unignore_cb, vfs_file)
                items.append(item)
            elif wtfiles[path] == 'V':
                item = nautilus.MenuItem('BzrNautilus::log',
                                 'Log',
                                 'List changes')
                item.connect('activate', self.log_cb, vfs_file)
                items.append(item)

                item = nautilus.MenuItem('BzrNautilus::diff',
                                 'Diff',
                                 'Show differences')
                item.connect('activate', self.diff_cb, vfs_file)
                items.append(item)

                item = nautilus.MenuItem('BzrNautilus::remove',
                                     'Remove',
                                     'Remove this file from versioning')
                item.connect('activate', self.remove_cb, vfs_file)
                items.append(item)

                item = nautilus.MenuItem('BzrNautilus::annotate',
                             'Annotate',
                             'Annotate File Data')
                item.connect('activate', self.annotate_cb, vfs_file)
                items.append(item)

                item = nautilus.MenuItem('BzrNautilus::commit',
                             'Commit',
                             'Commit Changes')
                item.connect('activate', self.commit_cb, vfs_file)
                items.append(item)

        return items

    def get_columns(self):
        return nautilus.Column("BzrNautilus::bzr_status",
                               "bzr_status",
                               "Bzr Status",
                               "Version control status"),

    def update_file_info(self, file):
        if disabled_flag == 'False':
            return

        if file.get_uri_scheme() != 'file':
            return
        
        try:
            tree, path = WorkingTree.open_containing(file.get_uri())
        except NotBranchError:
            return
        except NoWorkingTree:
            return

        emblem = None
        status = None

        if tree.has_filename(path):
            emblem = 'bzr-controlled'
            status = 'unchanged'
            id = tree.path2id(path)

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

    def enable_integration(self):
        config.set_user_option('nautilus_integration','True')

    def disable_integration(self):
        config.set_user_option('nautilus_integration','False')
