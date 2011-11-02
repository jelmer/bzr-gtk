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
    from bzrlib import bencode
except ImportError:
    from bzrlib.util import bencode

from bzrlib import osutils

class SavedCommitMessagesManager(object):
    """Save global and per-file commit messages.

    Saves global commit message and utf-8 file_id->message dictionary
    of per-file commit messages on disk. Re-reads them later for re-using.
    """

    def __init__(self, tree=None, branch=None):
        """If branch is None, builds empty messages, otherwise reads them
        from branch's disk storage. 'tree' argument is for the future."""
        if branch is None:
            self.global_message = u''
            self.file_messages = {}
        else:
            config = branch.get_config()
            self.global_message = config.get_user_option(
                'gtk_global_commit_message')
            if self.global_message is None:
                self.global_message = u''
            file_messages = config.get_user_option('gtk_file_commit_messages')
            if file_messages: # unicode and B-encoded:
                self.file_messages = bencode.bdecode(
                    file_messages.encode('UTF-8'))
            else:
                self.file_messages = {}

    def get(self):
        return self.global_message, self.file_messages

    def is_not_empty(self):
        return bool(self.global_message or self.file_messages)

    def insert(self, global_message, file_info):
        """Formats per-file commit messages (list of dictionaries, one per file)
        into one utf-8 file_id->message dictionary and merges this with
        previously existing dictionary. Merges global commit message too."""
        file_messages = {}
        for fi in file_info:
            file_message = fi['message']
            if file_message:
                file_messages[fi['file_id']] = file_message # utf-8 strings
        for k,v in file_messages.iteritems():
            try:
                self.file_messages[k] = v + '\n******\n' + self.file_messages[k]
            except KeyError:
                self.file_messages[k] = v
        if self.global_message:
            self.global_message = global_message + '\n******\n' \
                + self.global_message
        else:
            self.global_message = global_message

    def save(self, tree, branch):
        # We store in branch's config, which can be a problem if two gcommit
        # are done in two checkouts of one single branch (comments overwrite
        # each other). Ideally should be in working tree. But uncommit does
        # not always have a working tree, though it always has a branch.
        # 'tree' argument is for the future
        config = branch.get_config()
        # should it be named "gtk_" or some more neutral name ("gui_" ?) to
        # be compatible with qbzr in the future?
        config.set_user_option('gtk_global_commit_message', self.global_message)
        # bencode() does not know unicode objects but set_user_option()
        # requires one:
        config.set_user_option(
            'gtk_file_commit_messages',
            bencode.bencode(self.file_messages).decode('UTF-8'))


def save_commit_messages(local, master, old_revno, old_revid,
                         new_revno, new_revid):
    b = local
    if b is None:
        b = master
    mgr = SavedCommitMessagesManager(None, b)
    graph = b.repository.get_graph()
    revid_iterator = graph.iter_lefthand_ancestry(old_revid)
    cur_revno = old_revno
    new_revision_id = old_revid
    graph = b.repository.get_graph()
    for rev_id in revid_iterator:
        if cur_revno == new_revno:
            break
        cur_revno -= 1
        rev = b.repository.get_revision(rev_id)
        file_info = rev.properties.get('file-info', None)
        if file_info is None:
            file_info = {}
        else:
            file_info = bencode.bdecode(file_info.encode('UTF-8'))
        global_message = osutils.safe_unicode(rev.message)
        # Concatenate comment of the uncommitted revision
        mgr.insert(global_message, file_info)

        parents = graph.get_parent_map([rev_id]).get(rev_id, None)
        if not parents:
            continue
    mgr.save(None, b)
