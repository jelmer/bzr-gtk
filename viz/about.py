
import gtk
import gobject
import pango

import bzrlib.plugins.gtk

class AboutDialog(gtk.AboutDialog):

    def __init__(self):
        gtk.AboutDialog.__init__(self)
        self.set_name("Bazaar GTK")
        self.set_version(bzrlib.plugins.gtk.__version__)


