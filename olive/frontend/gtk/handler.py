# Copyright (C) 2006 by Szilveszter Farkas (Phanatic) <szilveszter.farkas@gmail.com>

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

import sys

try:
 	import pygtk
  	pygtk.require("2.0")
except:
  	pass
try:
	import gtk
  	import gtk.glade
except:
	sys.exit(1)

class OliveHandler:
    """ Signal handler class for Olive. """
    def __init__(self, gladefile):
        self.gladefile = gladefile
    
    def about(self, widget):
        import olive.frontend.gtk

        # Load AboutDialog description
        dglade = gtk.glade.XML(self.gladefile, 'aboutdialog')
        dialog = dglade.get_widget('aboutdialog')

        # Set version
        dialog.set_version(olive.frontend.gtk.__version__)
