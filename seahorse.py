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

__copyright__ = 'Copyright (C) 2008 Daniel Schierbeck'
__author__ = 'Daniel Schierbeck <daniel.schierbeck@gmail.com>'

import dbus

BUS_NAME = 'org.gnome.seahorse'

CRYPTO_INTERFACE = 'org.gnome.seahorse.CryptoService'
CRYPTO_PATH = '/org/gnome/seahorse/crypto'

OPENPGP_INTERFACE = 'org.gnome.seahorse.Keys'
OPENPGP_PATH = '/org/gnome/seahorse/keys/openpgp'

KEY_TYPE_OPENPGP = 'openpgp'
KEY_TYPE_SSH = 'ssh'

try:
    dbus.validate_bus_name(BUS_NAME)
except ValueError:
    raise ImportError

bus = dbus.SessionBus()

crypto = dbus.Interface(bus.get_object(BUS_NAME, CRYPTO_PATH), 
                        CRYPTO_INTERFACE)
openpgp = dbus.Interface(bus.get_object(BUS_NAME, OPENPGP_PATH),
                         OPENPGP_INTERFACE)

FLAG_VALID = 0x0001
FLAG_CAN_ENCRYPT = 0x0002
FLAG_CAN_SIGN = 0x0004
FLAG_EXPIRED = 0x0100
FLAG_REVOKED = 0x0200
FLAG_DISABLED = 0x0400
FLAG_TRUSTED = 0x1000

TRUST_NEVER = -1
TRUST_UNKNOWN = 0
TRUST_MARGINAL = 1
TRUST_FULL = 5
TRUST_ULTIMATE = 10

LOCATION_MISSING = 10
LOCATION_SEARCHING = 20
LOCATION_REMOTE = 50
LOCATION_LOCAL = 100

keyset = dict()

def verify(crypttext):
    (cleartext, key) = crypto.VerifyText(KEY_TYPE_OPENPGP, 1, crypttext)

    if key != "":
        if key not in keyset:
            keyset[key] = Key(key)

        return keyset[key]

class Key:

    def __init__(self, key):
        self.key = key
        self.fingerprint = None
        self.trust = None
        self.flags = None
        self.display_name = None
        self.location = None
        
        (keys, unmatched) = openpgp.MatchKeys([self.get_id()], 0x00000010)
        self.available = (key in keys)

    def get_field(self, field, default=None):
        (valid, value) = openpgp.GetKeyField(self.key, field)

        if valid:
            return value
        else:
            return default
    
    def get_flags(self):
        if self.flags is None:
            self.flags = self.get_field('flags', 0)

        return self.flags

    def get_display_name(self):
        if self.display_name is None:
            self.display_name = self.get_field('display-name')

        return self.display_name

    def get_id(self):
        return self.key.split(':')[1][8:]

    def get_fingerprint(self):
        if self.fingerprint is None:
            self.fingerprint = self.get_field('fingerprint')

        return self.fingerprint

    def get_trust(self):
        if self.trust is None:
            self.trust = self.get_field('trust', TRUST_UNKNOWN)

        return self.trust

    def get_location(self):
        if self.location is None:
            self.location = self.get_field('location', LOCATION_MISSING)

        return self.location

    def is_available(self):
        return self.available

    def is_trusted(self):
        return self.get_flags() & FLAG_TRUSTED
