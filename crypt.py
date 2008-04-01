
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

TRUST_NEVER = -1
TRUST_UNKNOWN = 0
TRUST_MARGINAL = 1
TRUST_FULL = 5
TRUST_ULTIMATE = 10

def verify(crypttext):
    return crypto.VerifyText(KEY_TYPE_OPENPGP, 1, crypttext)

def is_valid(signer):
    (v, field) = openpgp.GetKeyField(signer, 'flags')

    return v and field & 0x0001

def get_fingerprint(signer):
    (v, field) = openpgp.GetKeyField(signer, 'fingerprint')

    if v:
        return field
    else:
        return None

def get_trust(signer):
    (v, field) = openpgp.GetKeyField(signer, 'trust')

    if v is None:
        return 0

    return field
