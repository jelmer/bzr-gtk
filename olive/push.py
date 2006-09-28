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

import sys

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass
    
import gtk
import gtk.gdk
import gtk.glade

import bzrlib.errors as errors

from olive import gladefile

class OlivePush:
    """ Display Push dialog and perform the needed actions. """
    def __init__(self, branch):
        """ Initialize the Push dialog. """
        self.glade = gtk.glade.XML(gladefile, 'window_push')
        
        self.window = self.glade.get_widget('window_push')

        self.branch = branch
        
        # Dictionary for signal_autoconnect
        dic = { "on_button_push_push_clicked": self.push,
                "on_button_push_cancel_clicked": self.close,
                "on_button_push_test_clicked": self.test,
                "on_radiobutton_push_stored_toggled": self.stored_toggled,
                "on_radiobutton_push_specific_toggled": self.specific_toggled, }
        
        # Connect the signals to the handlers
        self.glade.signal_autoconnect(dic)
        
        # Get some useful widgets
        self.radio_stored = self.glade.get_widget('radiobutton_push_stored')
        self.radio_specific = self.glade.get_widget('radiobutton_push_specific')
        self.entry_stored = self.glade.get_widget('entry_push_stored')
        self.entry_location = self.glade.get_widget('entry_push_location')
        self.check_remember = self.glade.get_widget('checkbutton_push_remember')
        self.check_overwrite = self.glade.get_widget('checkbutton_push_overwrite')
        self.check_create = self.glade.get_widget('checkbutton_push_create')
        self.label_test = self.glade.get_widget('label_push_test')
        self.image_test = self.glade.get_widget('image_push_test')
        
        # Set initial state
        self.entry_location.set_sensitive(0)
        self.check_remember.set_sensitive(0)
        self.check_create.set_sensitive(0)
        
        self.entry_stored.set_text(branch.get_push_location())
    
    def display(self):
        """ Display the Push dialog. """
        self.window.show()
        self.width, self.height = self.window.get_size()
    
    def stored_toggled(self, widget):
        if widget.get_active():
            self.entry_stored.set_sensitive(1)
            self.entry_location.set_sensitive(0)
            self.check_remember.set_sensitive(0)
            self.check_create.set_sensitive(0)
        else:
            self.entry_stored.set_sensitive(0)
            self.entry_location.set_sensitive(1)
            self.check_remember.set_sensitive(1)
            self.check_create.set_sensitive(1)
    
    def specific_toggled(self, widget):
        if widget.get_active():
            self.entry_stored.set_sensitive(0)
            self.entry_location.set_sensitive(1)
            self.check_remember.set_sensitive(1)
            self.check_create.set_sensitive(1)
        else:
            self.entry_stored.set_sensitive(1)
            self.entry_location.set_sensitive(0)
            self.check_remember.set_sensitive(0)
            self.check_create.set_sensitive(0)
    
    def push(self, widget):
        revs = 0
        if self.radio_stored.get_active():
            try:
                revs = do_push(self.branch,
                               overwrite=self.check_overwrite.get_active())
            except errors.NotBranchError:
                error_dialog(_('Directory is not a branch'),
                                         _('You can perform this action only in a branch.'))
                return
            except errors.DivergedBranches:
                error_dialog(_('Branches have been diverged'),
                                         _('You cannot push if branches have diverged. Use the\noverwrite option if you want to push anyway.'))
                return
        elif self.radio_specific.get_active():
            location = self.entry_location.get_text()
            if location == '':
                error_dialog(_('No location specified'),
                                         _('Please specify a location or use the default.'))
                return
            
            try:
                revs = do_push(self.branch, location,
                               self.check_remember.get_active(),
                               self.check_overwrite.get_active(),
                               self.check_create.get_active())
            except errors.NotBranchError:
                error_dialog(_('Directory is not a branch'),
                                         _('You can perform this action only in a branch.'))
                return
            except errors.DivergedBranches:
                error_dialog(_('Branches have been diverged'),
                                         _('You cannot push if branches have diverged. Use the\noverwrite option if you want to push anyway.'))
                return
        
        self.close()
        info_dialog(_('Push successful'),
                                _('%d revision(s) pushed.') % revs)
    
    def test(self, widget):
        """ Test if write access possible. """
        import re
        _urlRE = re.compile(r'^(?P<proto>[^:/\\]+)://(?P<path>.*)$')
        
        if self.radio_stored.get_active():
            url = self.entry_stored.get_text()
        elif self.radio_specific.get_active():
            url = self.entry_location.get_text()
        
        m = _urlRE.match(url)
        if m:
            proto = m.groupdict()['proto']
            if (proto == 'sftp') or (proto == 'file') or (proto == 'ftp'):
                # have write acces (most probably)
                self.image_test.set_from_stock(gtk.STOCK_YES, 4)
                self.label_test.set_markup(_('<b>Write access is probably available</b>'))
            else:
                # no write access
                self.image_test.set_from_stock(gtk.STOCK_NO, 4)
                self.label_test.set_markup(_('<b>No write access</b>'))
        else:
            # couldn't determine
            self.image_test.set_from_stock(gtk.STOCK_DIALOG_QUESTION, 4)
            self.label_test.set_markup(_('<b>Could not determine</b>'))
    
    def close(self, widget=None):
        self.window.destroy()

