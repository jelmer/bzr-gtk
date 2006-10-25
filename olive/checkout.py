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

from bzrlib.branch import Branch
import bzrlib.bzrdir as bzrdir
import bzrlib.errors as errors
import bzrlib.osutils

from dialog import error_dialog
from gladefile import GLADEFILENAME


class OliveCheckout:
    """ Display checkout dialog and perform the needed operations. """
    def __init__(self, path=None):
        """ Initialize the Checkout dialog. """
        self.glade = gtk.glade.XML(GLADEFILENAME, 'window_checkout', 'olive-gtk')
        
        self.window = self.glade.get_widget('window_checkout')
        
        # Dictionary for signal_autoconnect
        dic = { "on_button_checkout_checkout_clicked": self.checkout,
                "on_button_checkout_cancel_clicked": self.close }
        
        # Connect the signals to the handlers
        self.glade.signal_autoconnect(dic)
        
        # Save FileChooser state
        self.filechooser = self.glade.get_widget('filechooserbutton_checkout')
        if path is not None:
            self.filechooser.set_filename(path)

    def display(self):
        """ Display the Checkout dialog. """
        self.window.show_all()
    
    def checkout(self, widget):
        entry_location = self.glade.get_widget('entry_checkout_location')
        location = entry_location.get_text()
        if location is '':
            error_dialog(_('Missing branch location'),
                         _('You must specify a branch location.'))
            return
        
        destination = self.filechooser.get_filename()
        
        spinbutton_revno = self.glade.get_widget('spinbutton_checkout_revno')
        revno = spinbutton_revno.get_value_as_int()
        
        checkbutton_lightweight = self.glade.get_widget('checkbutton_checkout_lightweight')
        lightweight = checkbutton_lightweight.get_active()
        
        try:
            source = Branch.open(location)
            rev_id = source.get_rev_id(revno)
            
            # if the source and destination are the same, 
            # and there is no working tree,
            # then reconstitute a branch
            if (bzrlib.osutils.abspath(destination) ==
                bzrlib.osutils.abspath(location)):
                try:
                    source.bzrdir.open_workingtree()
                except errors.NoWorkingTree:
                    source.bzrdir.create_workingtree()
                    return

            destination = destination + '/' + os.path.basename(location.rstrip("/\\"))
            
            os.mkdir(destination)

            old_format = bzrlib.bzrdir.BzrDirFormat.get_default_format()
            bzrdir.BzrDirFormat.set_default_format(bzrdir.BzrDirMetaFormat1())

            try:
                if lightweight:
                    checkout = bzrdir.BzrDirMetaFormat1().initialize(destination)
                    bzrlib.branch.BranchReferenceFormat().initialize(checkout, source)
                else:
                    checkout_branch = bzrlib.bzrdir.BzrDir.create_branch_convenience(
                        destination, force_new_tree=False)
                    checkout = checkout_branch.bzrdir
                    checkout_branch.bind(source)
                    if rev_id is not None:
                        rh = checkout_branch.revno_history()
                        checkout_branch.set_revno_history(rh[:rh.index(rev_id) + 1])

                checkout.create_workingtree(rev_id)
            finally:
                bzrlib.bzrdir.BzrDirFormat.set_default_format(old_format)
        except errors.NotBranchError, errmsg:
            error_dialog(_('Location is not a branch'),
                         _('The specified location has to be a branch.'))
            return
        except errors.TargetAlreadyExists, errmsg:
            error_dialog(_('Target already exists'),
                         _('Target directory (%s)\nalready exists. Please select another target.') % errmsg)
            return
        except errors.NonExistingParent, errmsg:
            error_dialog(_('Non existing parent directory'),
                         _("The parent directory (%s)\ndoesn't exist.") % errmsg)
            return
        
        self.close()
        self.comm.refresh_right()

    def close(self, widget=None):
        self.window.destroy()