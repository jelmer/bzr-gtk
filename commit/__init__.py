# Copyright (C) 2006 Jelmer Vernooij <jelmer@samba.org>

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

__version__ = "0.8"
__author__ = "Jelmer Vernooij <jelmer@samba.org>"

from bzrlib.workingtree import WorkingTree
from bzrlib.commands import Command, register_command
from bzrlib.commit import Commit
from bzrlib.errors import (BzrCommandError, PointlessCommit, ConflictsInTree, 
           StrictCommitFailed)

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

        from gcommit import GCommitDialog

        (wt, path) = WorkingTree.open_containing(filename)
        branch = wt.branch

        file_id = wt.path2id(path)

        if file_id is None:
            raise NotVersionedError(filename)

        dialog = GCommitDialog(wt)
        dialog.set_title(path + " - Commit")
        if dialog.run() != gtk.RESPONSE_CANCEL:
            Commit().commit(working_tree=wt,message=dialog.message,
                specific_files=dialog.specific_files)

register_command(cmd_gcommit)
