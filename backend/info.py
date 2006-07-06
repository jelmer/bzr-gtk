# Copyright (C) 2006 by Szilveszter Farkas (Phanatic)
# Some parts of the code are:
# Copyright (C) 2005, 2006 by Canonical Ltd

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

import bzrlib
import bzrlib.errors as errors

from bzrlib.branch import Branch

from errors import (NotBranchError)

def diff(revision=None, file_list=None, diff_options=None, prefix=None):
    """ Save the diff into a temporary file.
    
    :param revision: a list of revisions (one or two elements)
    
    :param file_list: list of files you want to diff
    
    :param diff_options: external diff options
    
    :param prefix: 0 - p0, 1 - p1, or specify prefixes in the form of old/:new/
    
    :return: path to the temporary file which contains the diff output
    """
    from tempfile import mkstemp
    
    from bzrlib.builtins import internal_tree_files
    from bzrlib.diff import show_diff_trees
    from bzrlib.workingtree import WorkingTree
    
    from info_helper import diff_helper

    if (prefix is None) or (prefix == '0'):
        # diff -p0 format
        old_label = ''
        new_label = ''
    elif prefix == '1':
        old_label = 'old/'
        new_label = 'new/'
    else:
        if not ':' in prefix:
            raise errors.BzrError("--diff-prefix expects two values separated by a colon")
        old_label, new_label = prefix.split(":")
    
    try:
        tree1, file_list = internal_tree_files(file_list)
        tree2 = None
        b = None
        b2 = None
    except errors.FileInWrongBranch:
        if len(file_list) != 2:
            raise errors.BzrCommandError("Files are in different branches")

        tree1, file1 = WorkingTree.open_containing(file_list[0])
        tree2, file2 = WorkingTree.open_containing(file_list[1])
    
        if file1 != "" or file2 != "":
            # FIXME diff those two files. rbc 20051123
            raise errors.BzrCommandError("Files are in different branches")
    
        file_list = None
    
    tmpfile = mkstemp(prefix='olive_')
    tmpfp = open(tmpfile[1], 'w')
    
    if revision is not None:
        if tree2 is not None:
            raise errors.BzrCommandError("Can't specify -r with two branches")
    
        if (len(revision) == 1) or (revision[1].spec is None):
            ret = diff_helper(tree1, file_list, diff_options,
                                   revision[0], 
                                   old_label=old_label, new_label=new_label,
                                   output=tmpfp)
        elif len(revision) == 2:
            ret = diff_helper(tree1, file_list, diff_options,
                                   revision[0], revision[1],
                                   old_label=old_label, new_label=new_label,
                                   output=tmpfp)
        else:
            raise errors.BzrCommandError('bzr diff --revision takes exactly one or two revision identifiers')
    else:
        if tree2 is not None:
            ret = show_diff_trees(tree1, tree2, tmpfp, 
                                   specific_files=file_list,
                                   external_diff_options=diff_options,
                                   old_label=old_label, new_label=new_label)
        else:
            ret = diff_helper(tree1, file_list, diff_options,
                                   old_label=old_label, new_label=new_label,
                                   output=tmpfp)
    
    tmpfp.close()
    
    if ret == 0:
        return False
    else:
        return tmpfile[1]

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
    ret['mrevbranch']['missing']: Missing revisions in branch
    ret['mrevworking']['missing']: Missing revisions in working tree
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
    a_bzrdir = bzrdir.BzrDir.open_containing(location)[0]
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
            ret['mrevbranch'] = info_helper.get_missing_revisions_branch(branch)
            ret['mrevworking'] = info_helper.get_missing_revisions_working(working)
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
        branch.lock_read()
        try:
            ret['location'] = info_helper.get_location_info(repository, branch)
            ret['related'] = info_helper.get_related_info(branch)
            ret['format'] = info_helper.get_format_info(control, repository, branch)
            ret['locking'] = info_helper.get_locking_info(repository, branch)
            ret['mrevbranch'] = info_helper.get_missing_revisions_branch(branch)
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

def nick(branch, nickname=None):
    """ Get or set nickname.
    
    :param branch: path to the branch
    
    :param nickname: if specified, the nickname will be set
    
    :return: nickname
    """
    try:
        branch = Branch.open_containing(branch)[0]
    except errors.NotBranchError:
        raise NotBranchError
    
    if nickname is not None:
        branch.nick = nickname

    return branch.nick    

def revno(branch):
    """ Get current revision number for specified branch
    
    :param branch: path to the branch
    
    :return: revision number
    """
    try:
        revno = Branch.open_containing(branch)[0].revno()
    except errors.NotBranchError:
        raise NotBranchError
    else:
        return revno

def version():
    """ Get version information from bzr
    
    :return: bzrlib version
    """
    return bzrlib.__version__

def whoami(branch=None, email=False):
    """ Get user's data (name and email address)
    
    :param branch: if specified, the user's data will be looked up in the branch's config
    
    :param email: if True, only the email address will be returned
    
    :return: user info (only email address if email is True)
    """
    from bzrlib.workingtree import WorkingTree
    
    if branch is not None:
        try:
            b = WorkingTree.open_containing(u'.')[0].branch
            config = bzrlib.config.BranchConfig(b)
        except NotBranchError:
            config = bzrlib.config.GlobalConfig()
    else:
        config = bzrlib.config.GlobalConfig()
        
    if email:
        return config.user_email()
    else:
        return config.username()
