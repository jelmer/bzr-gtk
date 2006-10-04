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
import bzrlib.errors as errors

from __init__ import gladefile
from dialog import error_dialog, info_dialog

class BranchDialog:
    """ Display branch dialog and perform the needed operations. """
    def __init__(self, path=None):
        """ Initialize the Branch dialog. """
        self.glade = gtk.glade.XML(gladefile, 'window_branch', 'olive-gtk')

        self.window = self.glade.get_widget('window_branch')
        
        # Dictionary for signal_autoconnect
        dic = { "on_button_branch_branch_clicked": self.branch,
                "on_button_branch_cancel_clicked": self.close }
        
        # Connect the signals to the handlers
        self.glade.signal_autoconnect(dic)
        
        # Save FileChooser state
        self.filechooser = self.glade.get_widget('filechooserbutton_branch')
        if path is not None:
            self.filechooser.set_filename(path)

    def display(self):
        """ Display the Branch dialog. """
        self.window.show_all()
    
    def branch(self, widget):
        entry_location = self.glade.get_widget('entry_branch_location')
        location = entry_location.get_text()
        if location is '':
            error_dialog(_('Missing branch location'),
                         _('You must specify a branch location.'))
            return
        
        destination = self.filechooser.get_filename()
        
        spinbutton_revno = self.glade.get_widget('spinbutton_branch_revno')
        revno = spinbutton_revno.get_value_as_int()
        
        try:
            from bzrlib.transport import get_transport

            br_from = Branch.open(location)
            br_from.lock_read()
            
            revision_id = br_from.get_rev_id(revno)

            try:
                destination = destination + '/' + os.path.basename(location.rstrip("/\\"))
                to_transport = get_transport(destination)
                to_transport.mkdir('.')

                try:
                    dir = br_from.bzrdir.sprout(to_transport.base, revision_id)
                    branch = dir.open_branch()
                    revs = branch.revno()
                except errors.NoSuchRevision:
                    to_transport.delete_tree('.')
                    raise

            finally:
                br_from.unlock()
                
            self.close()
            info_dialog(_('Branching successful'),
                        _('%d revision(s) branched.') % revs)
        except errors.NonExistingSource, errmsg:
            error_dialog(_('Non existing source'),
                         _("The location (%s)\ndoesn't exist.") % errmsg)
            return
        except errors.TargetAlreadyExists, errmsg:
            error_dialog(_('Target already exists'),
                         _('Target directory (%s)\nalready exists. Please select another target.') % errmsg)
            return
        except errors.NonExistingParent, errmsg:
            error_dialog(_('Non existing parent directory'),
                         _("The parent directory (%s)\ndoesn't exist.") % errmsg)
            return
        except errors.NonExistingRevision:
            error_dialog(_('Non existing revision'),
                         _("The revision you specified doesn't exist."))
            return
        except errors.NotBranchError, errmsg:
            error_dialog(_('Location is not a branch'),
                         _('The specified location has to be a branch.'))
            return
        
    def close(self, widget=None):
        self.window.destroy()
