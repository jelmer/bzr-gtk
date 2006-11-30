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


def about():
    """ Display the AboutDialog. """
    import olive
    from guifiles import GLADEFILENAME

    # Load AboutDialog description
    dglade = gtk.glade.XML(GLADEFILENAME, 'aboutdialog')
    dialog = dglade.get_widget('aboutdialog')

    # Set version
    dialog.set_version(olive.__version__)

    dialog.run()
    # Destroy the dialog
    dialog.destroy()

def _message_dialog(type, primary, secondary):
    """ Display a given type of MessageDialog with the given message.
    
    :param type: error | warning | info
    
    :param message: the message you want to display.
    """
    if type == 'error':
        dialog = gtk.MessageDialog(flags=gtk.DIALOG_MODAL,
                                   type=gtk.MESSAGE_ERROR,
                                   buttons=gtk.BUTTONS_OK)
        dialog.set_markup('<big><b>' + primary + '</b></big>')
    elif type == 'warning':
        dialog = gtk.MessageDialog(flags=gtk.DIALOG_MODAL,
                                   type=gtk.MESSAGE_WARNING,
                                   buttons=gtk.BUTTONS_OK)
        dialog.set_markup('<big><b>' + primary + '</b></big>')
    elif type == 'info':
        dialog = gtk.MessageDialog(flags=gtk.DIALOG_MODAL,
                                   type=gtk.MESSAGE_INFO,
                                   buttons=gtk.BUTTONS_OK)
        dialog.set_markup('<big><b>' + primary + '</b></big>')
    elif type == 'question':
        dialog = gtk.MessageDialog(flags=gtk.DIALOG_MODAL,
                                   type=gtk.MESSAGE_QUESTION,
                                   buttons=gtk.BUTTONS_YES_NO)
        dialog.set_markup('<big><b>' + primary + '</b></big>')
    else:
        return

    dialog.format_secondary_markup(secondary)

    response = dialog.run()
    dialog.destroy()

    return response

def error_dialog(primary, secondary):
    """ Display an error dialog with the given message. """
    return _message_dialog('error', primary, secondary)

def info_dialog(primary, secondary):
    """ Display an info dialog with the given message. """
    return _message_dialog('info', primary, secondary)

def warning_dialog(primary, secondary):
    """ Display a warning dialog with the given message. """
    return _message_dialog('warning', primary, secondary)

def question_dialog(primary, secondary):
    """ Display a dialog with the given question. """
    return _message_dialog('question', primary, secondary)
