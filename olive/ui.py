# Copyright (C) 2006 Szilveszter Farkas <szilveszter.farkas@gmail.com>

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
from bzrlib.symbol_versioning import (deprecated_method, 
        zero_eight)
from bzrlib.ui import UIFactory


class PromptDialog(gtk.Dialog):
    """ Prompt the user for a yes/no answer. """
    def __init__(self, prompt):
        gtk.Dialog.__init__(self)
        
        label = gtk.Label(prompt)
        self.vbox.pack_start(label, padding=10)
        
        self.vbox.show_all()

        self.add_buttons(gtk.STOCK_YES, gtk.RESPONSE_YES, gtk.STOCK_NO, gtk.RESPONSE_NO)


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
    """A UI factory for GTK user interefaces."""

    def __init__(self,
                 bar_type=None,
                 stdout=None,
                 stderr=None):
        """Create a GtkUIFactory.

        :param bar_type: The type of progress bar to create. It defaults to 
                         letting the bzrlib.progress.ProgressBar factory auto
                         select.
        """
        super(GtkUIFactory, self).__init__()
        self._bar_type = bar_type
        if stdout is None:
            self.stdout = sys.stdout
        else:
            self.stdout = stdout
        if stderr is None:
            self.stderr = sys.stderr
        else:
            self.stderr = stderr

    def get_boolean(self, prompt):
        """GtkDialog with yes/no answers"""
        dialog = PromptDialog(prompt)
        response = dialog.run()
        dialog.destroy()
        return (response == gtk.RESPONSE_YES)
        
    @deprecated_method(zero_eight)
    def progress_bar(self):
        """See UIFactory.nested_progress_bar()."""
        # this in turn is abstract, and creates either a tty or dots
        # bar depending on what we think of the terminal
        return bzrlib.progress.ProgressBar()

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
        
        The actual bar type returned depends on the progress module which
        may return a tty or dots bar depending on the terminal.
        
        FIXME: It should return a GtkProgressBar actually.
        """
        if self._progress_bar_stack is None:
            self._progress_bar_stack = bzrlib.progress.ProgressBarStack(
                klass=self._bar_type)
        return self._progress_bar_stack.get_nested()

    def clear_term(self):
        """Prepare the terminal for output.

        It has no sense when talking about GTK."""
        pass
