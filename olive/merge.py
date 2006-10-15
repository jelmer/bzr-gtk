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

import os

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

import gtk
import gtk.glade

import bzrlib.errors as errors

from __init__ import gladefile
from dialog import error_dialog

class MergeDialog:
    """ Display the Merge dialog and perform the needed actions. """
    def __init__(self, wt, wtpath):
        """ Initialize the Merge dialog. """
        self.glade = gtk.glade.XML(gladefile, 'window_merge', 'olive-gtk')
        
        self.window = self.glade.get_widget('window_merge')
        
        # Dictionary for signal_autoconnect
        dic = { "on_button_merge_merge_clicked": self.merge,
                "on_button_merge_cancel_clicked": self.close,
                "on_button_merge_open_clicked": self.open }
        
        # Connect the signals to the handlers
        self.glade.signal_autoconnect(dic)

        self.wt = wt
        self.wtpath = wtpath

    def display(self):
        """ Display the Add file(s) dialog. """
        self.window.show_all()

    def merge(self, widget):
        print "DEBUG: Merge button pressed."
    
    def open(self, widget):
        print "DEBUG: Open branch button pressed."
    
    def close(self, widget=None):
        self.window.destroy()
