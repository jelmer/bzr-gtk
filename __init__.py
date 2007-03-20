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

__version__ = '0.16.0'
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
from bzrlib.option import Option

import os.path

def import_pygtk():
    try:
        import pygtk
    except ImportError:
        raise errors.BzrCommandError("PyGTK not installed.")
    pygtk.require('2.0')
    return pygtk


def set_ui_factory():
    import_pygtk()
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


class cmd_gpush(Command):
    """ GTK+ push.
    
    """
    takes_args = [ "location?" ]

    def run(self, location="."):
        (br, path) = branch.Branch.open_containing(location)

        pygtk = import_pygtk()
        try:
            import gtk
        except RuntimeError, e:
            if str(e) == "could not open display":
                raise NoDisplayError

        from push import PushDialog

        set_ui_factory()
        dialog = PushDialog(br)
        dialog.run()


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
        wt.lock_read()
        try:
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
        finally:
            wt.unlock()


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
        (br, path) = branch.Branch.open_containing(location)
        br.lock_read()
        br.repository.lock_read()
        try:
            if revision is None:
                revid = br.last_revision()
                if revid is None:
                    return
            else:
                (revno, revid) = revision[0].in_history(br)

            from viz.branchwin import BranchWindow
            import gtk
                
            pp = BranchWindow()
            pp.set_branch(br, revid, limit)
            pp.connect("destroy", lambda w: gtk.main_quit())
            pp.show()
            gtk.main()
        finally:
            br.repository.unlock()
            br.unlock()


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
        from bzrlib.bzrdir import BzrDir

        wt, br, path = BzrDir.open_containing_tree_or_branch(filename)
        if wt is not None:
            tree = wt
        else:
            tree = br.basis_tree()

        file_id = tree.path2id(path)

        if file_id is None:
            raise NotVersionedError(filename)
        if revision is not None:
            if len(revision) != 1:
                raise BzrCommandError("Only 1 revion may be specified.")
            revision_id = revision[0].in_history(br).rev_id
            tree = br.repository.revision_tree(revision_id)
        else:
            revision_id = getattr(tree, 'get_revision_id', lambda: None)()

        window = GAnnotateWindow(all, plain)
        window.connect("destroy", lambda w: gtk.main_quit())
        window.set_title(path + " - gannotate")
        config = GAnnotateConfig(window)
        window.show()
        br.lock_read()
        if wt is not None:
            wt.lock_read()
        try:
            window.annotate(tree, br, file_id)
            window.jump_to_line(line)
            gtk.main()
        finally:
            br.unlock()
            if wt is not None:
                wt.unlock()


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
        br = None
        try:
            (wt, path) = workingtree.WorkingTree.open_containing(filename)
            br = wt.branch
        except NotBranchError, e:
            path = e.path
        except NoWorkingTree, e:
            path = e.base
            try:
                (br, path) = branch.Branch.open_containing(path)
            except NotBranchError, e:
                path = e.path


        commit = CommitDialog(wt, path, not br)
        commit.run()


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


class cmd_gpreferences(Command):
    """ GTK+ preferences dialog.

    """
    def run(self):
        pygtk = import_pygtk()
        try:
            import gtk
        except RuntimeError, e:
            if str(e) == "could not open display":
                raise NoDisplayError

        from bzrlib.plugins.gtk.preferences import PreferencesWindow

        set_ui_factory()
        dialog = PreferencesWindow()
        dialog.run()



class cmd_gmissing(Command):
    """ GTK+ missing revisions dialog.

    """
    takes_args = ["other_branch?"]
    def run(self, other_branch=None):
        pygtk = import_pygtk()
        try:
            import gtk
        except RuntimeError, e:
            if str(e) == "could not open display":
                raise NoDisplayError

        from bzrlib.plugins.gtk.missing import MissingWindow
        from bzrlib.branch import Branch

        local_branch = Branch.open_containing(".")[0]
        if other_branch is None:
            other_branch = local_branch.get_parent()
            
            if other_branch is None:
                raise errors.BzrCommandError("No peer location known or specified.")
        remote_branch = Branch.open_containing(other_branch)[0]
        set_ui_factory()
        local_branch.lock_read()
        try:
            remote_branch.lock_read()
            try:
                dialog = MissingWindow(local_branch, remote_branch)
                dialog.run()
            finally:
                remote_branch.unlock()
        finally:
            local_branch.unlock()


commands = [
    cmd_gmissing, 
    cmd_gpreferences, 
    cmd_gconflicts, 
    cmd_gstatus,
    cmd_gcommit, 
    cmd_gannotate, 
    cmd_visualise, 
    cmd_gdiff,
    cmd_gpush, 
    cmd_gcheckout, 
    cmd_gbranch 
    ]

for cmd in commands:
    register_command(cmd)

import gettext
gettext.install('olive-gtk')

class NoDisplayError(BzrCommandError):
    """gtk could not find a proper display"""

    def __str__(self):
        return "No DISPLAY. Unable to run GTK+ application."

def test_suite():
    from unittest import TestSuite
    import tests
    import sys
    default_encoding = sys.getdefaultencoding()
    try:
        result = TestSuite()
        result.addTest(tests.test_suite())
    finally:
        if sys.getdefaultencoding() != default_encoding:
            reload(sys)
            sys.setdefaultencoding(default_encoding)
    return result
