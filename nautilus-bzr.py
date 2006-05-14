import nautilus
import bzrlib
from bzrlib.bzrdir import BzrDir
from bzrlib.errors import NotBranchError
from bzrlib.workingtree import WorkingTree

from bzrlib.plugin import load_plugins
load_plugins()

try:
    from bzrlib.plugins.bzrk import cmd_visualise
    have_bzrk = True
except ImportError:
    have_bzrk = False

try:
    from bzrlib.plugins.gannotate import cmd_gannotate
    have_gannotate = True
except ImportError:
    have_gannotate = False

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

        return

    def log_cb(self, menu, vfs_file):
        # We can only cope with local files
        if vfs_file.get_uri_scheme() != 'file':
            return

        file = vfs_file.get_uri()
        try:
            tree, path = WorkingTree.open_containing(file)
        except NotBranchError:
            return

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
            return

        return

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

        return

    def annotate_cb(self, menu, vfs_file):
        # We can only cope with local files
        if vfs_file.get_uri_scheme() != 'file':
            return

        file = vfs_file.get_uri()

        vis = cmd_gannotate()
        vis.run(file)

        return
 

    def visualise_cb(self, menu, vfs_file):
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
            return item,

        if have_bzrk:
            item = nautilus.MenuItem('BzrNautilus::visualise',
                                 'Visualise Bazaar history',
                                 'Visualise Bazaar history')
            item.connect('activate', self.visualise_cb, vfs_file)
            return item,

        return


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

                if have_gannotate:
                    item = nautilus.MenuItem('BzrNautilus::annotate',
                                 'Annotate',
                                 'Annotate File Data')
                    item.connect('activate', self.annotate_cb, vfs_file)
                    items.append(item)
    
        return items
