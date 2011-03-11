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

from bzrlib.plugins.gtk.avatarprovider import AvatarProvider

PROVIDER_URL  = "http://www.gravatar.com/avatar.php?"

class AvatarProviderGravatar(AvatarProvider):
    """ Gravatar provider """
    
    def __init__(self):
        """ Constructor """
        AvatarProvider.__init__(self)
        super
    
    def gravatar_id_for_email(self, email):
        """ Return a converted email address to a gravatar_id """
        return PROVIDER_URL + \
                urllib.urlencode({
                    'gravatar_id':hashlib.md5(email.lower()).hexdigest(),
                    'size':str(self.size)
                })
