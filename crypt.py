
import dbus

BUS_NAME = 'org.gnome.seahorse'

CRYPTO_INTERFACE = 'org.gnome.seahorse.CryptoService'
CRYPTO_PATH = '/org/gnome/seahorse/crypto'

OPENPGP_INTERFACE = 'org.gnome.seahorse.Keys'
OPENPGP_PATH = '/org/gnome/seahorse/keys/openpgp'

KEY_TYPE_OPENPGP = 'openpgp'
KEY_TYPE_SSH = 'ssh'

bus = dbus.SessionBus()
crypto = dbus.Interface(bus.get_object(BUS_NAME, CRYPTO_PATH), 
                        CRYPTO_INTERFACE)
openpgp = dbus.Interface(bus.get_object(BUS_NAME, OPENPGP_PATH),
                      OPENPGP_INTERFACE)

def verify(crypttext):
    return crypto.VerifyText(KEY_TYPE_OPENPGP, 1, crypttext)

def is_valid(key):
    (v, field) = openpgp.GetKeyField(key, 'flags')

    return v and field & 0x0001

def get_fingerprint(key):
    (v, field) = openpgp.GetKeyField(key, 'fingerprint')

    if v:
        return field
    else:
        return None
