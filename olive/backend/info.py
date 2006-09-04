# Copyright (C) 2006 by Szilveszter Farkas (Phanatic) <szilveszter.farkas@gmail.com>
# Some parts of the code are:
# Copyright (C) 2005, 2006 by Canonical Ltd
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

import bzrlib
import bzrlib.errors as errors

from bzrlib.branch import Branch
from bzrlib.workingtree import WorkingTree

from bzrlib.errors import (NotBranchError, PermissionDenied, BzrError)

class DifferentBranchesError(BzrError):
    """ Occurs if the specified files are in different branches
    
    May occur in:
        info.diff()
    """


class PrefixFormatError(BzrError):
    """ Occurs if the prefix is badly formatted
    
    May occur in:
        info.diff()
    """


class RevisionValueError(BzrError):
    """ Invalid revision value provided
    
    May occur in:
        info.log()
    """


def diff(revision=None, file_list=None, diff_options=None, prefix=None):
    """ Save the diff into a temporary file.
    
    :param revision: a list of revision numbers (one or two elements)
    
    :param file_list: list of files you want to diff
    
    :param diff_options: external diff options
    
    :param prefix: 0 - p0, 1 - p1, or specify prefixes in the form of old/:new/
    
    :return: path to the temporary file which contains the diff output (the frontend has to remove it!)
    """
    from tempfile import mkstemp
    
    from bzrlib.builtins import internal_tree_files
    from bzrlib.diff import show_diff_trees
    from bzrlib.revisionspec import RevisionSpec_int
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
            raise PrefixFormatError
        old_label, new_label = prefix.split(":")
    
    try:
        tree1, file_list = internal_tree_files(file_list)
        tree2 = None
        b = None
        b2 = None
    except errors.FileInWrongBranch:
        if len(file_list) != 2:
            raise DifferentBranchesError

        tree1, file1 = WorkingTree.open_containing(file_list[0])
        tree2, file2 = WorkingTree.open_containing(file_list[1])
    
        if file1 != "" or file2 != "":
            raise DifferentBranchesError
    
        file_list = None
    
    tmpfile = mkstemp(prefix='olive_')
    tmpfp = open(tmpfile[1], 'w')
    
    if revision is not None:
        if tree2 is not None:
            raise RevisionValueError
    
        if len(revision) >= 1:
            revision[0] = RevisionSpec_int(revision[0])
        if len(revision) == 2:
            revision[1] = RevisionSpec_int(revision[1])
        
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
            raise RevisionValueError
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

def get_push_location(location):
    """ Get the stored push location of a branch.
    
    :param location: the path to the branch
    
    :return: the stored location
    """
    from bzrlib.branch import Branch
    
    try:
        branch = Branch.open_containing(location)[0]
    except errors.NotBranchError:
        raise NotBranchError(location)
    except:
        raise
    
    return branch.get_push_location()

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
        raise NotBranchError(location)

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

def is_branch(location):
    """ Check if the location is a branch.
    
    :param location: the location you want to check
    
    :return: True or False respectively
    """
    try:
        branch = Branch.open_containing(location)[0]
    except errors.NotBranchError:
        return False
    except errors.PermissionDenied:
        raise PermissionDenied(location)
    else:
        return True
        

def is_checkout(location):
    """ Check if the location is a checkout.
    
    :param location: the location you want to check
    
    :return: True or False respectively
    """
    try:
        branch = Branch.open_containing(location)[0]
    except errors.NotBranchError:
        raise NotBranchError
    
    try:
        working = WorkingTree.open_containing(location)[0]
    except:
        raise
    
    working_path = working.bzrdir.root_transport.base
    branch_path = branch.bzrdir.root_transport.base
    
    if working_path != branch_path:
        # lightweight checkout
        return True
    elif branch.get_bound_location():
        # checkout
        return True
    else:
        return False

def log(location, timezone='original', verbose=False, show_ids=False,
        forward=False, revision=None, log_format=None, message=None,
        long=False, short=False, line=False):
    """ Print log into a temporary file.
    
    :param location: location of local/remote branch or file
    
    :param timzone: requested timezone
    
    :param verbose: verbose output
    
    :param show_ids:
    
    :param forward: if True, start from the earliest entry
    
    :param revision: revision range as a list ([from, to])
    
    :param log_format: line, short, long
    
    :param message: show revisions whose message matches this regexp
    
    :param long: long log format
    
    :param short: short log format
    
    :param line: line log format
    
    :return: full path to the temporary file containing the log (the frontend has to remove it!)
    """
    from tempfile import mkstemp
    
    from bzrlib import bzrdir    
    from bzrlib.builtins import get_log_format
    from bzrlib.log import log_formatter, show_log
    from bzrlib.revisionspec import RevisionSpec_int
    
    assert message is None or isinstance(message, basestring), \
        "invalid message argument %r" % message
    direction = (forward and 'forward') or 'reverse'
        
    # log everything
    file_id = None
    
    # find the file id to log:
    dir, fp = bzrdir.BzrDir.open_containing(location)
    b = dir.open_branch()
    if fp != '':
        try:
            # might be a tree:
            inv = dir.open_workingtree().inventory
        except (errors.NotBranchError, errors.NotLocalUrl):
            # either no tree, or is remote.
            inv = b.basis_tree().inventory
        file_id = inv.path2id(fp)

    if revision is not None:
        if len(revision) >= 1:
            revision[0] = RevisionSpec_int(revision[0])
        if len(revision) == 2:
            revision[1] = RevisionSpec_int(revision[1])
    
    if revision is None:
        rev1 = None
        rev2 = None
    elif len(revision) == 1:
        rev1 = rev2 = revision[0].in_history(b).revno
    elif len(revision) == 2:
        if revision[0].spec is None:
            # missing begin-range means first revision
            rev1 = 1
        else:
            rev1 = revision[0].in_history(b).revno

        if revision[1].spec is None:
            # missing end-range means last known revision
            rev2 = b.revno()
        else:
            rev2 = revision[1].in_history(b).revno
    else:
        raise RevisionValueError

    # By this point, the revision numbers are converted to the +ve
    # form if they were supplied in the -ve form, so we can do
    # this comparison in relative safety
    if rev1 > rev2:
        (rev2, rev1) = (rev1, rev2)

    if (log_format == None):
        default = b.get_config().log_format()
        log_format = get_log_format(long=long, short=short, line=line, 
                                    default=default)
    
    tmpfile = mkstemp(prefix='olive_')
    tmpfp = open(tmpfile[1], 'w')
    
    lf = log_formatter(log_format,
                       show_ids=show_ids,
                       to_file=tmpfp,
                       show_timezone=timezone)

    show_log(b,
             lf,
             file_id,
             verbose=verbose,
             direction=direction,
             start_revision=rev1,
             end_revision=rev2,
             search=message)
    
    tmpfp.close()
    return tmpfile[1]

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
