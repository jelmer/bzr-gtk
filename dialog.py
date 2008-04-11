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


def _message_dialog(type, primary, secondary, buttons=gtk.BUTTONS_OK):
    """ Display a given type of MessageDialog with the given message.
    
    :param type: message dialog type
    
    :param message: the message you want to display.
    """
    dialog = gtk.MessageDialog(flags=gtk.DIALOG_MODAL, type=type,
                               buttons=buttons)
    dialog.set_markup('<big><b>' + primary + '</b></big>')
    dialog.format_secondary_markup(secondary)
    response = dialog.run()
    dialog.destroy()
    return response

def error_dialog(primary, secondary):
    """ Display an error dialog with the given message. """
    return _message_dialog(gtk.MESSAGE_ERROR, primary, secondary)

def info_dialog(primary, secondary):
    """ Display an info dialog with the given message. """
    return _message_dialog(gtk.MESSAGE_INFO, primary, secondary)

def warning_dialog(primary, secondary):
    """ Display a warning dialog with the given message. """
    return _message_dialog(gtk.MESSAGE_WARNING, primary, secondary)

def question_dialog(primary, secondary):
    """ Display a dialog with the given question. """
    return _message_dialog(gtk.MESSAGE_QUESTION, primary, secondary, gtk.BUTTONS_YES_NO)

def _chooserevison_dialog(history):
    """ Display a dialog with list of revisions. """
    dialog = gtk.Dialog()
    hbox = gtk.HBox()
    dialog.vbox.pack_start(hbox)
    dialog.vbox.set_spacing(2)
    
    img = gtk.Image()
    img.set_from_stock(gtk.STOCK_DIALOG_QUESTION,gtk.ICON_SIZE_DIALOG)
    hbox.pack_start(img)
    
    hbox.set_spacing(10)
    vbox = gtk.VBox()
    vbox.set_spacing(10)
    hbox.pack_start(vbox)
    
    lbl = gtk.Label("<b>Select a revision</b>")
    lbl.set_use_markup(True)
    lbl.set_alignment(0,0)
    vbox.pack_start(lbl)
    
    revisioncombo = gtk.ComboBox()
    model = gtk.ListStore(str,str)
    revisioncombo.set_model(model)
    
    for item in history:
        numver = ""
        for ver in item[3]: # item 3 contains a list with revision number and subnumbers
            numver = numver + str(ver) + "." # here we make a 'readable' version number (IE: 30.1.5)
        numver = numver[0:-1]
        model.append((item[1],numver))
    
    cell = gtk.CellRendererText()
    revisioncombo.pack_start(cell, True)
    revisioncombo.add_attribute(cell, 'text', 1)
    
    vbox.pack_start(revisioncombo)
    
    dialog.vbox.show_all()
    dialog.add_buttons(gtk.STOCK_CANCEL,gtk.RESPONSE_REJECT,gtk.STOCK_OK,gtk.RESPONSE_OK)
    returncode = dialog.run()
    active_iter = revisioncombo.get_active_iter()
    if active_iter != None:
        val = model.get_value(active_iter,0) # get selected revision id from model
    else:
        val = ''
        
    dialog.destroy()
    
    return (returncode, val) #return dialog return code and selected revision ID
