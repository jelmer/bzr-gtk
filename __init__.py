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

from bzrlib.commands import Command, register_command, display_command
from bzrlib.errors import NotVersionedError, BzrCommandError, NoSuchFile
from bzrlib.commands import Command, register_command
from bzrlib.option import Option
from bzrlib.branch import Branch
from bzrlib.workingtree import WorkingTree
from bzrlib.bzrdir import BzrDir

__version__ = '0.11.0'

class cmd_gbranch(Command):
    """GTK+ branching.
    
    """

    def run(self):
        import pygtk
        pygtk.require("2.0")
        try:
            import gtk
        except RuntimeError, e:
            if str(e) == "could not open display":
                raise NoDisplayError

        from bzrlib.plugins.gtk.olive.branch import BranchDialog

        window = BranchDialog('.')
        window.display()

register_command(cmd_gbranch)

class cmd_gdiff(Command):
    """Show differences in working tree in a GTK+ Window.
    
    Otherwise, all changes for the tree are listed.
    """
    takes_args = ['filename?']
    takes_options = ['revision']

    @display_command
    def run(self, revision=None, filename=None):
        wt = WorkingTree.open_containing(".")[0]
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

        from bzrlib.plugins.gtk.viz.diffwin import DiffWindow
        import gtk
        window = DiffWindow()
        window.connect("destroy", lambda w: gtk.main_quit())
        window.set_diff("Working Tree", tree1, tree2)
        if filename is not None:
            tree_filename = tree1.relpath(filename)
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
        (branch, path) = Branch.open_containing(location)
        branch.lock_read()
        branch.repository.lock_read()
        try:
            if revision is None:
                revid = branch.last_revision()
                if revid is None:
                    return
            else:
                (revno, revid) = revision[0].in_history(branch)

            from viz.bzrkapp import BzrkApp
                
            app = BzrkApp()
            app.show(branch, revid, limit)
        finally:
            branch.repository.unlock()
            branch.unlock()
        app.main()


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
               help="jump to specified line number")
    ]
    aliases = ["gblame", "gpraise"]
    
    def run(self, filename, all=False, plain=False, line='1'):
        import pygtk
        pygtk.require("2.0")

        try:
            import gtk
        except RuntimeError, e:
            if str(e) == "could not open display":
                raise NoDisplayError

        try:
            line = int(line)
        except ValueError:
            raise BzrCommandError('Line argument ("%s") is not a number.' % 
                                  line)

        from annotate.gannotate import GAnnotateWindow
        from annotate.config import GAnnotateConfig

        (wt, path) = WorkingTree.open_containing(filename)
        branch = wt.branch

        file_id = wt.path2id(path)

        if file_id is None:
            raise NotVersionedError(filename)

        window = GAnnotateWindow(all, plain)
        window.connect("destroy", lambda w: gtk.main_quit())
        window.set_title(path + " - gannotate")
        config = GAnnotateConfig(window)
        window.show()
        branch.lock_read()
        try:
            window.annotate(branch, file_id)
        finally:
            branch.unlock()
        window.jump_to_line(line)
        
        gtk.main()

register_command(cmd_gannotate)

class cmd_gcommit(Command):
    """GTK+ commit dialog

    Graphical user interface for committing revisions"""
    
    takes_args = []
    takes_options = []

    def run(self, filename=None):
        import pygtk
        pygtk.require("2.0")

        try:
            import gtk
        except RuntimeError, e:
            if str(e) == "could not open display":
                raise NoDisplayError

        from olive.commit import CommitDialog
        from bzrlib.commit import Commit
        from bzrlib.errors import (BzrCommandError, PointlessCommit, ConflictsInTree, 
           StrictCommitFailed)

        (wt, path) = WorkingTree.open_containing(filename)

        dialog = CommitDialog(wt, path)
        dialog.display()
        gtk.main()

register_command(cmd_gcommit)

class NoDisplayError(BzrCommandError):
    """gtk could not find a proper display"""

    def __str__(self):
        return "No DISPLAY. gannotate is disabled."
