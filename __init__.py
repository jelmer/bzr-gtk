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

__version__ = "0.7pre"
__author__ = "Dan Loda <danloda@gmail.com>"

from bzrlib.workingtree import WorkingTree
from bzrlib.commands import Command, register_command
from bzrlib.errors import NotVersionedError, BzrCommandError
from bzrlib.option import Option


class cmd_gannotate(Command):
    """GTK+ annotate.
    
    Browse changes to FILENAME line by line in a GTK+ window.
    """

    takes_args = ["filename"]
    takes_options = [
        Option("all", help="show annotations on all lines"),
        Option("plain", help="don't highlight annotation lines"),
        Option("line", type=int, argname="lineno",
               help="jump to specified line number")
    ]
    aliases = ["gblame", "gpraise"]
    
    def run(self, filename, all=False, plain=False, line=1):
        import pygtk
        pygtk.require("2.0")

        try:
            import gtk
        except RuntimeError, e:
            if str(e) == "could not open display":
                raise NoDisplayError

        from gannotate import GAnnotateWindow
        from config import GAnnotateConfig

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
        window.annotate(branch, file_id)
        window.jump_to_line(line)
        
        gtk.main()


register_command(cmd_gannotate)


class NoDisplayError(BzrCommandError):
    """gtk could not find a proper display"""

    def __str__(self):
        return "No DISPLAY. gannotate is disabled."

