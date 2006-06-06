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

from bzrlib.commands import Command, register_command, display_command
from bzrlib.bzrdir import BzrDir
from bzrlib.workingtree import WorkingTree


class cmd_gdiff(Command):
    """Show differences in working tree in a GTK+ Window.
    
    Otherwise, all changes for the tree are listed.
    """
    takes_args = []
    takes_options = []

    @display_command
    def run(self, revision=None, file_list=None):
        tree1 = WorkingTree.open_containing(".")[0]
        branch = tree1.branch
        tree2 = tree1.branch.repository.revision_tree(branch.last_revision())

        from bzrlib.plugins.gtk.viz.diffwin import DiffWindow
        import gtk
        window = DiffWindow()
        window.connect("destroy", lambda w: gtk.main_quit())
        window.set_diff("Working Tree", tree1, tree2)
        window.show()

        gtk.main()

register_command(cmd_gdiff)
