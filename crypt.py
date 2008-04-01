
import dbus

BUS_NAME = 'org.gnome.seahorse'
CRYPTO_INTERFACE = 'org.gnome.seahorse.CryptoService'
CRYPTO_PATH = '/org/gnome/seahorse/crypto'

KEY_TYPE_OPENPGP = 'openpgp'
KEY_TYPE_SSH = 'ssh'

bus = dbus.SessionBus()
crypto = dbus.Interface(bus.get_object(BUS_NAME, CRYPTO_PATH), 
                        CRYPTO_INTERFACE)

def verify(crypttext):
    return crypto.VerifyText(KEY_TYPE_OPENPGP, 1, crypttext)
