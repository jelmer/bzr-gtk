import nautilus
import bzrlib
from bzrlib.bzrdir import BzrDir
from bzrlib.errors import NotBranchError
from bzrlib.workingtree import WorkingTree

from bzrlib.plugin import load_plugins
load_plugins()

from bzrlib.plugins.gtk import cmd_visualise, cmd_gannotate

class BzrExtension(nautilus.MenuProvider):
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

        from bzrlib.plugins.gtk.viz.diffwin import DiffWindow
        window = DiffWindow()
        window.set_diff(tree.branch, tree, tree.branch.revision_tree())
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
            BzrDir.create_branch_and_repo(file)

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

        file = vfs_file.get_uri()
        try:
            tree, path = WorkingTree.open_containing(file)
        except NotBranchError:
            return

        from bzrlib.plugins.gtk.clone import CloneDialog
        dialog = CloneDialog(file)
        if dialog.run() != gtk.RESPONSE_CANCEL:
            bzrdir = BzrDir.open(dialog.url)
            bzrdir.sprout(dialog.dest_path)
 
    def commit_cb(self, menu, vfs_file=None):
        # We can only cope with local files
        if vfs_file.get_uri_scheme() != 'file':
            return

        file = vfs_file.get_uri()
        try:
            tree, path = WorkingTree.open_containing(file)
        except NotBranchError:
            return

        from bzrlib.plugins.gtk.commit import GCommitDialog
        dialog = GCommitDialog(tree)
        dialog.set_title(path + " - Commit")
        if dialog.run() != gtk.RESPONSE_CANCEL:
            Commit().commit(working_tree=wt,message=dialog.message,
                            specific_files=dialog.specific_files)

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

    def get_background_items(self, window, vfs_file):
        file = vfs_file.get_uri()
        try:
            tree, path = WorkingTree.open_containing(file)
        except NotBranchError:
            item = nautilus.MenuItem('BzrNautilus::newtree',
                                 'Create new Bazaar tree',
                                 'Create new Bazaar tree in this folder')
            item.connect('activate', self.newtree_cb, vfs_file)
            items.append(item)

            item = nautilus.MenuItem('BzrNautilus::clone',
                                 'Checkout',
                                 'Checkout Existing Bazaar Branch')
            item.connect('activate', self.clone_cb, vfs_file)
            items.append(item)

            return items

        items = []
        item = nautilus.MenuItem('BzrNautilus::log',
                             'Log',
                             'Show Bazaar history')
        item.connect('activate', self.log_cb, vfs_file)
        items.append(item)

        item = nautilus.MenuItem('BzrNautilus::commit',
                             'Commit',
                             'Commit Changes')
        item.connect('activate', self.commit_cb, vfs_file)
        items.append(item)

        return items


    def get_file_items(self, window, files):
        items = []

        for vfs_file in files:
            # We can only cope with local files
            if vfs_file.get_uri_scheme() != 'file':
                return

            file = vfs_file.get_uri()
            try:
                tree, path = WorkingTree.open_containing(file)
            except NotBranchError:
                if not vfs_file.is_directory():
                    return
                item = nautilus.MenuItem('BzrNautilus::newtree',
                                     'Create new Bazaar tree',
                                     'Create new Bazaar tree in %s' % vfs_file.get_name())
                item.connect('activate', self.newtree_cb, vfs_file)
                return item,

            file_class = tree.file_class(path)

            if file_class == '?':
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
            elif file_class == 'I':
                item = nautilus.MenuItem('BzrNautilus::unignore',
                                     'Unignore',
                                     'Unignore file for versioning')
                item.connect('activate', self.unignore_cb, vfs_file)
                items.append(item)
            elif file_class == 'V':
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
