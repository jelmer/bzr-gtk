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
from bzrlib.config import parse_username

class Avatar(gtk.Box):
    """ Author or committer avatar """
    
    def __init__(self, username):
        """ Constructor """
        gtk.Box.__init__(self)
        
        self.__username = username
        self.__name, self.__email = parse_username(username)
        self.__image = None
    
    
    # ~~~~~ Properties ~~~~~
    # username
    def get_username(self):
        return self.__username
    def set_username(self, username):
        self.__username = username
    username = property(get_username, set_username)
    
    # Name
    def get_name(self):
        return self.__name
    def set_name(self, name):
        self.__name = name
    name = property(get_name, set_name)
    
    # Email
    def get_email(self):
        return self.__email
    def set_email(self, email):
        self.__email = email
    email = property(get_email, set_email)
    
    # Image
    def get_image(self):
        return self.__image
    def set_image(self, image):
        self.__image = image
    image = property(get_image, set_image)
    
    
    # ~~~~~ Public methods ~~~~~
    def show_spinner(self):
        """
        Replace the current content of the Avatar with a gtk.Spinner
        if an email address has been parsed. If not, show an gtk.Label with
        the translatable 'No email' text.
        """
        if not self.email is "":
            spinner = gtk.Spinner()
            spinner.start()
            self.pack_start(spinner, False)
            spinner.set_tooltip_text(_i18n("Retrieving avatar for %s...") % self.email)
            spinner.set_size_request(20, 20)
            spinner.show()
        else:
            no_email = gtk.Label(_i18n("No email"))
            self.pack_start(no_email)
            self.set_tooltip_text("self.username")
            no_email.show()
    
    def show_image(self):
        """ Replace the current content of the Avatar with the gtk.Image """
        if not self.email is "" and self.image:
            self.remove(self.get_children()[0])
            self.pack_start(self.image)
            self.image.set_tooltip_text(self.username)
            self.image.show()
    
    def is_identical(self, avatar):
        """
        Return True if attributes of the given avatar
        match to current object attributes otherwise return False
        """
        return self.username == avatar.username and \
               self.name == avatar.name and \
               self.email == avatar.email
