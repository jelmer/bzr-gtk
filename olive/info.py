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

import bzrlib.errors as errors

from bzrlib.plugins.gtk import _i18n, icon_path
from bzrlib.plugins.gtk.dialog import error_dialog


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
    except errors.NoRepositoryPresent:
        pass


class InfoDialog(object):
    """ Display Informations window and perform the needed actions. """
    
    def __init__(self, branch):
        """ Initialize the Informations window. """
        # Check if current location is a branch
        self.notbranch = False
        try:
            self.ret = info(branch.base)
        except errors.NotBranchError:
            self.notbranch = True
            return
        
        # Create the window
        self.window = gtk.Dialog(title="Branch Information",
                                  parent = None,
                                  flags=0,
                                  buttons=None)
        self.window.set_icon_list(gtk.gdk.pixbuf_new_from_file(icon_path("oliveicon2.png")),
                                  gtk.gdk.pixbuf_new_from_file(icon_path("olive-gtk.png")))
        self.window.vbox.set_spacing(3)
        self.window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_NORMAL)
        
        infokeylist = ( ('location', _i18n("Location"), (
                            ('lightcoroot', _i18n("Light checkout root")),
                            ('sharedrepo', _i18n("Shared repository")),
                            ('repobranch', _i18n("Repository branch")),
                            ('cobranch', _i18n("Checkout of branch")),
                            ('repoco', _i18n("Repository checkout")),
                            ('coroot', _i18n("Checkout root")),
                            ('branchroot', _i18n("Branch root")),
                            )),
                        ('related', _i18n("Related branches"), (
                            ('parentbranch', _i18n("Parent branch")),
                            ('publishbranch', _i18n("Publish to branch")),
                            )),
                        ('format', _i18n("Format"), (
                            ('control', _i18n("Control format")),
                            ('workingtree', _i18n("Working tree format")),
                            ('branch', _i18n("Branch format")),
                            ('repository', _i18n("Repository format")),
                            )),
                        ('locking', _i18n("Lock status"), (
                            ('workingtree', _i18n("Working tree lock status")),
                            ('branch', _i18n("Branch lock status")),
                            ('repository', _i18n("Repository lock status")),
                            )),
                        #('missing', _i18n("Missing revisions"), (
                        #    ('branch', _i18n("Missing revisions in branch")),
                        #    ('workingtree', _i18n("Missing revisions in working tree")),
                        #    )), # Missing is 'temporary' disabled
                        ('wtstats', _i18n("In the working tree"), (
                            ('unchanged', _i18n("Unchanged files")),
                            ('modified', _i18n("Modified files")),
                            ('added', _i18n("Added files")),
                            ('removed', _i18n("Removed files")),
                            ('renamed', _i18n("Renamed files")),
                            ('unknown', _i18n("Unknown files")),
                            ('ignored', _i18n("Ignored files")),
                            ('subdirs', _i18n("Versioned subdirectories")),
                            )),
                        ('brstats', _i18n("Branch history"), (
                            ('revno', _i18n("Revisions in branch")),
                            ('commiters', _i18n("Number of commiters")),
                            ('age', _i18n("Age of branch in days")),
                            ('firstrev', _i18n("Time of first revision")),
                            ('lastrev', _i18n("Time of last revision")),
                            )),
                        ('repstats', _i18n("Revision store"), (
                            ('revisions', _i18n("Revisions in repository")),
                            ('size', _i18n("Size of repository in bytes")),
                            )),
                        )
               
        # Generate status output
        self._generate_info(infokeylist)
        
        button_close = gtk.Button(stock=gtk.STOCK_CLOSE)        
        button_close.connect('clicked', self.close)
        self.window.action_area.pack_end(button_close)
        self.window.set_focus(button_close)
    
    def _generate_info(self, infokeylist):
        """ Generate 'bzr info' output. """
        for key, keystring, subkeylist in infokeylist:
            if self.ret.has_key(key):
                tablelength = 0
                for subkey, subkeystring in subkeylist:
                    if self.ret[key].has_key(subkey):
                        tablelength += 1
                if tablelength == 0:
                    pass
                else:
                    exec "exp_%s = gtk.Expander('<b>%s</b>')"%(key, keystring)
                    eval("exp_%s.set_use_markup(True)"%key)
                    eval("exp_%s.connect('activate', self.activate)"%key)
                    
                    exec "alignment_%s = gtk.Alignment()"%key
                    eval("alignment_%s.set_padding(0, 0, 24, 0)"%key)
                    eval("exp_%s.add(alignment_%s)"%(key, key))
                    
                    exec "table_%s = gtk.Table(tablelength, 2)"%key
                    eval("table_%s.set_col_spacings(12)"%key)
                    eval("alignment_%s.add(table_%s)"%(key, key))
                    
                    tablepos = 0
                    for subkey, subkeystring in subkeylist:
                        if self.ret[key].has_key(subkey):
                            exec "%s_%s_label = gtk.Label('%s:')"%(key,subkey, subkeystring)
                            eval("table_%s.attach(%s_%s_label, 0, 1, %i, %i, gtk.FILL)"%(key, key, subkey, tablepos, tablepos + 1))
                            eval("%s_%s_label.set_alignment(0, 0.5)"%(key, subkey))
                            
                            exec "%s_%s = gtk.Label('%s')"%(key, subkey, str(self.ret[key][subkey]))
                            eval("table_%s.attach(%s_%s, 1, 2, %i, %i, gtk.FILL)"%(key, key, subkey, tablepos, tablepos + 1))
                            eval("%s_%s.set_alignment(0, 0.5)"%(key, subkey))
                            tablepos += 1
                    eval("exp_%s.set_expanded(True)"%key)
                    eval("self.window.vbox.pack_start(exp_%s, False, True, 0)"%key)
    
    def activate(self, expander):
        """ Redraw the window. """
        self.window.resize(50, 50)
        self.window.queue_resize()
    
    def display(self):
        """ Display the Informations window. """
        if self.notbranch:
            error_dialog(_i18n('Directory is not a branch'),
                         _i18n('You can perform this action only in a branch.'))
            self.close()
        else:
            self.window.show_all()
    
    def close(self, widget=None):
        self.window.destroy()
