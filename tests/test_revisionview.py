# Copyright (C) 2007, 2008 John Arbash Meinel <john@arbash-meinel.com>
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

"""Test the RevisionView functionality."""

from bzrlib import (
    tests,
    )
try:
    from bzrlib import bencode
except ImportError:
    from bzrlib.util import bencode

from bzrlib.plugins.gtk import revisionview


class TestPendingRevisions(tests.TestCaseWithMemoryTransport):

    def assertBufferText(self, text, buffer):
        """Check the text stored in the buffer."""
        self.assertEqual(text, buffer.get_text(buffer.get_start_iter(),
                                               buffer.get_end_iter()))

    def test_create_view(self):
        builder = self.make_branch_builder('test')
        builder.build_snapshot('A', None,
            [('add', ('', 'root-id', 'directory', None))])
        b = builder.get_branch()

        rv = revisionview.RevisionView(b)
        rev = b.repository.get_revision('A')
        rv.set_revision(rev)
        self.assertEqual(rev.committer, rv.committer.get_text())
        self.assertFalse(rv.author.get_property('visible'))
        self.assertFalse(rv.author_label.get_property('visible'))
        self.assertFalse(rv.file_info_box.get_property('visible'))

    def test_create_view_with_file_info(self):
        tree = self.make_branch_and_memory_tree('test')
        file_info = bencode.bencode([{'file_id':'root-id', 'path':'',
                                      'message':'test-message\n'}])
        tree.lock_write()
        try:
            tree.add([''], ['root-id'])
            tree.commit('test', rev_id='A', revprops={'file-info': file_info})
        finally:
            tree.unlock()
        b = tree.branch

        rv = revisionview.RevisionView(b)
        rev = b.repository.get_revision('A')
        rv.set_revision(rev)

        self.assertEqual(rev.committer, rv.committer.get_text())
        self.assertTrue(rv.file_info_box.get_property('visible'))
        self.assertBufferText('\ntest-message\n', rv.file_info_buffer)

    def test_create_view_with_broken_file_info(self):
        tree = self.make_branch_and_memory_tree('test')
        # This should be 'message13:'
        file_info = 'ld7:file_id7:root-id7:message11:test-message\n4:path0:ee'
        tree.lock_write()
        try:
            tree.add([''], ['root-id'])
            tree.commit('test', rev_id='A', revprops={'file-info': file_info})
        finally:
            tree.unlock()
        b = tree.branch

        rv = revisionview.RevisionView(b)
        rev = b.repository.get_revision('A')
        rv.set_revision(rev)

        self.assertEqual(rev.committer, rv.committer.get_text())
        self.assertFalse(rv.file_info_box.get_property('visible'))
        log = self._get_log(True)
        self.assertContainsRe(log, 'Invalid per-file info for revision:A')
