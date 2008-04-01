
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

def discover(*key_ids):
    return openpgp.DiscoverKeys(key_ids, 0)

def verify(crypttext):
    return crypto.VerifyText(KEY_TYPE_OPENPGP, 1, crypttext)

def is_valid(signer):
    (v, field) = openpgp.GetKeyField(signer, 'flags')

    return v and field & FLAG_VALID

def is_trusted(signer):
    (v, field) = openpgp.GetKeyField(signer, 'flags')

    return v and field & FLAG_TRUSTED

def get_key_id(signer):
    return signer.split(':')[1]

def get_fingerprint(signer):
    (v, field) = openpgp.GetKeyField(signer, 'fingerprint')

    return v and field

def get_trust(signer):
    (v, field) = openpgp.GetKeyField(signer, 'trust')

    if v is None:
        return 0

    return field
