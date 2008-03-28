# Copyright (C) 2006 Szilveszter Farkas <szilveszter.farkas@gmail.com>
# Copyright (C) 2007 Jelmer Vernooij <jelmer@samba.org>

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


"""GTK UI
"""

import gtk
import sys

import bzrlib.progress
from bzrlib.ui import UIFactory


class PromptDialog(gtk.Dialog):
    """ Prompt the user for a yes/no answer. """
    def __init__(self, prompt):
        gtk.Dialog.__init__(self)
        
        label = gtk.Label(prompt)
        self.vbox.pack_start(label, padding=10)
        
        self.vbox.show_all()

        self.add_buttons(gtk.STOCK_YES, gtk.RESPONSE_YES, gtk.STOCK_NO, 
                         gtk.RESPONSE_NO)


class GtkProgressBar(gtk.ProgressBar):
    def __init__(self, stack):
        super(GtkProgressBar, self).__init__()
        self.set_fraction(0.0)
        self._stack = stack

    def finished(self):
        self._stack.remove(self)

    def clear(self):
        pass

    def tick(self):
        self.pulse()

    def update(self, msg=None, current=None, total=None):
        if msg is not None:
            self.set_text(msg)
        if None not in (current, total):
            self.set_fraction(1.0 * current / total)
        while gtk.events_pending():
            gtk.main_iteration()


class GtkProgressBarStack(gtk.Window):
    def __init__(self):
        super(GtkProgressBarStack, self).__init__(type=gtk.WINDOW_TOPLEVEL)
        self.set_border_width(0)
        self.set_title("Progress")
        self.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        self.vbox = gtk.VBox()
        self.add(self.vbox)
        self.set_resizable(False)

    def _adapt_size(self):
        self.resize(250, 15 * len(self.vbox.get_children()))

    def get_nested(self):
        nested = GtkProgressBar(self)
        self.vbox.pack_start(nested)
        self._adapt_size()
        self.show_all()
        return nested

    def remove(self, pb):
        self.vbox.remove(pb)


class PasswordDialog(gtk.Dialog):
    """ Prompt the user for a password. """
    def __init__(self, prompt):
        gtk.Dialog.__init__(self)
        
        label = gtk.Label(prompt)
        self.vbox.pack_start(label, padding=10)
        
        self.entry = gtk.Entry()
        self.entry.set_visibility(False)
        self.vbox.pack_end(self.entry, padding=10)
        
        self.vbox.show_all()
        
        self.add_buttons(gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
    
    def _get_passwd(self):
        return self.entry.get_text()

    passwd = property(_get_passwd)


class GtkUIFactory(UIFactory):
    """A UI factory for GTK user interfaces."""

    def __init__(self,
                 stdout=None,
                 stderr=None):
        """Create a GtkUIFactory.

        """
        super(GtkUIFactory, self).__init__()
        self._progress_bar_stack = None

    def get_boolean(self, prompt):
        """GtkDialog with yes/no answers"""
        dialog = PromptDialog(prompt)
        response = dialog.run()
        dialog.destroy()
        return (response == gtk.RESPONSE_YES)
        
    def get_password(self, prompt='', **kwargs):
        """Prompt the user for a password.

        :param prompt: The prompt to present the user
        :param kwargs: Arguments which will be expanded into the prompt.
                       This lets front ends display different things if
                       they so choose.
        :return: The password string, return None if the user 
                 canceled the request.
        """
        dialog = PasswordDialog(prompt % kwargs)
        response = dialog.run()
        passwd = dialog.passwd
        dialog.destroy()
        if response == gtk.RESPONSE_OK:
            return passwd
        else:
            return None

    def nested_progress_bar(self):
        """Return a nested progress bar.
        """
        if self._progress_bar_stack is None:
            self._progress_bar_stack = GtkProgressBarStack()
        return self._progress_bar_stack.get_nested()

    def set_progress_bar_vbox(self, vbox):
        """Change the vbox to put progress bars in.
        """
        self._progress_bar_stack = vbox

    def clear_term(self):
        """Prepare the terminal for output.

        It has no sense when talking about GTK."""
        pass
