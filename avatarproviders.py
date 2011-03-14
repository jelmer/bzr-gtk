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

import hashlib
import urllib

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
