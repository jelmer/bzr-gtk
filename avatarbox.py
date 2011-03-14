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

from bzrlib.plugins.gtk import _i18n

class AvatarBox(gtk.HBox):
    """ Improved gtk.HBox """
    
    def __init__(self, homogeneous=False, spacing=0):
        """ Constructor """
        gtk.HBox.__init__(self, homogeneous, spacing)
        self.__avatars = {}
        self.avatar = None
        self.__displaying = None
    
    
    # ~~~~~ Public methods ~~~~~
    def reset_view(self):
        """ Remove current avatars from the gtk box """
        for child in self.get_children():
            self.remove(child)
        self.__displaying = None
    
    def have_avatar(self, avatar):
        """
        Return True if this box has registered given avatar,
        otherwise return False
        """
        return avatar.email in self.__avatars
    
    def showing(self, avatar):
        """
        Return True if the displaying avatar is the same
        as the given one otherwise return False
        """
        return self.__displaying and self.__displaying == avatar
    
    def append_avatars_with(self, avatar):
        """
        Append avatars collection with the given one if not already registed
        otherwise render it back.
        When an avatar is added this method True, otherwise, if the avatar
        was in the collection, return False.
        """
        if not avatar.email is "" and not avatar.email in self.__avatars:
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
        if not email is "" and email in self.__avatars:
            self.avatar = self.__avatars[email]
        else:
            self.avatar = None
        return self
    
    def update_avatar_image_from_pixbuf_loader(self, loader):
        """ Replace the gtk.Spinner with the given loader """
        if self.avatar:
            self.avatar.image = gtk.Image()
            self.avatar.image.set_from_pixbuf(loader.get_pixbuf())
            self.avatar.show_image()
            self.__displaying = self.avatar
    
    def come_back_to_gui(self):
        """ Render back avatar in the GUI """
        if self.avatar:
            self.pack_start(self.avatar)
            self.__displaying = self.avatar
        else:
            self._show_no_email()
    
    
    # ~~~~~ Private methods ~~~~~~
    def _new_cell_for_avatar(self, avatar):
        """ Create a new cell in this box with a gtk.Spinner """
        avatar.show_spinner()
        self.pack_start(avatar)
        avatar.show()
        self.__displaying = avatar
    
    def _show_no_email(self):
        """ Show a gtk.Label with test 'No email' """
        no_email = gtk.Label(_i18n("No email"))
        self.pack_start(no_email)
        no_email.show()
