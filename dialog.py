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

from gi.repository import Gtk


def _message_dialog(type, primary, secondary, parent=None, buttons=Gtk.ButtonsType.OK):
    """ Display a given type of MessageDialog with the given message.

    :param type: message dialog type

    :param message: the message you want to display.
    """
    dialog = Gtk.MessageDialog(parent=parent, flags=Gtk.DialogFlags.MODAL,
                               type=type, buttons=buttons)
    dialog.set_markup('<big><b>' + primary + '</b></big>')
    dialog.format_secondary_text(secondary)
    response = dialog.run()
    dialog.destroy()
    return response

def error_dialog(primary, secondary, parent=None):
    """ Display an error dialog with the given message. """
    return _message_dialog(Gtk.MessageType.ERROR, primary, secondary, parent)

def info_dialog(primary, secondary, parent=None):
    """ Display an info dialog with the given message. """
    return _message_dialog(Gtk.MessageType.INFO, primary, secondary, parent)

def warning_dialog(primary, secondary, parent=None):
    """ Display a warning dialog with the given message. """
    return _message_dialog(Gtk.MessageType.WARNING, primary, secondary, parent)

def question_dialog(primary, secondary, parent=None):
    """ Display a dialog with the given question. """
    return _message_dialog(Gtk.MessageType.QUESTION, primary, secondary, parent, Gtk.ButtonsType.YES_NO)
