# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""GTK+ frontends to Bazaar commands """

import bzrlib

__version__ = '0.15.0'
version_info = tuple(int(n) for n in __version__.split('.'))


def check_bzrlib_version(desired):
    """Check that bzrlib is compatible.

    If version is < bzr-gtk version, assume incompatible.
    If version == bzr-gtk version, assume completely compatible
    If version == bzr-gtk version + 1, assume compatible, with deprecations
    Otherwise, assume incompatible.
    """
    desired_plus = (desired[0], desired[1]+1)
    bzrlib_version = bzrlib.version_info[:2]
    if bzrlib_version == desired:
        return
    try:
        from bzrlib.trace import warning
    except ImportError:
        # get the message out any way we can
        from warnings import warn as warning
    if bzrlib_version < desired:
        warning('Installed bzr version %s is too old to be used with bzr-gtk'
                ' %s.' % (bzrlib.__version__, __version__))
        # Not using BzrNewError, because it may not exist.
        raise Exception, ('Version mismatch', version_info)
    else:
        warning('bzr-gtk is not up to date with installed bzr version %s.'
                ' \nThere should be a newer version available, e.g. %i.%i.' 
                % (bzrlib.__version__, bzrlib_version[0], bzrlib_version[1]))
        if bzrlib_version != desired_plus:
            raise Exception, 'Version mismatch'


check_bzrlib_version(version_info[:2])

from bzrlib.trace import warning
if __name__ != 'bzrlib.plugins.gtk':
    warning("Not running as bzrlib.plugins.gtk, things may break.")

from bzrlib.lazy_import import lazy_import
lazy_import(globals(), """
from bzrlib import (
    branch,
    errors,
    workingtree,
    )
""")

from bzrlib.commands import Command, register_command, display_command
from bzrlib.errors import NotVersionedError, BzrCommandError, NoSuchFile
from bzrlib.commands import Command, register_command
from bzrlib.option import Option
from bzrlib.bzrdir import BzrDir

import os.path

def import_pygtk():
    try:
        import pygtk
    except ImportError:
        raise errors.BzrCommandError("PyGTK not installed.")
    pygtk.require('2.0')
    return pygtk


def set_ui_factory():
    pygtk = import_pygtk()
    from ui import GtkUIFactory
    import bzrlib.ui
    bzrlib.ui.ui_factory = GtkUIFactory()


class cmd_gbranch(Command):
    """GTK+ branching.
    
    """

    def run(self):
        pygtk = import_pygtk()
        try:
            import gtk
        except RuntimeError, e:
            if str(e) == "could not open display":
                raise NoDisplayError

        from bzrlib.plugins.gtk.branch import BranchDialog

        set_ui_factory()
        dialog = BranchDialog(os.path.abspath('.'))
        dialog.run()

register_command(cmd_gbranch)

class cmd_gcheckout(Command):
    """ GTK+ checkout.
    
    """
    
    def run(self):
        pygtk = import_pygtk()
        try:
            import gtk
        except RuntimeError, e:
            if str(e) == "could not open display":
                raise NoDisplayError

        from bzrlib.plugins.gtk.checkout import CheckoutDialog

        set_ui_factory()
        dialog = CheckoutDialog(os.path.abspath('.'))
        dialog.run()

register_command(cmd_gcheckout)

class cmd_gpush(Command):
    """ GTK+ push.
    
    """
    takes_args = [ "location?" ]
    
    def run(self, location="."):
        (branch, path) = branch.Branch.open_containing(location)
        
        pygtk = import_pygtk()
        try:
            import gtk
        except RuntimeError, e:
            if str(e) == "could not open display":
                raise NoDisplayError

        from push import PushDialog

        set_ui_factory()
        dialog = PushDialog(branch)
        dialog.run()

register_command(cmd_gpush)

class cmd_gdiff(Command):
    """Show differences in working tree in a GTK+ Window.
    
    Otherwise, all changes for the tree are listed.
    """
    takes_args = ['filename?']
    takes_options = ['revision']

    @display_command
    def run(self, revision=None, filename=None):
        set_ui_factory()
        wt = workingtree.WorkingTree.open_containing(".")[0]
        branch = wt.branch
        if revision is not None:
            if len(revision) == 1:
                tree1 = wt
                revision_id = revision[0].in_history(branch).rev_id
                tree2 = branch.repository.revision_tree(revision_id)
            elif len(revision) == 2:
                revision_id_0 = revision[0].in_history(branch).rev_id
                tree2 = branch.repository.revision_tree(revision_id_0)
                revision_id_1 = revision[1].in_history(branch).rev_id
                tree1 = branch.repository.revision_tree(revision_id_1)
        else:
            tree1 = wt
            tree2 = tree1.basis_tree()

        from diff import DiffWindow
        import gtk
        window = DiffWindow()
        window.connect("destroy", gtk.main_quit)
        window.set_diff("Working Tree", tree1, tree2)
        if filename is not None:
            tree_filename = wt.relpath(filename)
            try:
                window.set_file(tree_filename)
            except NoSuchFile:
                if (tree1.inventory.path2id(tree_filename) is None and 
                    tree2.inventory.path2id(tree_filename) is None):
                    raise NotVersionedError(filename)
                raise BzrCommandError('No changes found for file "%s"' % 
                                      filename)
        window.show()

        gtk.main()

register_command(cmd_gdiff)

