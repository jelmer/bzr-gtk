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

from bzrlib.plugins.gtk.avatar import Avatar
from bzrlib.plugins.gtk.avatarbox import AvatarBox
from bzrlib.plugins.gtk.avatarprovidergravatar import AvatarProviderGravatar
from bzrlib.plugins.gtk.avatardownloaderworker import AvatarDownloaderWorker

class AvatarsBox(gtk.HBox):
    """ GTK container for authors and committers avatars """
    
    def __init__(self):
        """ Constructor """
        gtk.HBox.__init__(self, False, 10)
        
        self.__committer_box = None
        self.__authors_box = None
        self._init_gui()
        
        # If more later you want to implement more avatar providers, to it like this:
        # Create a new class named AvatarProvider + provider_name that inherit from
        # the AvatarProvider class.
        # Implement a method that return url to use in the request.
        # For example, with Gravatar, the method return the complete url
        # with MD5 hash of the email address and put the value in a gravatar_id field.
        # Then create a new worker (manage them in a python dictionnary).
        provider = AvatarProviderGravatar()
        self.__worker = AvatarDownloaderWorker(
            provider.gravatar_id_for_email
        )
        # This callback method should be fired bt all workers when a request is done.
        self.__worker.set_callback_method(self._update_avatar_from_response)
        self.__worker.start()
    
    
    # ~~~~~ Public methods ~~~~~
    def add(self, username, role):
        """
        Add the given username in the right role box and add in the worker queue.
        Here again: If you want to implement more providers, you should add the
        avatar request in all workers queue.
        """
        avatar = Avatar(username)
        if role is "author" and not self._role_box_for("committer").showing(avatar) or role is "committer":
            if self._role_box_for(role).append_avatars_with(avatar):
                self.__worker.queue(avatar.email)
    
    def merge(self, usernames, role):
        """ Add avatars from a list """
        [self.add(username, role) for username in usernames]
    
    def reset(self):
        """
        Request a reset view for all boxes in order to show only avatars
        of the selected line in the revision view screen.
        """
        [self._role_box_for(role).reset_view() for role in ["committer", "author"]]
    
    
    # ~~~~~ Private methods ~~~~~
    def _init_gui(self):
        """ Create boxes where avatars will be displayed """
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
        """
        Callback method fired by avatar worker when finished.
        
        response is a urllib2.urlopen() return value.
        email is used to identify item from self.__avatars.
        """
        if not email is "":
            # Convert downloaded image from provider to gtk.Image
            loader = gtk.gdk.PixbufLoader()
            loader.write(response.read())
            loader.close()
            
            for role in ["committer", "author"]:
                self._role_box_for(role).and_avatar_email(email).update_avatar_image_from_pixbuf_loader(loader)
    
    def _role_box_for(self, role):
        """ Return the gtk.HBox for the given role """
        return self.__committer_box if role is "committer" else self.__authors_box
