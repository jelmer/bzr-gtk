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

import Queue
import urllib
import urllib2
import hashlib
import threading


class AvatarProvider(object):
    """Base class for Avatar providers.

    All AvatarProviderXxxx classes should inherite from this one
    and override at least get_base_url.
    """
    def __init__(self, size=80):
        """ Constructor """
        self.size = size

    def get_base_url(self):
        """Return the base URL of this provider.
        """
        raise NotImplementedError(self.get_base_url)


class AvatarDownloaderWorker(threading.Thread):
    """Threaded worker to retrieve avatar from a provider.

    This creates a persistant connection to the provider in order
    to get avatars quickly through the same socket (urllib2).
    """

    def __init__(self, provider_method):
        """Constructor
        
        :param provider_method: Provider method that returns fields
                 to send with the request.
        """
        threading.Thread.__init__(self)
        self.__stop = threading.Event()
        self.__queue = Queue.Queue()

        self.__provider_method = provider_method

    def stop(self):
        """ Stop this worker """
        self.__stop.set()
        while self.__queue.qsize() > 0:
            self.__queue.get_nowait()
            self.__queue.task_done()
        self.__queue.join()

    @property
    def is_running(self):
        return not self.__stop.is_set()

    def set_callback_method(self, method):
        """ Fire the given callback method when treatment is finished """
        self.__callback_method = method

    def queue(self, id_field):
        """Put in Queue the id_field to treat in the thread.

        This id_field is for example with Gravatar the email address.
        """
        if self.is_running:
            self.__queue.put(id_field)
            if not self.is_alive():
                self.start()

    def run(self):
        """Worker core code. """
        while self.is_running:
            try:
                id_field = self.__queue.get_nowait()
                # Call provider method to get fields to pass in the request
                url = self.__provider_method(id_field)
                # Execute the request
                response = urllib2.urlopen(url)
                # Fire the callback method
                if not self.__callback_method is None:
                    self.__callback_method(response, id_field)
                self.__queue.task_done()
            except Queue.Empty:
                # There is no more work to do.
                pass


class AvatarProviderGravatar(AvatarProvider):
    """Gravatar provider."""

    def get_base_url(self):
        return "http://www.gravatar.com/avatar.php?"

    def gravatar_id_for_email(self, email):
        """Return a gravatar URL for an email address.."""
        return self.get_base_url() + \
                urllib.urlencode({
                    'gravatar_id':hashlib.md5(email.lower()).hexdigest(),
                    'size':str(self.size)
                })
