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

import bzrlib.errors as errors

from bzrlib.plugins.gtk.dialog import error_dialog
from guifiles import GLADEFILENAME


def info(location):
    """ Get info about branch, working tree, and repository
    
    :param location: the location of the branch/working tree/repository
    
    :return: the information in dictionary format
    
    The following informations are delivered (if available):
    ret['location']['lightcoroot']: Light checkout root
    ret['location']['sharedrepo']: Shared repository
    ret['location']['repobranch']: Repository branch
    ret['location']['cobranch']: Checkout of branch
    ret['location']['repoco']: Repository checkout
    ret['location']['coroot']: Checkout root
    ret['location']['branchroot']: Branch root
    ret['related']['parentbranch']: Parent branch
    ret['related']['publishbranch']: Publish to branch
    ret['format']['control']: Control format
    ret['format']['workingtree']: Working tree format
    ret['format']['branch']: Branch format
    ret['format']['repository']: Repository format
    ret['locking']['workingtree']: Working tree lock status
    ret['locking']['branch']: Branch lock status
    ret['locking']['repository']: Repository lock status
    ret['missing']['branch']: Missing revisions in branch
    ret['missing']['workingtree']: Missing revisions in working tree
    ret['wtstats']['unchanged']: Unchanged files
    ret['wtstats']['modified']: Modified files
    ret['wtstats']['added']: Added files
    ret['wtstats']['removed']: Removed files
    ret['wtstats']['renamed']: Renamed files
    ret['wtstats']['unknown']: Unknown files
    ret['wtstats']['ignored']: Ingnored files
    ret['wtstats']['subdirs']: Versioned subdirectories
    ret['brstats']['revno']: Revisions in branch
    ret['brstats']['commiters']: Number of commiters
    ret['brstats']['age']: Age of branch in days
    ret['brstats']['firstrev']: Time of first revision
    ret['brstats']['lastrev']: Time of last revision
    ret['repstats']['revisions']: Revisions in repository
    ret['repstats']['size']: Size of repository in bytes
    """
    import bzrlib.bzrdir as bzrdir
    
    import info_helper
    
    ret = {}
    try:
        a_bzrdir = bzrdir.BzrDir.open_containing(location)[0]
    except errors.NotBranchError:
        raise errors.NotBranchError(location)

    try:
        working = a_bzrdir.open_workingtree()
        working.lock_read()
        try:
            branch = working.branch
            repository = branch.repository
            control = working.bzrdir
            
            ret['location'] = info_helper.get_location_info(repository, branch, working)
            ret['related'] = info_helper.get_related_info(branch)
            ret['format'] = info_helper.get_format_info(control, repository, branch, working)
            ret['locking'] = info_helper.get_locking_info(repository, branch, working)
            ret['missing'] = {}
            ret['missing']['branch'] = info_helper.get_missing_revisions_branch(branch)
            ret['missing']['workingtree'] = info_helper.get_missing_revisions_working(working)
            ret['wtstats'] = info_helper.get_working_stats(working)
            ret['brstats'] = info_helper.get_branch_stats(branch)
            ret['repstats'] = info_helper.get_repository_stats(repository)
        finally:
            working.unlock()
            return ret
        return
    except (errors.NoWorkingTree, errors.NotLocalUrl):
        pass

    try:
        branch = a_bzrdir.open_branch()
        repository = branch.repository
        control = a_bzrdir
        branch.lock_read()
        try:
            ret['location'] = info_helper.get_location_info(repository, branch)
            ret['related'] = info_helper.get_related_info(branch)
            ret['format'] = info_helper.get_format_info(control, repository, branch)
            ret['locking'] = info_helper.get_locking_info(repository, branch)
            ret['missing']['branch'] = info_helper.get_missing_revisions_branch(branch)
            ret['brstats'] = info_helper.get_branch_stats(branch)
            ret['repstats'] = info_helper.get_repository_stats(repository)
        finally:
            branch.unlock()
            return ret
        return
    except errors.NotBranchError:
        pass

    try:
        repository = a_bzrdir.open_repository()
        repository.lock_read()
        try:
            ret['location'] = info_helper.get_location_info(repository)
            ret['format'] = info_helper.get_format_info(control, repository)
            ret['locking'] = info_helper.get_locking_info(repository)
            ret['repstats'] = info_helper.get_repository_stats(repository)
        finally:
            repository.unlock()
            return ret
        return
    except errors.NoRepositoryPresent:
        pass


