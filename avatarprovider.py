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

class AvatarProvider(object):
    """
    Master class for Avatar providers.
    
    All AvatarProviderXxxx classes should inherite from this one
    and override at least get_base_url.
    """
    def __init__(self, size=80):
        """ Constructor """
        self.__size = size
    
    # ~~~~~ Properties ~~~~~
    # Size
    def get_size(self):
        return self.__size
    def set_size(self, size):
        self.__size = size
    size = property(get_size, set_size)