class cmd_visualise(Command):
    """Graphically visualise this branch.

    Opens a graphical window to allow you to see the history of the branch
    and relationships between revisions in a visual manner,

    The default starting point is latest revision on the branch, you can
    specify a starting point with -r revision.
    """
    takes_options = [
        "revision",
        Option('limit', "maximum number of revisions to display",
               int, 'count')]
    takes_args = [ "location?" ]
    aliases = [ "visualize", "vis", "viz" ]

    def run(self, location=".", revision=None, limit=None):
        set_ui_factory()
        (branch, path) = branch.Branch.open_containing(location)
        branch.lock_read()
        branch.repository.lock_read()
        try:
            if revision is None:
                revid = branch.last_revision()
                if revid is None:
                    return
            else:
                (revno, revid) = revision[0].in_history(branch)

            from viz.branchwin import BranchWindow
            import gtk
                
            pp = BranchWindow()
            pp.set_branch(branch, revid, limit)
            pp.connect("destroy", lambda w: gtk.main_quit())
            pp.show()
            gtk.main()
        finally:
            branch.repository.unlock()
            branch.unlock()


register_command(cmd_visualise)

class cmd_gannotate(Command):
    """GTK+ annotate.
    
    Browse changes to FILENAME line by line in a GTK+ window.
    """

    takes_args = ["filename", "line?"]
    takes_options = [
        Option("all", help="show annotations on all lines"),
        Option("plain", help="don't highlight annotation lines"),
        Option("line", type=int, argname="lineno",
               help="jump to specified line number"),
        "revision",
    ]
    aliases = ["gblame", "gpraise"]
    
    def run(self, filename, all=False, plain=False, line='1', revision=None):
        pygtk = import_pygtk()

        try:
            import gtk
        except RuntimeError, e:
            if str(e) == "could not open display":
                raise NoDisplayError
        set_ui_factory()

        try:
            line = int(line)
        except ValueError:
            raise BzrCommandError('Line argument ("%s") is not a number.' % 
                                  line)

        from annotate.gannotate import GAnnotateWindow
        from annotate.config import GAnnotateConfig

        try:
            (tree, path) = workingtree.WorkingTree.open_containing(filename)
            branch = tree.branch
        except errors.NoWorkingTree:
            (branch, path) = branch.Branch.open_containing(filename)
            tree = branch.basis_tree()

        file_id = tree.path2id(path)

        if file_id is None:
            raise NotVersionedError(filename)
        if revision is not None:
            if len(revision) != 1:
                raise BzrCommandError("Only 1 revion may be specified.")
            revision_id = revision[0].in_history(branch).rev_id
            tree = branch.repository.revision_tree(revision_id)
        else:
            revision_id = getattr(tree, 'get_revision_id', lambda: None)()

        window = GAnnotateWindow(all, plain)
        window.connect("destroy", lambda w: gtk.main_quit())
        window.set_title(path + " - gannotate")
        config = GAnnotateConfig(window)
        window.show()
        branch.lock_read()
        try:
            window.annotate(tree, branch, file_id)
        finally:
            branch.unlock()
        window.jump_to_line(line)
        
        gtk.main()

register_command(cmd_gannotate)

class cmd_gcommit(Command):
    """GTK+ commit dialog

    Graphical user interface for committing revisions"""
    
    aliases = [ "gci" ]
    takes_args = []
    takes_options = []

    def run(self, filename=None):
        import os
        pygtk = import_pygtk()

        try:
            import gtk
        except RuntimeError, e:
            if str(e) == "could not open display":
                raise NoDisplayError

        set_ui_factory()
        from commit import CommitDialog
        from bzrlib.commit import Commit
        from bzrlib.errors import (BzrCommandError,
                                   NotBranchError,
                                   NoWorkingTree,
                                   PointlessCommit,
                                   ConflictsInTree,
                                   StrictCommitFailed)

        wt = None
        branch = None
        try:
            (wt, path) = workingtree.WorkingTree.open_containing(filename)
            branch = wt.branch
        except NotBranchError, e:
            path = e.path
        except NoWorkingTree, e:
            path = e.base
            try:
                (branch, path) = branch.Branch.open_containing(path)
            except NotBranchError, e:
                path = e.path


        commit = CommitDialog(wt, path, not branch)
        commit.run()

register_command(cmd_gcommit)

class cmd_gstatus(Command):
    """GTK+ status dialog

    Graphical user interface for showing status 
    information."""
    
    aliases = [ "gst" ]
    takes_args = ['PATH?']
    takes_options = []

    def run(self, path='.'):
        import os
        pygtk = import_pygtk()

        try:
            import gtk
        except RuntimeError, e:
            if str(e) == "could not open display":
                raise NoDisplayError

        set_ui_factory()
        from status import StatusDialog
        (wt, wt_path) = workingtree.WorkingTree.open_containing(path)
        status = StatusDialog(wt, wt_path)
        status.connect("destroy", gtk.main_quit)
        status.run()

register_command(cmd_gstatus)

class cmd_gconflicts(Command):
    """ GTK+ push.
    
    """
    def run(self):
        (wt, path) = workingtree.WorkingTree.open_containing('.')
        
        pygtk = import_pygtk()
        try:
            import gtk
        except RuntimeError, e:
            if str(e) == "could not open display":
                raise NoDisplayError

        from bzrlib.plugins.gtk.conflicts import ConflictsDialog

        set_ui_factory()
        dialog = ConflictsDialog(wt)
        dialog.run()

register_command(cmd_gconflicts)

import gettext
gettext.install('olive-gtk')

class NoDisplayError(BzrCommandError):
    """gtk could not find a proper display"""

    def __str__(self):
        return "No DISPLAY. Unable to run GTK+ application."

def test_suite():
    from unittest import TestSuite
    import tests
    result = TestSuite()
    result.addTest(tests.test_suite())
    return result