class OliveInfo:
    """ Display Informations window and perform the needed actions. """
    def __init__(self, branch):
        """ Initialize the Informations window. """
        self.glade = gtk.glade.XML(GLADEFILENAME, 'window_info', 'olive-gtk')
        
        # Get the Informations window widget
        self.window = self.glade.get_widget('window_info')
        
        # Check if current location is a branch
        self.notbranch = False
        try:
            self.ret = info(branch.base)
        except errors.NotBranchError:
            self.notbranch = True
            return
        
        # Dictionary for signal_autoconnect
        dic = { "on_button_info_close_clicked": self.close,
                "on_expander_info_location_activate": self.activate,
                "on_expander_info_related_activate": self.activate,
                "on_expander_info_format_activate": self.activate,
                "on_expander_info_locking_activate": self.activate,
                "on_expander_info_missing_activate": self.activate,
                "on_expander_info_wtstats_activate": self.activate,
                "on_expander_info_brstats_activate": self.activate,
                "on_expander_info_repstats_activate": self.activate }
        
        # Connect the signals to the handlers
        self.glade.signal_autoconnect(dic)
        
        # Generate status output
        self._generate_info()

    def _generate_info(self):
        """ Generate 'bzr info' output. """
        # location
        if self.ret.has_key('location'):
            display = False
            e = self.glade.get_widget('expander_info_location')
            if self.ret['location'].has_key('lightcoroot'):
                ll = self.glade.get_widget('label_info_location_lightcoroot_label')
                l = self.glade.get_widget('label_info_location_lightcoroot')
                l.set_text(self.ret['location']['lightcoroot'])
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
            if self.ret['location'].has_key('sharedrepo'):
                ll = self.glade.get_widget('label_info_location_sharedrepo_label')
                l = self.glade.get_widget('label_info_location_sharedrepo')
                l.set_text(self.ret['location']['sharedrepo'])
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
            if self.ret['location'].has_key('repobranch'):
                ll = self.glade.get_widget('label_info_location_repobranch_label')
                l = self.glade.get_widget('label_info_location_repobranch')
                l.set_text(self.ret['location']['repobranch'])
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
            if self.ret['location'].has_key('cobranch'):
                ll = self.glade.get_widget('label_info_location_cobranch_label')
                l = self.glade.get_widget('label_info_location_cobranch')
                l.set_text(self.ret['location']['cobranch'])
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
            if self.ret['location'].has_key('repoco'):
                ll = self.glade.get_widget('label_info_location_repoco_label')
                l = self.glade.get_widget('label_info_location_repoco')
                l.set_text(self.ret['location']['repoco'])
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
            if self.ret['location'].has_key('coroot'):
                ll = self.glade.get_widget('label_info_location_coroot_label')
                l = self.glade.get_widget('label_info_location_coroot')
                l.set_text(self.ret['location']['coroot'])
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
            if self.ret['location'].has_key('branchroot'):
                ll = self.glade.get_widget('label_info_location_branchroot_label')
                l = self.glade.get_widget('label_info_location_branchroot')
                l.set_text(self.ret['location']['branchroot'])
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
        # related
        if self.ret.has_key('related'):
            display = False
            e = self.glade.get_widget('expander_info_related')
            if self.ret['related'].has_key('parentbranch'):
                ll = self.glade.get_widget('label_info_related_parentbranch_label')
                l = self.glade.get_widget('label_info_related_parentbranch')
                l.set_text(self.ret['related']['parentbranch'])
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
            if self.ret['related'].has_key('publishbranch'):
                ll = self.glade.get_widget('label_info_related_publishbranch_label')
                l = self.glade.get_widget('label_info_related_publishbranch')
                l.set_text(self.ret['related']['publishbranch'])
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
        # format
        if self.ret.has_key('format'):
            display = False
            e = self.glade.get_widget('expander_info_format')
            if self.ret['format'].has_key('control'):
                ll = self.glade.get_widget('label_info_format_control_label')
                l = self.glade.get_widget('label_info_format_control')
                l.set_text(self.ret['format']['control'])
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
            if self.ret['format'].has_key('workingtree'):
                ll = self.glade.get_widget('label_info_format_workingtree_label')
                l = self.glade.get_widget('label_info_format_workingtree')
                l.set_text(self.ret['format']['workingtree'])
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
            if self.ret['format'].has_key('branch'):
                ll = self.glade.get_widget('label_info_format_branch_label')
                l = self.glade.get_widget('label_info_format_branch')
                l.set_text(self.ret['format']['branch'])
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
            if self.ret['format'].has_key('repository'):
                ll = self.glade.get_widget('label_info_format_repository_label')
                l = self.glade.get_widget('label_info_format_repository')
                l.set_text(self.ret['format']['repository'])
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
        # locking
        if self.ret.has_key('locking'):
            display = False
            e = self.glade.get_widget('expander_info_locking')
            if self.ret['locking'].has_key('workingtree'):
                ll = self.glade.get_widget('label_info_locking_workingtree_label')
                l = self.glade.get_widget('label_info_locking_workingtree')
                l.set_text(self.ret['locking']['workingtree'])
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
            if self.ret['locking'].has_key('branch'):
                ll = self.glade.get_widget('label_info_locking_branch_label')
                l = self.glade.get_widget('label_info_locking_branch')
                l.set_text(self.ret['locking']['branch'])
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
            if self.ret['locking'].has_key('repository'):
                ll = self.glade.get_widget('label_info_locking_repository_label')
                l = self.glade.get_widget('label_info_locking_repository')
                l.set_text(self.ret['locking']['repository'])
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
        # missing - temporary disabled
        """
        if self.ret.has_key('missing'):
            display = False
            e = self.glade.get_widget('expander_info_missing')
            if self.ret['missing'].has_key('branch'):
                ll = self.glade.get_widget('label_info_missing_branch_label')
                l = self.glade.get_widget('label_info_missing_branch')
                l.set_text(self.ret['missing']['branch'])
                ll.set_markup('<b>' + ll.get_text() + '</b>')
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
            if self.ret['missing'].has_key('workingtree'):
                ll = self.glade.get_widget('label_info_missing_workingtree_label')
                l = self.glade.get_widget('label_info_missing_workingtree')
                l.set_text(self.ret['missing']['branch'])
                ll.set_markup('<b>' + ll.get_text() + '</b>')
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
        """
        # working tree stats
        if self.ret.has_key('wtstats'):
            display = False
            e = self.glade.get_widget('expander_info_wtstats')
            if self.ret['wtstats'].has_key('unchanged'):
                ll = self.glade.get_widget('label_info_wtstats_unchanged_label')
                l = self.glade.get_widget('label_info_wtstats_unchanged')
                l.set_text(str(self.ret['wtstats']['unchanged']))
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
            if self.ret['wtstats'].has_key('modified'):
                ll = self.glade.get_widget('label_info_wtstats_modified_label')
                l = self.glade.get_widget('label_info_wtstats_modified')
                l.set_text(str(self.ret['wtstats']['modified']))
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
            if self.ret['wtstats'].has_key('added'):
                ll = self.glade.get_widget('label_info_wtstats_added_label')
                l = self.glade.get_widget('label_info_wtstats_added')
                l.set_text(str(self.ret['wtstats']['added']))
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
            if self.ret['wtstats'].has_key('removed'):
                ll = self.glade.get_widget('label_info_wtstats_removed_label')
                l = self.glade.get_widget('label_info_wtstats_removed')
                l.set_text(str(self.ret['wtstats']['removed']))
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
            if self.ret['wtstats'].has_key('renamed'):
                ll = self.glade.get_widget('label_info_wtstats_renamed_label')
                l = self.glade.get_widget('label_info_wtstats_renamed')
                l.set_text(str(self.ret['wtstats']['renamed']))
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
            if self.ret['wtstats'].has_key('unknown'):
                ll = self.glade.get_widget('label_info_wtstats_unknown_label')
                l = self.glade.get_widget('label_info_wtstats_unknown')
                l.set_text(str(self.ret['wtstats']['unknown']))
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
            if self.ret['wtstats'].has_key('ignored'):
                ll = self.glade.get_widget('label_info_wtstats_ignored_label')
                l = self.glade.get_widget('label_info_wtstats_ignored')
                l.set_text(str(self.ret['wtstats']['ignored']))
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
            if self.ret['wtstats'].has_key('subdirs'):
                ll = self.glade.get_widget('label_info_wtstats_subdirs_label')
                l = self.glade.get_widget('label_info_wtstats_subdirs')
                l.set_text(str(self.ret['wtstats']['subdirs']))
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
        # branch stats
        if self.ret.has_key('brstats'):
            display = False
            e = self.glade.get_widget('expander_info_brstats')
            if self.ret['brstats'].has_key('revno'):
                ll = self.glade.get_widget('label_info_brstats_revno_label')
                l = self.glade.get_widget('label_info_brstats_revno')
                l.set_text(str(self.ret['brstats']['revno']))
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
            if self.ret['brstats'].has_key('commiters'):
                ll = self.glade.get_widget('label_info_brstats_commiters_label')
                l = self.glade.get_widget('label_info_brstats_commiters')
                l.set_text(str(self.ret['brstats']['commiters']))
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
            if self.ret['brstats'].has_key('age'):
                ll = self.glade.get_widget('label_info_brstats_age_label')
                l = self.glade.get_widget('label_info_brstats_age')
                l.set_text('%d days' % self.ret['brstats']['age'])
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
            if self.ret['brstats'].has_key('firstrev'):
                ll = self.glade.get_widget('label_info_brstats_firstrev_label')
                l = self.glade.get_widget('label_info_brstats_firstrev')
                l.set_text(self.ret['brstats']['firstrev'])
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
            if self.ret['brstats'].has_key('lastrev'):
                ll = self.glade.get_widget('label_info_brstats_lastrev_label')
                l = self.glade.get_widget('label_info_brstats_lastrev')
                l.set_text(self.ret['brstats']['lastrev'])
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
        # repository stats
        if self.ret.has_key('repstats'):
            display = False
            e = self.glade.get_widget('expander_info_repstats')
            if self.ret['repstats'].has_key('revisions'):
                ll = self.glade.get_widget('label_info_repstats_revisions_label')
                l = self.glade.get_widget('label_info_repstats_revisions')
                l.set_text(str(self.ret['repstats']['revisions']))
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
            if self.ret['repstats'].has_key('size'):
                ll = self.glade.get_widget('label_info_repstats_size_label')
                l = self.glade.get_widget('label_info_repstats_size')
                l.set_text('%d KiB' % (self.ret['repstats']['size'] / 1024))
                ll.show()
                l.show()
                if not display:
                    e.set_expanded(True)
                    e.show()
                    display = True
    
    def activate(self, expander):
        """ Redraw the window. """
        self.window.resize(50, 50)
        self.window.queue_resize()
    
    def display(self):
        """ Display the Informations window. """
        if self.notbranch:
            error_dialog(_('Directory is not a branch'),
                         _('You can perform this action only in a branch.'))
            self.close()
        else:
            self.window.show()

    def close(self, widget=None):
        self.window.destroy()
