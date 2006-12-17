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

from olive import OlivePreferences
from dialog import error_dialog
from guifiles import GLADEFILENAME


class OliveBookmark:
    """ Display the Edit bookmark dialog and perform the needed actions. """
    def __init__(self, selected):
        """ Initialize the Edit bookmark dialog. """
        self.glade = gtk.glade.XML(GLADEFILENAME, 'window_bookmark', 'olive-gtk')
        
        self.window = self.glade.get_widget('window_bookmark')
        
        self.pref = OlivePreferences()
        
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

class OliveBookmarkDialog(gtk.Dialog):
    """ This class wraps the old Bookmark window into a gtk.Dialog. """
    
    def __init__(self, selected, parent=None):
        """ Initialize the Bookmark dialog. """
        gtk.Dialog.__init__(self, title="Bookmarks - Olive",
                                  parent=parent,
                                  flags=0,
                                  buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        
        self.pref = OlivePreferences()
        
        # Get arguments
        self.selected = selected
        
        # Create widgets
        self._label_location = gtk.Label(_("Location:"))
        self._label_title = gtk.Label(_("Title:"))
        self._entry_location = gtk.Entry()
        self._entry_title = gtk.Entry()
        self._button_save = gtk.Button(stock=gtk.STOCK_SAVE)
        
        self._button_save.connect('clicked', self._on_save_clicked)
        
        # Set default values
        self._entry_location.set_text(self.selected)
        self._entry_location.set_sensitive(False)
        self._entry_title.set_text(self.pref.get_bookmark_title(self.selected))
        self._entry_title.set_flags(gtk.CAN_FOCUS | gtk.HAS_FOCUS)
        
        # Create a table and put widgets into it
        self._table = gtk.Table(rows=2, columns=2)
        self._table.attach(self._label_location, 0, 1, 0, 1)
        self._table.attach(self._label_title, 0, 1, 1, 2)
        self._table.attach(self._entry_location, 1, 2, 0, 1)
        self._table.attach(self._entry_title, 1, 2, 1, 2)
        
        self._label_location.set_alignment(0, 0.5)
        self._label_title.set_alignment(0, 0.5)
        self._table.set_row_spacings(3)
        self._table.set_col_spacings(3)
        self.vbox.set_spacing(3)
        
        self.vbox.add(self._table)
        
        self.action_area.pack_end(self._button_save)
        
        self.vbox.show_all()
        
    def _on_save_clicked(self, button):
        """ Save button clicked handler. """
        if self._entry_title.get_text() == '':
            error_dialog(_('No title given'),
                         _('Please specify a title to continue.'))
            return
        
        self.pref.set_bookmark_title(self._entry_location.get_text(),
                                     self._entry_title.get_text())
        self.pref.write()
        
        self.response(gtk.RESPONSE_OK)
