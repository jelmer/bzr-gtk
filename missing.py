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

from gi.repository import Gtk

from bzrlib.missing import find_unmerged

from bzrlib.plugins.gtk.revisionview import RevisionView


class MissingWindow(Gtk.Dialog):
    """Displays revisions present in one branch but missing in 
    another."""
    def __init__(self, local_branch, remote_branch):
        """ Initialize the Status window. """
        super(MissingWindow, self).__init__(flags=Gtk.DialogFlags.MODAL)
        self.set_title("Missing Revisions")
        self.local_branch = local_branch
        self.remote_branch = remote_branch
        (self.local_extra, self.remote_extra) = find_unmerged(
                local_branch, remote_branch)
        self._create()

    def _create_revisions_frame(self, revisions):
        extra_revs = Gtk.ScrolledWindow()
        vbox = Gtk.VBox()
        for rev in revisions:
            rv = RevisionView()
            rv.set_revision(rev)
            vbox.pack_start(rv, True, True, 0)
        extra_revs.add_with_viewport(vbox)
        extra_revs.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        return extra_revs

    def _create(self):
        self.set_default_size(600, 600)
        paned = Gtk.Paned.new(Gtk.Orientation.VERTICAL)

        frame = Gtk.Frame(label="You have the following extra revisions:")

        extra_revs = self._create_revisions_frame(
                self.local_branch.repository.get_revisions(
                    map(lambda (x,y):y, self.local_extra)))
        frame.add(extra_revs)
        paned.pack1(frame, resize=True, shrink=False)

        missing_revs = self._create_revisions_frame(
                self.remote_branch.repository.get_revisions(
                    map(lambda (x,y):y, self.remote_extra)))

        frame = Gtk.Frame(label="You are missing following revisions:")
        frame.add(missing_revs)

        paned.pack2(frame, resize=False, shrink=True)

        self.get_content_area().pack_start(paned, True, True, 0)
        self.get_content_area().show_all()
