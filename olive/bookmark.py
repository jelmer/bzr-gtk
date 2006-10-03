# Copyright (C) 2006 by Szilveszter Farkas (Phanatic) <szilveszter.farkas@gmail.com>
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

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

import gtk
import gtk.glade

from olive import gladefile, OlivePreferences
from dialog import error_dialog

class OliveBookmark:
    """ Display the Edit bookmark dialog and perform the needed actions. """
    def __init__(self, selected):
        """ Initialize the Edit bookmark dialog. """
        self.glade = gtk.glade.XML(gladefile, 'window_bookmark', 'olive-gtk')
        
        self.window = self.glade.get_widget('window_bookmark')
        
        self.pref = self.pref = OlivePreferences()
        
        # Dictionary for signal_autoconnect
        dic = { "on_button_bookmark_save_clicked": self.bookmark,
                "on_button_bookmark_cancel_clicked": self.close }
        
        # Connect the signals to the handlers
        self.glade.signal_autoconnect(dic)
        
        # Get some important widgets
        self.entry_location = self.glade.get_widget('entry_bookmark_location')
        self.entry_title = self.glade.get_widget('entry_bookmark_title')
        
        self.selected = selected

    def display(self):
        """ Display the Edit bookmark dialog. """
        path = self.selected
        self.entry_location.set_text(path)
        self.entry_title.set_text(self.pref.get_bookmark_title(path))
        self.window.show_all()
        
    def bookmark(self, widget):
        if self.entry_title.get_text() == '':
            error_dialog(_('No title given'),
                         _('Please specify a title to continue.'))
            return
        
        self.pref.set_bookmark_title(self.entry_location.get_text(),
                                     self.entry_title.get_text())
        self.pref.write()
        
        self.close()
    
    def close(self, widget=None):
        self.window.destroy()
