# Copyright (C) 2007 Jelmer Vernooij <jelmer@samba.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

import gtk

from bzrlib.config import GlobalConfig
from bzrlib.missing import find_unmerged

from logview import LogView

class MissingWindow(gtk.Dialog):
    """Displays revisions present in one branch but missing in 
    another."""
    def __init__(self, local_branch, remote_branch):
        """ Initialize the Status window. """
        super(MissingWindow, self).__init__(flags=gtk.DIALOG_MODAL)
        self.set_title("Missing Revisions")
        self.local_branch = local_branch
        self.remote_branch = remote_branch
        (self.local_extra, self.remote_extra) = find_unmerged(
                local_branch, remote_branch)
        self._create()

    def _create_revisions_frame(self, revisions):
        extra_revs = gtk.ScrolledWindow()
        vbox = gtk.VBox()
        for rev in revisions:
            vbox.pack_start(LogView(rev), True, True)
        extra_revs.add_with_viewport(vbox)
        extra_revs.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        return extra_revs

    def _create(self):
        self.set_default_size(600, 600)

        frame = gtk.Frame("You have the following extra revisions:")

        extra_revs = self._create_revisions_frame(
                self.local_branch.repository.get_revisions(
                    map(lambda (x,y):y, self.local_extra)))
        frame.add(extra_revs)
        self.vbox.pack_start(frame, True, True)

        missing_revs = self._create_revisions_frame(
                self.remote_branch.repository.get_revisions(
                    map(lambda (x,y):y, self.remote_extra)))

        frame = gtk.Frame("You are missing following revisions:")
        frame.add(missing_revs)
        self.vbox.pack_start(frame, True, True)
        self.vbox.show_all()

    def display(self):
        self.window.show_all()

    def close(self, widget=None):
        self.window.destroy()
