# Copyright (C) 2011 by Guillaume Hain (zedtux) <zedtux@zedroot.org>
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

import gtk

from bzrlib.config import parse_username

from bzrlib.plugins.gtk.i18n import _i18n
from bzrlib.plugins.gtk.avatarproviders import (
    AvatarProviderGravatar,
    AvatarDownloaderWorker,
    )


class Avatar(gtk.HBox):
    """ Author or committer avatar """

    def __init__(self, apparent_username):
        """ Constructor """
        gtk.HBox.__init__(self)

        self.apparent_username = apparent_username
        self.username, self.email = parse_username(apparent_username)
        self.image = None

    def __eq__(self, other):
        return (self.apparent_username == other.apparent_username and
                self.username == other.username and
                self.email == other.email)

    def show_spinner(self):
        """
        Replace the current content of the Avatar with a gtk.Spinner
        if an email address has been parsed. If not, show an gtk.Label with
        the translatable 'No email' text.
        """
        if self.email:
            tooltip = _i18n("Retrieving avatar for %s...") % self.email
            if getattr(gtk, "Spinner", False):
                spinner = gtk.Spinner()
                spinner.start()
                self.pack_start(spinner, False)
                spinner.set_tooltip_text(tooltip)
                spinner.set_size_request(20, 20)
                spinner.show()
            else:
                spinner = gtk.Label(tooltip)
                self.pack_start(spinner)
                self.set_tooltip_text(self.apparent_username)
                spinner.show()
        else:
            no_email = gtk.Label(_i18n("No email"))
            self.pack_start(no_email)
            self.set_tooltip_text(self.apparent_username)
            no_email.show()

    def show_image(self):
        """Replace the current content of the Avatar with the gtk.Image """
        if self.email and self.image:
            self.remove(self.get_children()[0])
            self.pack_start(self.image)
            self.image.set_tooltip_text(self.apparent_username)
            self.image.show()


class AvatarBox(gtk.HBox):
    """HBox showing an avatar."""

    def __init__(self, homogeneous=False, spacing=0):
        gtk.HBox.__init__(self, homogeneous, spacing)
        self.__avatars = {}
        self.avatar = None
        self.__displaying = None

    def reset_view(self):
        """Remove current avatars from the gtk box."""
        for child in self.get_children():
            self.remove(child)
        self.__displaying = None

    def have_avatar(self, avatar):
        """Return True if this box has the specified avatar.
        """
        return avatar.email in self.__avatars

    def showing(self, avatar):
        """Return True if the displaying avatar matches the specified one.
        """
        return self.__displaying and self.__displaying == avatar

    def append_avatars_with(self, avatar):
        """
        Append avatars collection with the given one if not already registed
        otherwise render it back.
        When an avatar is added this method True, otherwise, if the avatar
        was in the collection, return False.
        """
        if avatar.email and not avatar.email in self.__avatars:
            self.__avatars[avatar.email] = avatar
            self._new_cell_for_avatar(avatar)
            return True
        else:
            self.and_avatar_email(avatar.email).come_back_to_gui()
        return False

    def and_avatar_email(self, email):
        """
        Select the avatar from avatars collection
        in order to apply future actions
        """
        self.avatar = None
        if email and email in self.__avatars:
            self.avatar = self.__avatars[email]
        else:
            self.avatar = None
        return self

    def update_avatar_image_from_pixbuf_loader(self, loader):
        """Replace the gtk.Spinner with the given loader."""
        if self.avatar:
            self.avatar.image = gtk.Image()
            self.avatar.image.set_from_pixbuf(loader.get_pixbuf())
            self.avatar.show_image()
            self.__displaying = self.avatar

    def come_back_to_gui(self):
        """Render back avatar in the GUI."""
        if self.avatar:
            self.pack_start(self.avatar)
            self.__displaying = self.avatar
        else:
            self._show_no_email()

    def _new_cell_for_avatar(self, avatar):
        """Create a new cell in this box with a gtk.Spinner."""
        avatar.show_spinner()
        self.pack_start(avatar)
        avatar.show()
        self.__displaying = avatar

    def _show_no_email(self):
        """Show a gtk.Label with test 'No email'."""
        no_email = gtk.Label(_i18n("No email"))
        self.pack_start(no_email)
        no_email.show()


class AvatarsBox(gtk.HBox):
    """GTK container for author and committer avatars."""

    def __init__(self):
        gtk.HBox.__init__(self, False, 10)

        self.__committer_box = None
        self.__authors_box = None
        self._init_gui()

        # If more later you want to implement more avatar providers:
        # * Create a new class named AvatarProvider + provider_name that
        #   inherit from the AvatarProvider class.
        # * Implement a method that return url to use in the request.

        # For example, with Gravatar, the method return the complete url
        # with MD5 hash of the email address and put the value in a
        # gravatar_id field.
        # Then create a new worker (manage them in a python dictionary).
        provider = AvatarProviderGravatar()
        self.__worker = AvatarDownloaderWorker(
            provider.gravatar_id_for_email
        )
        # This callback method should be fired by all workers when a request
        # is done.
        self.__worker.set_callback_method(self._update_avatar_from_response)
        self.connect('destroy', self.on_destroy)

    def on_destroy(self, widget):
        self.__worker.stop()
        if self.__worker.is_alive():
            self.__worker.join()

    def add(self, username, role):
        """Add the given username in the role box and add in the worker queue.
        """
        avatar = Avatar(username)
        if (role == "author" and not self._role_box_for("committer").showing(avatar)) or role == "committer":
            if self._role_box_for(role).append_avatars_with(avatar):
                self.__worker.queue(avatar.email)

    def merge(self, usernames, role):
        """Add avatars from a list"""
        for username in usernames:
            self.add(username, role)

    def reset(self):
        """
        Request a reset view for all boxes in order to show only avatars
        of the selected line in the revision view screen.
        """
        for role in ("committer", "author"):
            self._role_box_for(role).reset_view()

    def _init_gui(self):
        """Create boxes where avatars will be displayed."""
        # 2 gtk.HBox: One for the committer and one for authors
        # Committer
        self.__committer_box = AvatarBox()
        self.__committer_box.set_size_request(80, 80)
        self.pack_end(self.__committer_box, False)
        self.__committer_box.show()
        # Authors
        self.__authors_box = AvatarBox()
        self.pack_end(self.__authors_box, False)
        self.__authors_box.set_spacing(10)
        self.__authors_box.show()

    def _update_avatar_from_response(self, response, email):
        """Callback method fired by avatar worker when finished.

        :param response: a urllib2.urlopen() return value.
        :param email: used to identify item from self.__avatars.
        """
        if email:
            # Convert downloaded image from provider to gtk.Image
            loader = gtk.gdk.PixbufLoader()
            loader.write(response.read())
            loader.close()

            for role in ["committer", "author"]:
                self._role_box_for(role).and_avatar_email(email).update_avatar_image_from_pixbuf_loader(loader)

    def _role_box_for(self, role):
        """ Return the gtk.HBox for the given role """
        if role == "committer":
            return self.__committer_box
        else:
            return self.__authors_box
