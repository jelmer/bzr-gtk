# Copyright (C) 2005 Dan Loda <danloda@gmail.com>

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

__version__ = "0.6"
__author__ = "Dan Loda <danloda@gmail.com>"

import pygtk
pygtk.require("2.0")
import gtk

from bzrlib.branch import Branch
from bzrlib.commands import Command, register_command
from bzrlib.errors import NotVersionedError
from bzrlib.option import Option


class cmd_gannotate(Command):
    """GTK+ annotate.
    
    Browse changes to FILENAME line by line in a GTK+ window.
    """

    takes_args = ["filename"]
    takes_options = [Option("all", help="show annotations on all lines")]
    aliases = ["gblame", "gpraise"]
    
    def run(self, filename, all=False):
        (branch, path) = Branch.open_containing(filename)

        file_id = branch.working_tree().path2id(path)

        if file_id is None:
            raise NotVersionedError(filename)

        from gannotate import GAnnotateWindow

        window = GAnnotateWindow()
        window.show()
        window.set_title(path + " - gannotate")
        window.annotate(branch, file_id, all)
        window.connect("destroy", lambda w: gtk.main_quit())
        gtk.main()


register_command(cmd_gannotate)

