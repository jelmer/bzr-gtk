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
    """
    Master class for Avatar providers.
    
    All AvatarProviderXxxx classes should inherite from this one
    and override at least get_base_url.
    """
    def __init__(self, size=80):
        """ Constructor """
        self.size = size
    
    def get_base_url(self):
        """
        Override this methode in your provider class in order to return
        base url of your provider.
        """
        raise NotImplementedError("You must implement the get_base_url method.")


class AvatarDownloaderWorker(threading.Thread):
    """
    Threaded worker to retrieve avatar from a provider.
    
    It create a persitante connection to the provider in order
    to get avatars quickly through the same socket (urllib3).
    """
    
    def __init__(self, provider_method):
        """
        Constructor
        
        provider_method: Provider method that return fields
                         to send with the request.
        """
        threading.Thread.__init__(self)
        self.__stop = threading.Event()
        self.__queue = Queue.Queue()
        
        self.__provider_method = provider_method
        self.__end_thread = False
    
    def stop(self):
        """ Stop this worker """
        self.__end_thread = True
        self.__stop.set()
    
    def set_callback_method(self, method):
        """ Fire the given callback method when treatment is finished """
        self.__callback_method = method
    
    def queue(self, id_field):
        """
        Put in Queue the id_field to treat in the thread.
        This id_field is for example with Gravatar the email address.
        """
        self.__queue.put(id_field)
    
    def run(self):
        """ Worker core code. """
        while not self.__end_thread:
            id_field = self.__queue.get()
            # Call provider method to get fields to pass in the request
            url = self.__provider_method(id_field)
            # Execute the request
            response = urllib2.urlopen(url)
            # Fire the callback method
            if not self.__callback_method is None:
                self.__callback_method(response, id_field)
            self.__queue.task_done()


class AvatarProviderGravatar(AvatarProvider):
    """ Gravatar provider """
    
    def __init__(self):
        """ Constructor """
        super(AvatarProviderGravatar, self).__init__()
    
    def get_base_url(self):
        return "http://www.gravatar.com/avatar.php?"
    
    def gravatar_id_for_email(self, email):
        """ Return a converted email address to a gravatar_id """
        return self.get_base_url() + \
                urllib.urlencode({
                    'gravatar_id':hashlib.md5(email.lower()).hexdigest(),
                    'size':str(self.size)
                })
