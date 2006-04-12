import nautilus
import bzrlib
from bzrlib.bzrdir import BzrDir

class BzrExtension(nautilus.MenuProvider):
    def __init__(self):
        pass

    def add_cb(self, menu, files):
        return

    def get_file_items(self, window, files):
        trees = []
        items = []
        file_class = None

        for file in files:
            try:
                dir = BzrDir.open_containing(file)
            except NotBranchError:
                return

            tree = dir.open_workingtree()

            trees.append(tree)

            fc = tree.file_class(file)
            if not file_class:
                file_class = fc
            elif fc != file_class:
                return

        if file_class == '?':
            item = nautilus.MenuItem('Nautilus::add',
                                 'Add',
                                 'Add as versioned file')
            item.connect('activate', self.add_cb, files)
            items.append(item)

            item = nautilus.MenuItem('Nautilus::ignore',
                                 'Ignore',
                                 'Ignore file for versioning')
            item.connect('activate', self.ignore_cb, files)
            items.append(item)
        elif file_class == 'I':
            item = nautilus.MenuItem('Nautilus::unignore',
                                 'Unignore',
                                 'Unignore file for versioning')
            item.connect('activate', self.unignore_cb, files)
            items.append(item)
        elif file_class == 'V':
            item = nautilus.MenuItem('Nautilus::log',
                                 'Log',
                                 'List changes')
            item.connect('activate', self.log_cb, files)
            items.append(item)

            item = nautilus.MenuItem('Nautilus::diff',
                                 'Diff',
                                 'Show differences')
            item.connect('activate', self.diff_cb, files)
            items.append(item)

            item = nautilus.MenuItem('Nautilus::remove',
                                 'Remove',
                                 'Remove this file from versioning')
            item.connect('activate', self.remove_cb, files)
            items.append(item)

        return items
