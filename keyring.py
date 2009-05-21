# Copyright (C) 2009 Jelmer Vernooij <jelmer@samba.org>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import gobject
try:
    import gnomekeyring
except ImportError:
    gnomekeyring = None

from bzrlib.config import (
    CredentialStore,
    )


class GnomeKeyringCredentialStore(CredentialStore):

    def __init__(self):
        CredentialStore.__init__(self)
        # External apps that load bzrlib may also set this, so 
        # don't override:
        if gobject.get_application_name() is None:
            gobject.set_application_name("bzr")

    def decode_password(self, credentials):
        if gnomekeyring is None:
            return None
        try:
            attrs = {}
            if "scheme" in credentials:
                attrs["protocol"] = credentials["scheme"]
            if "host" in credentials:
                attrs["server"] = credentials["host"]
            if "user" in credentials:
                attrs["user"] = credentials["user"]
            if "port" in credentials:
                attrs["port"] = str(credentials["port"])
            items = gnomekeyring.find_items_sync(gnomekeyring.ITEM_GENERIC_SECRET, 
                                                 attrs)
            return items[0].secret
        except (gnomekeyring.NoMatchError, gnomekeyring.DeniedError):
            return None

    def get_credentials(self, scheme, host, port=None, user=None, path=None, 
                        realm=None):
        if gnomekeyring is None:
            return None
        attrs = {
            "protocol": scheme,
            "server": host,
            }
        if realm is not None:
            attrs["realm"] = realm
        if port is not None:
            attrs["port"] = str(port)
        if user is not None:
            attrs["user"] = user
        credentials = { "scheme": scheme, "host": host, "port": port, 
            "realm": realm, "user": user}
        try:
            items = gnomekeyring.find_items_sync(
                gnomekeyring.ITEM_NETWORK_PASSWORD, attrs)
            credentials["user"] = items[0].attributes["user"]
            credentials["password"] = items[0].secret
        except (gnomekeyring.NoMatchError, gnomekeyring.DeniedError):
            return None