def do_push(branch, location=None, remember=False, overwrite=False,
         create_prefix=False):
    """ Update a mirror of a branch.
    
    :param branch: the source branch
    
    :param location: the location of the branch that you'd like to update
    
    :param remember: if set, the location will be stored
    
    :param overwrite: overwrite target location if it diverged
    
    :param create_prefix: create the path leading up to the branch if it doesn't exist
    
    :return: number of revisions pushed
    """
    from bzrlib.branch import Branch
    from bzrlib.bzrdir import BzrDir
    from bzrlib.transport import get_transport
        
    br_from = Branch.open_containing(branch)[0]
    
    stored_loc = br_from.get_push_location()
    if location is None:
        if stored_loc is None:
            error_dialog(_('Push location is unknown'),
                                     _('Please specify a location manually.'))
            return
        else:
            location = stored_loc

    transport = get_transport(location)
    location_url = transport.base

    if br_from.get_push_location() is None or remember:
        br_from.set_push_location(location_url)

    old_rh = []

    try:
        dir_to = BzrDir.open(location_url)
        br_to = dir_to.open_branch()
    except errors.NotBranchError:
        # create a branch.
        transport = transport.clone('..')
        if not create_prefix:
            try:
                relurl = transport.relpath(location_url)
                transport.mkdir(relurl)
            except errors.NoSuchFile:
                error_dialog(_('Non existing parent directory'),
                                         _("The parent directory (%s)\ndoesn't exist.") % location)
                return
        else:
            current = transport.base
            needed = [(transport, transport.relpath(location_url))]
            while needed:
                try:
                    transport, relpath = needed[-1]
                    transport.mkdir(relpath)
                    needed.pop()
                except errors.NoSuchFile:
                    new_transport = transport.clone('..')
                    needed.append((new_transport,
                                   new_transport.relpath(transport.base)))
                    if new_transport.base == transport.base:
                        error_dialog(_('Path prefix not created'),
                                                 _("The path leading up to the specified location couldn't\nbe created."))
                        return
        dir_to = br_from.bzrdir.clone(location_url,
            revision_id=br_from.last_revision())
        br_to = dir_to.open_branch()
        count = len(br_to.revision_history())
    else:
        old_rh = br_to.revision_history()
        try:
            tree_to = dir_to.open_workingtree()
        except errors.NotLocalUrl:
            # FIXME - what to do here? how should we warn the user?
            #warning('This transport does not update the working '
            #        'tree of: %s' % (br_to.base,))
            count = br_to.pull(br_from, overwrite)
        except errors.NoWorkingTree:
            count = br_to.pull(br_from, overwrite)
        else:
            count = tree_to.pull(br_from, overwrite)

    return count
