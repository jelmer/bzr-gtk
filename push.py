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

from olive import delimiter
from errors import show_bzr_error

from bzrlib.config import LocationConfig
import bzrlib.errors as errors

from dialog import error_dialog, info_dialog, question_dialog


class PushDialog(gtk.Dialog):
    """ New implementation of the Push dialog. """
    def __init__(self, branch, parent=None):
        """ Initialize the Push dialog. """
        gtk.Dialog.__init__(self, title="Push - Olive",
                                  parent=parent,
                                  flags=0,
                                  buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        
        # Get arguments
        self.branch = branch
        
        # Create the widgets
        self._label_location = gtk.Label(_("Location:"))
        self._label_test = gtk.Label(_("(click the Test button to check write access)"))
        self._check_remember = gtk.CheckButton(_("_Remember as default location"),
                                               use_underline=True)
        self._check_prefix = gtk.CheckButton(_("Create the path _leading up to the location"),
                                             use_underline=True)
        self._check_overwrite = gtk.CheckButton(_("_Overwrite target if diverged"),
                                                use_underline=True)
        self._combo = gtk.ComboBoxEntry()
        self._button_test = gtk.Button(_("_Test"), use_underline=True)
        self._button_push = gtk.Button(_("_Push"), use_underline=True)
        self._hbox_location = gtk.HBox()
        self._hbox_test = gtk.HBox()
        self._image_test = gtk.Image()
        
        # Set callbacks
        self._button_test.connect('clicked', self._on_test_clicked)
        self._button_push.connect('clicked', self._on_push_clicked)
        
        # Set properties
        self._image_test.set_from_stock(gtk.STOCK_DIALOG_INFO, gtk.ICON_SIZE_BUTTON)
        self._label_location.set_alignment(0, 0.5)
        self._label_test.set_alignment(0, 0.5)
        self._hbox_location.set_spacing(3)
        self._hbox_test.set_spacing(3)
        self.vbox.set_spacing(3)
        
        # Pack widgets
        self._hbox_location.pack_start(self._label_location, False, False)
        self._hbox_location.pack_start(self._combo, True, True)
        self._hbox_test.pack_start(self._image_test, False, False)
        self._hbox_test.pack_start(self._label_test, True, True)
        self.vbox.pack_start(self._hbox_location)
        self.vbox.pack_start(self._check_remember)
        self.vbox.pack_start(self._check_prefix)
        self.vbox.pack_start(self._check_overwrite)
        self.vbox.pack_start(self._hbox_test)
        self.action_area.pack_start(self._button_test)
        self.action_area.pack_end(self._button_push)
        
        # Show the dialog
        self.vbox.show_all()
        
        # Build location history
        self._build_history()
        
    def _build_history(self):
        """ Build up the location history. """
        config = LocationConfig(self.branch.base)
        history = config.get_user_option('gpush_history')
        if history is not None:
            self._combo_model = gtk.ListStore(str)
            for item in history.split(delimiter):
                self._combo_model.append([ item ])
            self._combo.set_model(self._combo_model)
            self._combo.set_text_column(0)
        
        location = self.branch.get_push_location()
        if location:
            self._combo.get_child().set_text(location)
    
    def _add_to_history(self, location):
        """ Add specified location to the history (if not yet added). """
        config = LocationConfig(self.branch.base)
        history = config.get_user_option('gpush_history')
        if history is None:
            config.set_user_option('gpush_history', location)
        else:
            h = history.split(delimiter)
            if location not in h:
                h.append(location)
            config.set_user_option('gpush_history', delimiter.join(h))
    
    def _on_test_clicked(self, widget):
        """ Test button clicked handler. """
        import re
        _urlRE = re.compile(r'^(?P<proto>[^:/\\]+)://(?P<path>.*)$')
        
        url = self._combo.get_child().get_text()
        
        m = _urlRE.match(url)
        if m:
            proto = m.groupdict()['proto']
            if (proto == 'sftp') or (proto == 'file') or (proto == 'ftp'):
                # have write acces (most probably)
                self._image_test.set_from_stock(gtk.STOCK_YES, 4)
                self._label_test.set_markup(_('<b>Write access is probably available</b>'))
            else:
                # no write access
                self._image_test.set_from_stock(gtk.STOCK_NO, 4)
                self._label_test.set_markup(_('<b>No write access</b>'))
        else:
            # couldn't determine
            self._image_test.set_from_stock(gtk.STOCK_DIALOG_QUESTION, 4)
            self._label_test.set_markup(_('<b>Could not determine</b>'))
    
    @show_bzr_error
    def _on_push_clicked(self, widget):
        """ Push button clicked handler. """
        location = self._combo.get_child().get_text()
        revs = 0
        try:
            revs = do_push(self.branch,
                           location=location,
                           overwrite=self._check_overwrite.get_active(),
                           remember=self._check_remember.get_active(),
                           create_prefix=self._check_prefix.get_active())
        except errors.DivergedBranches:
            response = question_dialog(_('Branches have been diverged'),
                                       _('You cannot push if branches have diverged.\nOverwrite?'))
            if response == gtk.RESPONSE_OK:
                revs = do_push(self.branch, overwrite=True)
            return
        
        self._add_to_history(location)
        info_dialog(_('Push successful'),
                    _("%d revision(s) pushed.") % revs)
        
        self.response(gtk.RESPONSE_OK)

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
    from bzrlib.bzrdir import BzrDir
    from bzrlib.transport import get_transport
        
    br_from = branch
    
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
