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

"""Test the Commit functionality."""

import os

from gi.repository import Gtk

from bzrlib import (
    branch,
    tests,
    uncommit,
    )
try:
    from bzrlib.tests.features import UnicodeFilenameFeature
except ImportError: # bzr < 2.5
    from bzrlib.tests import UnicodeFilenameFeature
from bzrlib import bencode

from bzrlib.plugins.gtk import (
    commit,
    commitmsgs,
    )


# TODO: All we need is basic ancestry code to test this, we shouldn't need a
# TestCaseWithTransport, just a TestCaseWithMemoryTransport or somesuch.

class TestPendingRevisions(tests.TestCaseWithTransport):

    def test_pending_revisions_none(self):
        tree = self.make_branch_and_tree('.')
        tree.commit('one')

        self.addCleanup(tree.lock_read().unlock)
        self.assertIs(None, commit.pending_revisions(tree))

    def test_pending_revisions_simple(self):
        tree = self.make_branch_and_tree('tree')
        rev_id1 = tree.commit('one')
        tree2 = tree.bzrdir.sprout('tree2').open_workingtree()
        rev_id2 = tree2.commit('two')
        tree.merge_from_branch(tree2.branch)
        self.assertEqual([rev_id1, rev_id2], tree.get_parent_ids())

        self.addCleanup(tree.lock_read().unlock)
        pending_revisions = commit.pending_revisions(tree)
        # One primary merge
        self.assertEqual(1, len(pending_revisions))
        # Revision == rev_id2
        self.assertEqual(rev_id2, pending_revisions[0][0].revision_id)
        # No children of this revision.
        self.assertEqual([], pending_revisions[0][1])

    def test_pending_revisions_with_children(self):
        tree = self.make_branch_and_tree('tree')
        rev_id1 = tree.commit('one')
        tree2 = tree.bzrdir.sprout('tree2').open_workingtree()
        rev_id2 = tree2.commit('two')
        rev_id3 = tree2.commit('three')
        rev_id4 = tree2.commit('four')
        tree.merge_from_branch(tree2.branch)
        self.assertEqual([rev_id1, rev_id4], tree.get_parent_ids())

        self.addCleanup(tree.lock_read().unlock)
        pending_revisions = commit.pending_revisions(tree)
        # One primary merge
        self.assertEqual(1, len(pending_revisions))
        # Revision == rev_id2
        self.assertEqual(rev_id4, pending_revisions[0][0].revision_id)
        # Two children for this revision
        self.assertEqual(2, len(pending_revisions[0][1]))
        self.assertEqual(rev_id3, pending_revisions[0][1][0].revision_id)
        self.assertEqual(rev_id2, pending_revisions[0][1][1].revision_id)

    def test_pending_revisions_multi_merge(self):
        tree = self.make_branch_and_tree('tree')
        rev_id1 = tree.commit('one')
        tree2 = tree.bzrdir.sprout('tree2').open_workingtree()
        rev_id2 = tree2.commit('two')
        tree3 = tree2.bzrdir.sprout('tree3').open_workingtree()
        rev_id3 = tree2.commit('three')
        rev_id4 = tree3.commit('four')
        rev_id5 = tree3.commit('five')
        tree.merge_from_branch(tree2.branch)
        tree.merge_from_branch(tree3.branch, force=True)
        self.assertEqual([rev_id1, rev_id3, rev_id5], tree.get_parent_ids())

        self.addCleanup(tree.lock_read().unlock)
        pending_revisions = commit.pending_revisions(tree)
        # Two primary merges
        self.assertEqual(2, len(pending_revisions))
        # Revision == rev_id2
        self.assertEqual(rev_id3, pending_revisions[0][0].revision_id)
        self.assertEqual(rev_id5, pending_revisions[1][0].revision_id)
        # One child for the first merge
        self.assertEqual(1, len(pending_revisions[0][1]))
        self.assertEqual(rev_id2, pending_revisions[0][1][0].revision_id)
        # One child for the second merge
        self.assertEqual(1, len(pending_revisions[1][1]))
        self.assertEqual(rev_id4, pending_revisions[1][1][0].revision_id)


class Test_RevToPendingInfo(tests.TestCaseWithTransport):

    def test_basic_info(self):
        tree = self.make_branch_and_tree('tree')
        rev_id = tree.commit('Multiline\ncommit\nmessage',
                             committer='Joe Foo <joe@foo.com>',
                             timestamp=1191012408.674,
                             timezone=-18000
                             )
        rev = tree.branch.repository.get_revision(rev_id)
        rev_dict = commit.CommitDialog._rev_to_pending_info(rev)
        self.assertEqual({'committer':'Joe Foo',
                          'summary':'Multiline',
                          'date':'2007-09-28',
                          'revision_id':rev_id,
                         }, rev_dict)


class CommitDialogNoWidgets(commit.CommitDialog):

    def construct(self):
        pass # Don't create any widgets here

    def fill_in_data(self):
        pass # With no widgets, there are no widgets to fill out


class TestCommitDialogSimple(tests.TestCaseWithTransport):

    def test_setup_parameters_no_pending(self):
        tree = self.make_branch_and_tree('tree')
        rev_id = tree.commit('first')

        dlg = CommitDialogNoWidgets(tree)
        self.assertEqual(rev_id, dlg._basis_tree.get_revision_id())
        self.assertIs(None, dlg._pending)
        self.assertFalse(dlg._is_checkout)

    def test_setup_parameters_checkout(self):
        tree = self.make_branch_and_tree('tree')
        rev_id = tree.commit('first')
        tree2 = tree.bzrdir.sprout('tree2').open_workingtree()
        tree2.branch.bind(tree.branch)

        dlg = CommitDialogNoWidgets(tree2)
        self.assertEqual(rev_id, dlg._basis_tree.get_revision_id())
        self.assertIs(None, dlg._pending)
        self.assertTrue(dlg._is_checkout)

    def test_setup_parameters_pending(self):
        tree = self.make_branch_and_tree('tree')
        rev_id1 = tree.commit('one')
        tree2 = tree.bzrdir.sprout('tree2').open_workingtree()
        rev_id2 = tree2.commit('two')
        tree.merge_from_branch(tree2.branch)

        dlg = CommitDialogNoWidgets(tree)
        self.assertEqual(rev_id1, dlg._basis_tree.get_revision_id())
        self.assertIsNot(None, dlg._pending)
        self.assertEqual(1, len(dlg._pending))
        self.assertEqual(rev_id2, dlg._pending[0][0].revision_id)

    def test_setup_parameters_delta(self):
        tree = self.make_branch_and_tree('tree')
        self.build_tree(['tree/a'])
        tree.add(['a'], ['a-id'])

        dlg = CommitDialogNoWidgets(tree)
        self.assertIs(None, dlg._delta)
        dlg._compute_delta()

        delta = dlg._delta
        self.assertEqual([], delta.modified)
        self.assertEqual([], delta.renamed)
        self.assertEqual([], delta.removed)
        self.assertEqual([(u'a', 'a-id', 'file')], delta.added)


class TestCommitDialog(tests.TestCaseWithTransport):

    def test_bound(self):
        tree = self.make_branch_and_tree('tree')
        rev_id = tree.commit('first')
        tree2 = tree.bzrdir.sprout('tree2').open_workingtree()
        tree2.branch.bind(tree.branch)

        # tree is not a checkout
        dlg = commit.CommitDialog(tree)
        self.assertFalse(dlg._check_local.get_property('visible'))

        # tree2 is a checkout
        dlg2 = commit.CommitDialog(tree2)
        self.assertTrue(dlg2._check_local.get_property('visible'))

    def test_no_pending(self):
        tree = self.make_branch_and_tree('tree')
        rev_id1 = tree.commit('one')

        dlg = commit.CommitDialog(tree)

        self.assertFalse(dlg._pending_box.get_property('visible'))

        commit_col = dlg._treeview_files.get_column(0)
        self.assertEqual('Commit', commit_col.get_title())
        renderer = commit_col.get_cells()[0]
        self.assertTrue(renderer.get_property('activatable'))

        self.assertEqual('Commit all changes',
                         dlg._commit_all_files_radio.get_label())
        self.assertTrue(dlg._commit_all_files_radio.get_property('sensitive'))
        self.assertTrue(dlg._commit_selected_radio.get_property('sensitive'))

    def test_pending(self):
        tree = self.make_branch_and_tree('tree')
        rev_id1 = tree.commit('one')

        tree2 = tree.bzrdir.sprout('tree2').open_workingtree()
        rev_id2 = tree2.commit('two',
                               committer='Joe Foo <joe@foo.com>',
                               timestamp=1191264271.05,
                               timezone=+7200)
        tree.merge_from_branch(tree2.branch)

        dlg = commit.CommitDialog(tree)

        self.assertTrue(dlg._pending_box.get_property('visible'))

        commit_col = dlg._treeview_files.get_column(0)
        self.assertEqual('Commit*', commit_col.get_title())
        renderer = commit_col.get_cells()[0]
        self.assertFalse(renderer.get_property('activatable'))

        values = [(r[0], r[1], r[2], r[3]) for r in dlg._pending_store]
        self.assertEqual([(rev_id2, '2007-10-01', 'Joe Foo', 'two')], values)

        self.assertEqual('Commit all changes*',
                         dlg._commit_all_files_radio.get_label())
        self.assertFalse(dlg._commit_all_files_radio.get_property('sensitive'))
        self.assertFalse(dlg._commit_selected_radio.get_property('sensitive'))

    def test_pending_multiple(self):
        tree = self.make_branch_and_tree('tree')
        rev_id1 = tree.commit('one')

        tree2 = tree.bzrdir.sprout('tree2').open_workingtree()
        rev_id2 = tree2.commit('two',
                               committer='Joe Foo <joe@foo.com>',
                               timestamp=1191264271.05,
                               timezone=+7200)
        rev_id3 = tree2.commit('three',
                               committer='Jerry Foo <jerry@foo.com>',
                               timestamp=1191264278.05,
                               timezone=+7200)
        tree.merge_from_branch(tree2.branch)
        tree3 = tree.bzrdir.sprout('tree3').open_workingtree()
        rev_id4 = tree3.commit('four',
                               committer='Joe Foo <joe@foo.com>',
                               timestamp=1191264279.05,
                               timezone=+7200)
        rev_id5 = tree3.commit('five',
                               committer='Jerry Foo <jerry@foo.com>',
                               timestamp=1191372278.05,
                               timezone=+7200)
        tree.merge_from_branch(tree3.branch, force=True)

        dlg = commit.CommitDialog(tree)
        # TODO: assert that the pending box is set to show
        values = [(r[0], r[1], r[2], r[3]) for r in dlg._pending_store]
        self.assertEqual([(rev_id3, '2007-10-01', 'Jerry Foo', 'three'),
                          (rev_id2, '2007-10-01', 'Joe Foo', 'two'),
                          (rev_id5, '2007-10-03', 'Jerry Foo', 'five'),
                          (rev_id4, '2007-10-01', 'Joe Foo', 'four'),
                         ], values)

    def test_filelist_added(self):
        tree = self.make_branch_and_tree('tree')
        self.build_tree(['tree/a', 'tree/b/', 'tree/b/c'])
        tree.add(['a', 'b', 'b/c'], ['a-id', 'b-id', 'c-id'])

        dlg = commit.CommitDialog(tree)
        values = [(r[0], r[1], r[2], r[3], r[4]) for r in dlg._files_store]
        self.assertEqual([(None, None, True, 'All Files', ''),
                          ('a-id', 'a', True, 'a', 'added'),
                          ('b-id', 'b', True, 'b/', 'added'),
                          ('c-id', 'b/c', True, 'b/c', 'added'),
                         ], values)

    def test_filelist_renamed(self):
        tree = self.make_branch_and_tree('tree')
        self.build_tree(['tree/a', 'tree/b/', 'tree/b/c'])
        tree.add(['a', 'b', 'b/c'], ['a-id', 'b-id', 'c-id'])
        rev_id1 = tree.commit('one')

        tree.rename_one('b', 'd')
        tree.rename_one('a', 'd/a')

        dlg = commit.CommitDialog(tree)
        values = [(r[0], r[1], r[2], r[3], r[4]) for r in dlg._files_store]
        self.assertEqual([(None, None, True, 'All Files', ''),
                          ('b-id', 'd', True, 'b/ => d/', 'renamed'),
                          ('a-id', 'd/a', True, 'a => d/a', 'renamed'),
                         ], values)

    def test_filelist_modified(self):
        tree = self.make_branch_and_tree('tree')
        self.build_tree(['tree/a'])
        tree.add(['a'], ['a-id'])
        rev_id1 = tree.commit('one')

        self.build_tree_contents([('tree/a', 'new contents for a\n')])

        dlg = commit.CommitDialog(tree)
        values = [(r[0], r[1], r[2], r[3], r[4]) for r in dlg._files_store]
        self.assertEqual([(None, None, True, 'All Files', ''),
                          ('a-id', 'a', True, 'a', 'modified'),
                         ], values)

    def test_filelist_renamed_and_modified(self):
        tree = self.make_branch_and_tree('tree')
        self.build_tree(['tree/a', 'tree/b/', 'tree/b/c'])
        tree.add(['a', 'b', 'b/c'], ['a-id', 'b-id', 'c-id'])
        rev_id1 = tree.commit('one')

        tree.rename_one('b', 'd')
        tree.rename_one('a', 'd/a')
        self.build_tree_contents([('tree/d/a', 'new contents for a\n'),
                                  ('tree/d/c', 'new contents for c\n'),
                                 ])
        # 'c' is not considered renamed, because only its parent was moved, it
        # stayed in the same directory

        dlg = commit.CommitDialog(tree)
        values = [(r[0], r[1], r[2], r[3], r[4]) for r in dlg._files_store]
        self.assertEqual([(None, None, True, 'All Files', ''),
                          ('b-id', 'd', True, 'b/ => d/', 'renamed'),
                          ('a-id', 'd/a', True, 'a => d/a', 'renamed and modified'),
                          ('c-id', 'd/c', True, 'd/c', 'modified'),
                         ], values)

    def test_filelist_kind_changed(self):
        tree = self.make_branch_and_tree('tree')
        self.build_tree(['tree/a', 'tree/b'])
        tree.add(['a', 'b'], ['a-id', 'b-id'])
        tree.commit('one')

        os.remove('tree/a')
        self.build_tree(['tree/a/'])
        # XXX:  This is technically valid, and the file list handles it fine,
        #       but 'show_diff_trees()' does not, so we skip this part of the
        #       test for now.
        # tree.rename_one('b', 'c')
        # os.remove('tree/c')
        # self.build_tree(['tree/c/'])

        dlg = commit.CommitDialog(tree)
        values = [(r[0], r[1], r[2], r[3], r[4]) for r in dlg._files_store]
        self.assertEqual([(None, None, True, 'All Files', ''),
                          ('a-id', 'a', True, 'a => a/', 'kind changed'),
                          # ('b-id', 'c', True, 'b => c/', 'renamed and modified'),
                         ], values)

    def test_filelist_removed(self):
        tree = self.make_branch_and_tree('tree')
        self.build_tree(['tree/a', 'tree/b/'])
        tree.add(['a', 'b'], ['a-id', 'b-id'])
        tree.commit('one')

        os.remove('tree/a')
        tree.remove('b', force=True)

        dlg = commit.CommitDialog(tree)
        values = [(r[0], r[1], r[2], r[3], r[4]) for r in dlg._files_store]
        self.assertEqual([(None, None, True, 'All Files', ''),
                          ('a-id', 'a', True, 'a', 'removed'),
                          ('b-id', 'b', True, 'b/', 'removed'),
                         ], values)
        # All Files should be selected
        self.assertEqual(
            (Gtk.TreePath(path=0), None), dlg._treeview_files.get_cursor())

    def test_filelist_with_selected(self):
        tree = self.make_branch_and_tree('tree')
        self.build_tree(['tree/a', 'tree/b/'])
        tree.add(['a', 'b'], ['a-id', 'b-id'])

        dlg = commit.CommitDialog(tree, selected='a')
        values = [(r[0], r[1], r[2], r[3], r[4]) for r in dlg._files_store]
        self.assertEqual([(None, None, False, 'All Files', ''),
                          ('a-id', 'a', True, 'a', 'added'),
                          ('b-id', 'b', False, 'b/', 'added'),
                         ], values)
        # This file should also be selected in the file list, rather than the
        # 'All Files' selection
        self.assertEqual(
            (Gtk.TreePath(path=1), None), dlg._treeview_files.get_cursor())

    def test_diff_view(self):
        tree = self.make_branch_and_tree('tree')
        self.build_tree(['tree/a', 'tree/b'])
        tree.add(['a', 'b'], ['a-id', 'b-id'])
        tree.commit('one')

        self.build_tree_contents([('tree/a', 'new contents for a\n')])
        tree.remove('b')

        dlg = commit.CommitDialog(tree)
        diff_buffer = dlg._diff_view.buffer
        text = diff_buffer.get_text(diff_buffer.get_start_iter(),
                                    diff_buffer.get_end_iter(),
                                    True).splitlines(True)

        self.assertEqual("=== modified file 'a'\n", text[0])
        self.assertContainsRe(text[1],
            r"--- a\t\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d [+-]\d\d\d\d")
        self.assertContainsRe(text[2],
            r"\+\+\+ a\t\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d [+-]\d\d\d\d")
        self.assertEqual('@@ -1,1 +1,1 @@\n', text[3])
        self.assertEqual('-contents of tree/a\n', text[4])
        self.assertEqual('+new contents for a\n', text[5])
        self.assertEqual('\n', text[6])

        self.assertEqual("=== removed file 'b'\n", text[7])
        self.assertContainsRe(text[8],
            r"--- b\t\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d [+-]\d\d\d\d")
        self.assertEqual('+++ b\t1970-01-01 00:00:00 +0000\n', text[9])
        self.assertEqual('@@ -1,1 +0,0 @@\n', text[10])
        self.assertEqual('-contents of tree/b\n', text[11])
        self.assertEqual('\n', text[12])

        self.assertEqual('Diff for All Files', dlg._diff_label.get_text())

    def test_commit_partial_toggle(self):
        tree = self.make_branch_and_tree('tree')
        self.build_tree(['tree/a', 'tree/b'])
        tree.add(['a', 'b'], ['a-id', 'b-id'])

        dlg = commit.CommitDialog(tree)
        checked_col = dlg._treeview_files.get_column(0)
        self.assertFalse(checked_col.get_property('visible'))
        self.assertTrue(dlg._commit_all_changes)

        dlg._commit_selected_radio.set_active(True)
        self.assertTrue(checked_col.get_property('visible'))
        self.assertFalse(dlg._commit_all_changes)

    def test_file_selection(self):
        """Several things should happen when a file has been selected."""
        tree = self.make_branch_and_tree('tree')
        tree.branch.get_config().set_user_option('per_file_commits', 'true')
        self.build_tree(['tree/a', 'tree/b'])
        tree.add(['a', 'b'], ['a-id', 'b-id'])

        dlg = commit.CommitDialog(tree)
        diff_buffer = dlg._diff_view.buffer
        self.assertEqual('Diff for All Files', dlg._diff_label.get_text())
        self.assertEqual('File commit message',
                         dlg._file_message_expander.get_label())
        self.assertFalse(dlg._file_message_expander.get_expanded())
        self.assertFalse(dlg._file_message_expander.get_property('sensitive'))

        dlg._treeview_files.set_cursor(
            Gtk.TreePath(path=1), None, False)
        self.assertEqual('Diff for a', dlg._diff_label.get_text())
        text = diff_buffer.get_text(diff_buffer.get_start_iter(),
                                    diff_buffer.get_end_iter(),
                                    True).splitlines(True)
        self.assertEqual("=== added file 'a'\n", text[0])
        self.assertContainsRe(text[1],
            r"--- a\t\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d [+-]\d\d\d\d")
        self.assertContainsRe(text[2],
            r"\+\+\+ a\t\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d [+-]\d\d\d\d")
        self.assertEqual('@@ -0,0 +1,1 @@\n', text[3])
        self.assertEqual('+contents of tree/a\n', text[4])
        self.assertEqual('\n', text[5])
        self.assertEqual('Commit message for a',
                         dlg._file_message_expander.get_label())
        self.assertTrue(dlg._file_message_expander.get_expanded())
        self.assertTrue(dlg._file_message_expander.get_property('sensitive'))

        dlg._treeview_files.set_cursor(
            Gtk.TreePath(path=2), None, False)
        self.assertEqual('Diff for b', dlg._diff_label.get_text())
        text = diff_buffer.get_text(diff_buffer.get_start_iter(),
                                    diff_buffer.get_end_iter(),
                                    True).splitlines(True)
        self.assertEqual("=== added file 'b'\n", text[0])
        self.assertContainsRe(text[1],
            r"--- b\t\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d [+-]\d\d\d\d")
        self.assertContainsRe(text[2],
            r"\+\+\+ b\t\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d [+-]\d\d\d\d")
        self.assertEqual('@@ -0,0 +1,1 @@\n', text[3])
        self.assertEqual('+contents of tree/b\n', text[4])
        self.assertEqual('\n', text[5])
        self.assertEqual('Commit message for b',
                         dlg._file_message_expander.get_label())
        self.assertTrue(dlg._file_message_expander.get_expanded())
        self.assertTrue(dlg._file_message_expander.get_property('sensitive'))

        dlg._treeview_files.set_cursor(
            Gtk.TreePath(path=0), None, False)
        self.assertEqual('Diff for All Files', dlg._diff_label.get_text())
        self.assertEqual('File commit message',
                         dlg._file_message_expander.get_label())
        self.assertFalse(dlg._file_message_expander.get_expanded())
        self.assertFalse(dlg._file_message_expander.get_property('sensitive'))

    def test_file_selection_message(self):
        """Selecting a file should bring up its commit message."""
        tree = self.make_branch_and_tree('tree')
        tree.branch.get_config().set_user_option('per_file_commits', 'true')
        self.build_tree(['tree/a', 'tree/b/'])
        tree.add(['a', 'b'], ['a-id', 'b-id'])

        def get_file_text():
            buf = dlg._file_message_text_view.get_buffer()
            return buf.get_text(
                buf.get_start_iter(), buf.get_end_iter(), True)

        def get_saved_text(path):
            """Get the saved text for a given record."""
            return dlg._files_store.get_value(dlg._files_store.get_iter(path), 5)

        dlg = commit.CommitDialog(tree)
        self.assertEqual('File commit message',
                         dlg._file_message_expander.get_label())
        self.assertFalse(dlg._file_message_expander.get_expanded())
        self.assertFalse(dlg._file_message_expander.get_property('sensitive'))
        self.assertEqual('', get_file_text())

        dlg._treeview_files.set_cursor(
            Gtk.TreePath(path=1), None, False)
        self.assertEqual('Commit message for a',
                         dlg._file_message_expander.get_label())
        self.assertTrue(dlg._file_message_expander.get_expanded())
        self.assertTrue(dlg._file_message_expander.get_property('sensitive'))
        self.assertEqual('', get_file_text())

        self.assertEqual('', get_saved_text(1))
        dlg._set_file_commit_message('Some text\nfor a\n')
        dlg._save_current_file_message()
        # We should have updated the ListStore with the new file commit info
        self.assertEqual('Some text\nfor a\n', get_saved_text(1))

        dlg._treeview_files.set_cursor(
            Gtk.TreePath(path=2), None, False)
        self.assertEqual('Commit message for b/',
                         dlg._file_message_expander.get_label())
        self.assertTrue(dlg._file_message_expander.get_expanded())
        self.assertTrue(dlg._file_message_expander.get_property('sensitive'))
        self.assertEqual('', get_file_text())

        self.assertEqual('', get_saved_text(2))
        dlg._set_file_commit_message('More text\nfor b\n')
        # Now switch back to 'a'. The message should be saved, and the buffer
        # should be updated with the other text
        dlg._treeview_files.set_cursor(
            Gtk.TreePath(path=1), None, False)
        self.assertEqual('More text\nfor b\n', get_saved_text(2))
        self.assertEqual('Commit message for a',
                         dlg._file_message_expander.get_label())
        self.assertTrue(dlg._file_message_expander.get_expanded())
        self.assertTrue(dlg._file_message_expander.get_property('sensitive'))
        self.assertEqual('Some text\nfor a\n', get_file_text())

    def test_toggle_all_files(self):
        """When checking the All Files entry, it should toggle all fields"""
        tree = self.make_branch_and_tree('tree')
        self.build_tree(['tree/a', 'tree/b/'])
        tree.add(['a', 'b'], ['a-id', 'b-id'])

        dlg = commit.CommitDialog(tree)
        self.assertEqual([(None, None, True),
                          ('a-id', 'a', True),
                          ('b-id', 'b', True),
                         ], [(r[0], r[1], r[2]) for r in dlg._files_store])

        # TODO: jam 20071002 I'm not sure how to exactly trigger a toggle, it
        #       looks like we need to call renderer.activate() and pass an
        #       event and widget, and lots of other stuff I'm not sure what to
        #       do with. So instead, we just call toggle directly, and assume
        #       that toggle is hooked in correctly
        # column = dlg._treeview_files.get_column(0)
        # renderer = column.get_cells()[0]

        # Toggle a single entry should set just that entry to False
        dlg._toggle_commit(None, 1, dlg._files_store)
        self.assertEqual([(None, None, True),
                          ('a-id', 'a', False),
                          ('b-id', 'b', True),
                         ], [(r[0], r[1], r[2]) for r in dlg._files_store])

        # Toggling the main entry should set all entries
        dlg._toggle_commit(None, 0, dlg._files_store)
        self.assertEqual([(None, None, False),
                          ('a-id', 'a', False),
                          ('b-id', 'b', False),
                         ], [(r[0], r[1], r[2]) for r in dlg._files_store])

        dlg._toggle_commit(None, 2, dlg._files_store)
        self.assertEqual([(None, None, False),
                          ('a-id', 'a', False),
                          ('b-id', 'b', True),
                         ], [(r[0], r[1], r[2]) for r in dlg._files_store])

        dlg._toggle_commit(None, 0, dlg._files_store)
        self.assertEqual([(None, None, True),
                          ('a-id', 'a', True),
                          ('b-id', 'b', True),
                         ], [(r[0], r[1], r[2]) for r in dlg._files_store])

    def test_specific_files(self):
        tree = self.make_branch_and_tree('tree')
        self.build_tree(['tree/a', 'tree/b/'])
        tree.add(['a', 'b'], ['a-id', 'b-id'])

        dlg = commit.CommitDialog(tree)
        self.assertEqual((['a', 'b'], []), dlg._get_specific_files())

        dlg._commit_selected_radio.set_active(True)
        dlg._toggle_commit(None, 0, dlg._files_store)
        self.assertEqual(([], []), dlg._get_specific_files())

        dlg._toggle_commit(None, 1, dlg._files_store)
        self.assertEqual((['a'], []), dlg._get_specific_files())

    def test_specific_files_with_messages(self):
        tree = self.make_branch_and_tree('tree')
        tree.branch.get_config().set_user_option('per_file_commits', 'true')
        self.build_tree(['tree/a_file', 'tree/b_dir/'])
        tree.add(['a_file', 'b_dir'], ['1a-id', '0b-id'])

        dlg = commit.CommitDialog(tree)
        dlg._commit_selected_radio.set_active(True)
        self.assertEqual((['a_file', 'b_dir'], []), dlg._get_specific_files())

        dlg._treeview_files.set_cursor(
            Gtk.TreePath(path=1), None, False)
        dlg._set_file_commit_message('Test\nmessage\nfor a_file\n')
        dlg._treeview_files.set_cursor(
            Gtk.TreePath(path=2), None, False)
        dlg._set_file_commit_message('message\nfor b_dir\n')

        self.assertEqual((['a_file', 'b_dir'],
                          [{'path':'a_file', 'file_id':'1a-id',
                            'message':'Test\nmessage\nfor a_file\n'},
                           {'path':'b_dir', 'file_id':'0b-id',
                            'message':'message\nfor b_dir\n'},
                          ]), dlg._get_specific_files())

        dlg._toggle_commit(None, 1, dlg._files_store)
        self.assertEqual((['b_dir'],
                          [{'path':'b_dir', 'file_id':'0b-id',
                            'message':'message\nfor b_dir\n'},
                          ]), dlg._get_specific_files())

    def test_specific_files_sanitizes_messages(self):
        tree = self.make_branch_and_tree('tree')
        tree.branch.get_config().set_user_option('per_file_commits', 'true')
        self.build_tree(['tree/a_file', 'tree/b_dir/'])
        tree.add(['a_file', 'b_dir'], ['1a-id', '0b-id'])

        dlg = commit.CommitDialog(tree)
        dlg._commit_selected_radio.set_active(True)
        self.assertEqual((['a_file', 'b_dir'], []), dlg._get_specific_files())

        dlg._treeview_files.set_cursor(
            Gtk.TreePath(path=1), None, False)
        dlg._set_file_commit_message('Test\r\nmessage\rfor a_file\n')
        dlg._treeview_files.set_cursor(
            Gtk.TreePath(path=2), None, False)
        dlg._set_file_commit_message('message\r\nfor\nb_dir\r')

        self.assertEqual((['a_file', 'b_dir'],
                          [{'path':'a_file', 'file_id':'1a-id',
                            'message':'Test\nmessage\nfor a_file\n'},
                           {'path':'b_dir', 'file_id':'0b-id',
                            'message':'message\nfor\nb_dir\n'},
                          ]), dlg._get_specific_files())


class QuestionHelpers(object):

    def _set_question_yes(self, dlg):
        """Set the dialog to answer YES to any questions."""
        self.questions = []
        def _question_yes(*args, **kwargs):
            self.questions.append(args)
            self.questions.append('YES')
            return Gtk.ResponseType.YES
        dlg._question_dialog = _question_yes

    def _set_question_no(self, dlg):
        """Set the dialog to answer NO to any questions."""
        self.questions = []
        def _question_no(*args, **kwargs):
            self.questions.append(args)
            self.questions.append('NO')
            return Gtk.ResponseType.NO
        dlg._question_dialog = _question_no


class TestCommitDialog_Commit(tests.TestCaseWithTransport, QuestionHelpers):
    """Tests on the actual 'commit' button being pushed."""

    def test_bound_commit_local(self):
        tree = self.make_branch_and_tree('tree')
        self.build_tree(['tree/a'])
        tree.add(['a'], ['a-id'])
        rev_id1 = tree.commit('one')

        tree2 = tree.bzrdir.sprout('tree2').open_workingtree()
        self.build_tree(['tree2/b'])
        tree2.add(['b'], ['b-id'])
        tree2.branch.bind(tree.branch)

        dlg = commit.CommitDialog(tree2)
        # With the check box set, it should only effect the local branch
        dlg._check_local.set_active(True)
        dlg._set_global_commit_message('Commit message\n')
        dlg._do_commit()

        last_rev = tree2.last_revision()
        self.assertEqual(last_rev, dlg.committed_revision_id)
        self.assertEqual(rev_id1, tree.branch.last_revision())

    def test_commit_global_sanitizes_message(self):
        tree = self.make_branch_and_tree('tree')
        self.build_tree(['tree/a'])
        tree.add(['a'], ['a-id'])
        rev_id1 = tree.commit('one')

        self.build_tree(['tree/b'])
        tree.add(['b'], ['b-id'])
        dlg = commit.CommitDialog(tree)
        # With the check box set, it should only effect the local branch
        dlg._set_global_commit_message('Commit\r\nmessage\rfoo\n')
        dlg._do_commit()
        rev = tree.branch.repository.get_revision(tree.last_revision())
        self.assertEqual('Commit\nmessage\nfoo\n', rev.message)

    def test_bound_commit_both(self):
        tree = self.make_branch_and_tree('tree')
        self.build_tree(['tree/a'])
        tree.add(['a'], ['a-id'])
        rev_id1 = tree.commit('one')

        tree2 = tree.bzrdir.sprout('tree2').open_workingtree()
        self.build_tree(['tree2/b'])
        tree2.add(['b'], ['b-id'])
        tree2.branch.bind(tree.branch)

        dlg = commit.CommitDialog(tree2)
        # With the check box set, it should only effect the local branch
        dlg._check_local.set_active(False)
        dlg._set_global_commit_message('Commit message\n')
        dlg._do_commit()

        last_rev = tree2.last_revision()
        self.assertEqual(last_rev, dlg.committed_revision_id)
        self.assertEqual(last_rev, tree.branch.last_revision())

    def test_commit_empty_message(self):
        tree = self.make_branch_and_tree('tree')
        self.build_tree(['tree/a', 'tree/b'])
        tree.add(['a'], ['a-id'])
        rev_id = tree.commit('one')

        tree.add(['b'], ['b-id'])

        dlg = commit.CommitDialog(tree)
        self._set_question_no(dlg)
        dlg._do_commit()
        self.assertEqual(
            [('Commit with an empty message?',
              'You can describe your commit intent in the message.'),
              'NO',
            ], self.questions)
        # By saying NO, nothing should be committed.
        self.assertEqual(rev_id, tree.last_revision())
        self.assertIs(None, dlg.committed_revision_id)
        self.assertTrue(dlg._global_message_text_view.get_property('is-focus'))

        self._set_question_yes(dlg)

        dlg._do_commit()
        self.assertEqual(
            [('Commit with an empty message?',
              'You can describe your commit intent in the message.'),
              'YES',
            ], self.questions)
        committed = tree.last_revision()
        self.assertNotEqual(rev_id, committed)
        self.assertEqual(committed, dlg.committed_revision_id)

    def test_initial_commit(self):
        tree = self.make_branch_and_tree('tree')
        self.build_tree(['tree/a'])
        tree.add(['a'], ['a-id'])

        dlg = commit.CommitDialog(tree)
        dlg._set_global_commit_message('Some text\n')
        dlg._do_commit()

        last_rev = tree.last_revision()
        self.assertEqual(last_rev, dlg.committed_revision_id)
        rev = tree.branch.repository.get_revision(last_rev)
        self.assertEqual(last_rev, rev.revision_id)
        self.assertEqual('Some text\n', rev.message)

    def test_pointless_commit(self):
        tree = self.make_branch_and_tree('tree')
        self.build_tree(['tree/a'])
        tree.add(['a'], ['a-id'])
        rev_id1 = tree.commit('one')

        dlg = commit.CommitDialog(tree)
        dlg._set_global_commit_message('Some text\n')

        self._set_question_no(dlg)
        dlg._do_commit()

        self.assertIs(None, dlg.committed_revision_id)
        self.assertEqual(rev_id1, tree.last_revision())
        self.assertEqual(
            [('Commit with no changes?',
              'There are no changes in the working tree.'
              ' Do you want to commit anyway?'),
              'NO',
            ], self.questions)

        self._set_question_yes(dlg)
        dlg._do_commit()

        rev_id2 = tree.last_revision()
        self.assertEqual(rev_id2, dlg.committed_revision_id)
        self.assertNotEqual(rev_id1, rev_id2)
        self.assertEqual(
            [('Commit with no changes?',
              'There are no changes in the working tree.'
              ' Do you want to commit anyway?'),
              'YES',
            ], self.questions)

    def test_unknowns(self):
        """We should check if there are unknown files."""
        tree = self.make_branch_and_tree('tree')
        rev_id1 = tree.commit('one')
        self.build_tree(['tree/a', 'tree/b'])
        tree.add(['a'], ['a-id'])

        dlg = commit.CommitDialog(tree)
        dlg._set_global_commit_message('Some text\n')
        self._set_question_no(dlg)

        dlg._do_commit()

        self.assertIs(None, dlg.committed_revision_id)
        self.assertEqual(rev_id1, tree.last_revision())
        self.assertEqual(
            [("Commit with unknowns?",
              "Unknown files exist in the working tree. Commit anyway?"),
              "NO",
            ], self.questions)

        self._set_question_yes(dlg)
        dlg._do_commit()

        rev_id2 = tree.last_revision()
        self.assertNotEqual(rev_id1, rev_id2)
        self.assertEqual(rev_id2, dlg.committed_revision_id)
        self.assertEqual(
            [("Commit with unknowns?",
              "Unknown files exist in the working tree. Commit anyway?"),
              "YES",
            ], self.questions)

    def test_commit_specific_files(self):
        tree = self.make_branch_and_tree('tree')
        rev_id1 = tree.commit('one')
        self.build_tree(['tree/a', 'tree/b'])
        tree.add(['a', 'b'], ['a-id', 'b-id'])

        dlg = commit.CommitDialog(tree)
        dlg._commit_selected_radio.set_active(True) # enable partial
        dlg._toggle_commit(None, 2, dlg._files_store) # unset 'b'

        dlg._set_global_commit_message('Committing just "a"\n')
        dlg._do_commit()

        rev_id2 = dlg.committed_revision_id
        self.assertIsNot(None, rev_id2)
        self.assertEqual(rev_id2, tree.last_revision())

        rt = tree.branch.repository.revision_tree(rev_id2)
        entries = [(path, ie.file_id) for path, ie in rt.iter_entries_by_dir()
                                       if path] # Ignore the root entry
        self.assertEqual([('a', 'a-id')], entries)

    def test_commit_partial_no_partial(self):
        """Ignore the checkboxes if committing all files."""
        tree = self.make_branch_and_tree('tree')
        rev_id1 = tree.commit('one')
        self.build_tree(['tree/a', 'tree/b'])
        tree.add(['a', 'b'], ['a-id', 'b-id'])

        dlg = commit.CommitDialog(tree)
        dlg._commit_selected_radio.set_active(True) # enable partial
        dlg._toggle_commit(None, 2, dlg._files_store) # unset 'b'

        # Switch back to committing all changes
        dlg._commit_all_files_radio.set_active(True)

        dlg._set_global_commit_message('Committing everything\n')
        dlg._do_commit()

        rev_id2 = dlg.committed_revision_id
        self.assertIsNot(None, rev_id2)
        self.assertEqual(rev_id2, tree.last_revision())

        rt = tree.branch.repository.revision_tree(rev_id2)
        entries = [(path, ie.file_id) for path, ie in rt.iter_entries_by_dir()
                                       if path] # Ignore the root entry
        self.assertEqual([('a', 'a-id'), ('b', 'b-id')], entries)

    def test_commit_no_messages(self):
        tree = self.make_branch_and_tree('tree')
        rev_id1 = tree.commit('one')
        self.build_tree(['tree/a', 'tree/b'])
        tree.add(['a', 'b'], ['a-id', 'b-id'])

        dlg = commit.CommitDialog(tree)
        dlg._set_global_commit_message('Simple commit\n')
        dlg._do_commit()

        rev = tree.branch.repository.get_revision(dlg.committed_revision_id)
        self.failIf('file-info' in rev.properties)

    def test_commit_disabled_messages(self):
        tree = self.make_branch_and_tree('tree')
        rev_id1 = tree.commit('one')

        self.build_tree(['tree/a', 'tree/b'])
        tree.add(['a', 'b'], ['a-id', 'b-id'])

        dlg = commit.CommitDialog(tree)
        self.assertFalse(dlg._file_message_expander.get_property('visible'))
        self.assertEqual('Commit Message',
                         dlg._global_message_label.get_text())

        tree.branch.get_config().set_user_option('per_file_commits', 'true')
        dlg = commit.CommitDialog(tree)
        self.assertTrue(dlg._file_message_expander.get_property('visible'))
        self.assertEqual('Global Commit Message',
                         dlg._global_message_label.get_text())

        tree.branch.get_config().set_user_option('per_file_commits', 'on')
        dlg = commit.CommitDialog(tree)
        self.assertTrue(dlg._file_message_expander.get_property('visible'))
        self.assertEqual('Global Commit Message',
                         dlg._global_message_label.get_text())

        tree.branch.get_config().set_user_option('per_file_commits', 'y')
        dlg = commit.CommitDialog(tree)
        self.assertTrue(dlg._file_message_expander.get_property('visible'))
        self.assertEqual('Global Commit Message',
                         dlg._global_message_label.get_text())

        tree.branch.get_config().set_user_option('per_file_commits', 'n')
        dlg = commit.CommitDialog(tree)
        self.assertFalse(dlg._file_message_expander.get_property('visible'))
        self.assertEqual('Commit Message',
                         dlg._global_message_label.get_text())

    def test_commit_specific_files_with_messages(self):
        tree = self.make_branch_and_tree('tree')
        tree.branch.get_config().set_user_option('per_file_commits', 'true')
        rev_id1 = tree.commit('one')
        self.build_tree(['tree/a', 'tree/b'])
        tree.add(['a', 'b'], ['a-id', 'b-id'])

        dlg = commit.CommitDialog(tree)
        dlg._commit_selected_radio.set_active(True) # enable partial
        dlg._treeview_files.set_cursor(
            Gtk.TreePath(path=1), None, False)
        dlg._set_file_commit_message('Message for A\n')
        dlg._treeview_files.set_cursor(
            Gtk.TreePath(path=2), None, False)
        dlg._set_file_commit_message('Message for B\n')
        dlg._toggle_commit(None, 2, dlg._files_store) # unset 'b'
        dlg._set_global_commit_message('Commit just "a"')

        dlg._do_commit()

        rev_id2 = dlg.committed_revision_id
        self.assertEqual(rev_id2, tree.last_revision())
        rev = tree.branch.repository.get_revision(rev_id2)
        self.assertEqual('Commit just "a"', rev.message)
        file_info = rev.properties['file-info']
        self.assertEqual(u'ld7:file_id4:a-id'
                         '7:message14:Message for A\n'
                         '4:path1:a'
                         'ee',
                         file_info)
        self.assertEqual([{'path':'a', 'file_id':'a-id',
                           'message':'Message for A\n'},],
                         bencode.bdecode(file_info.encode('UTF-8')))

    def test_commit_messages_after_merge(self):
        tree = self.make_branch_and_tree('tree')
        tree.branch.get_config().set_user_option('per_file_commits', 'true')
        rev_id1 = tree.commit('one')
        tree2 = tree.bzrdir.sprout('tree2').open_workingtree()
        self.build_tree(['tree2/a', 'tree2/b'])
        tree2.add(['a', 'b'], ['a-id', 'b-id'])
        rev_id2 = tree2.commit('two')

        tree.merge_from_branch(tree2.branch)

        dlg = commit.CommitDialog(tree)
        dlg._treeview_files.set_cursor(
            Gtk.TreePath(path=1), None, False) # 'a'
        dlg._set_file_commit_message('Message for A\n')
        # No message for 'B'
        dlg._set_global_commit_message('Merging from "tree2"\n')

        dlg._do_commit()

        rev_id3 = dlg.committed_revision_id
        self.assertEqual(rev_id3, tree.last_revision())
        rev = tree.branch.repository.get_revision(rev_id3)
        self.assertEqual('Merging from "tree2"\n', rev.message)
        self.assertEqual([rev_id1, rev_id2], rev.parent_ids)
        file_info = rev.properties['file-info']
        self.assertEqual(u'ld7:file_id4:a-id'
                         '7:message14:Message for A\n'
                         '4:path1:a'
                         'ee',
                         file_info)
        self.assertEqual([{'path':'a', 'file_id':'a-id',
                           'message':'Message for A\n'},],
                         bencode.bdecode(file_info.encode('UTF-8')))

    def test_commit_unicode_messages(self):
        self.requireFeature(UnicodeFilenameFeature)

        tree = self.make_branch_and_tree('tree')
        tree.branch.get_config().set_user_option('per_file_commits', 'true')
        self.build_tree(['tree/a', u'tree/\u03a9'])
        tree.add(['a', u'\u03a9'], ['a-id', 'omega-id'])

        dlg = commit.CommitDialog(tree)
        dlg._treeview_files.set_cursor(
            Gtk.TreePath(path=1), None, False) # 'a'
        dlg._set_file_commit_message(u'Test \xfan\xecc\xf6de\n')
        dlg._treeview_files.set_cursor(
            Gtk.TreePath(path=2), None, False) # omega
        dlg._set_file_commit_message(u'\u03a9 is the end of all things.\n')
        dlg._set_global_commit_message(u'\u03a9 and \xfan\xecc\xf6de\n')

        self.assertEqual(([u'a', u'\u03a9'],
                          [{'path':'a', 'file_id':'a-id',
                            'message':'Test \xc3\xban\xc3\xacc\xc3\xb6de\n'},
                           {'path':'\xce\xa9', 'file_id':'omega-id',
                            'message':'\xce\xa9 is the end of all things.\n'},
                          ]), dlg._get_specific_files())

        dlg._do_commit()

        rev = tree.branch.repository.get_revision(dlg.committed_revision_id)
        file_info = rev.properties['file-info'].encode('UTF-8')
        value = ('ld7:file_id4:a-id'
                   '7:message16:Test \xc3\xban\xc3\xacc\xc3\xb6de\n'
                   '4:path1:a'
                  'e'
                  'd7:file_id8:omega-id'
                   '7:message29:\xce\xa9 is the end of all things.\n'
                   '4:path2:\xce\xa9'
                  'e'
                 'e')
        self.assertEqual(value, file_info)
        file_info_decoded = bencode.bdecode(file_info)
        for d in file_info_decoded:
            d['path'] = d['path'].decode('UTF-8')
            d['message'] = d['message'].decode('UTF-8')

        self.assertEqual([{'path':u'a', 'file_id':'a-id',
                           'message':u'Test \xfan\xecc\xf6de\n'},
                          {'path':u'\u03a9', 'file_id':'omega-id',
                           'message':u'\u03a9 is the end of all things.\n'},
                         ], file_info_decoded)


class TestSanitizeMessage(tests.TestCase):

    def assertSanitize(self, expected, original):
        self.assertEqual(expected,
                         commit._sanitize_and_decode_message(original))

    def test_untouched(self):
        self.assertSanitize('foo\nbar\nbaz\n', 'foo\nbar\nbaz\n')

    def test_converts_cr_to_lf(self):
        self.assertSanitize('foo\nbar\nbaz\n', 'foo\rbar\rbaz\r')

    def test_converts_crlf_to_lf(self):
        self.assertSanitize('foo\nbar\nbaz\n', 'foo\r\nbar\r\nbaz\r\n')

    def test_converts_mixed_to_lf(self):
        self.assertSanitize('foo\nbar\nbaz\n', 'foo\r\nbar\rbaz\n')


class TestSavedCommitMessages(tests.TestCaseWithTransport):

    def setUp(self):
        super(TestSavedCommitMessages, self).setUp()
        # Install our hook
        branch.Branch.hooks.install_named_hook(
            'post_uncommit', commitmsgs.save_commit_messages, None)

    def _get_file_info_dict(self, rank):
        file_info = [dict(path='a', file_id='a-id', message='a msg %d' % rank),
                     dict(path='b', file_id='b-id', message='b msg %d' % rank)]
        return file_info

    def _get_file_info_revprops(self, rank):
        file_info_prop = self._get_file_info_dict(rank)
        return {'file-info': bencode.bencode(file_info_prop).decode('UTF-8')}

    def _get_commit_message(self):
        return self.config.get_user_option('gtk_global_commit_message')

    def _get_file_commit_messages(self):
        return self.config.get_user_option('gtk_file_commit_messages')


class TestUncommitHook(TestSavedCommitMessages):

    def setUp(self):
        super(TestUncommitHook, self).setUp()
        self.tree = self.make_branch_and_tree('tree')
        self.config = self.tree.branch.get_config()
        self.build_tree(['tree/a', 'tree/b'])
        self.tree.add(['a'], ['a-id'])
        self.tree.add(['b'], ['b-id'])
        rev1 = self.tree.commit('one', rev_id='one-id',
                                revprops=self._get_file_info_revprops(1))
        rev2 = self.tree.commit('two', rev_id='two-id',
                                revprops=self._get_file_info_revprops(2))
        rev3 = self.tree.commit('three', rev_id='three-id',
                                revprops=self._get_file_info_revprops(3))

    def test_uncommit_one_by_one(self):
        uncommit.uncommit(self.tree.branch, tree=self.tree)
        self.assertEquals(u'three', self._get_commit_message())
        self.assertEquals(u'd4:a-id7:a msg 34:b-id7:b msg 3e',
                          self._get_file_commit_messages())

        uncommit.uncommit(self.tree.branch, tree=self.tree)
        self.assertEquals(u'two\n******\nthree', self._get_commit_message())
        self.assertEquals(u'd4:a-id22:a msg 2\n******\na msg 3'
                          '4:b-id22:b msg 2\n******\nb msg 3e',
                          self._get_file_commit_messages())

        uncommit.uncommit(self.tree.branch, tree=self.tree)
        self.assertEquals(u'one\n******\ntwo\n******\nthree',
                          self._get_commit_message())
        self.assertEquals(u'd4:a-id37:a msg 1\n******\na msg 2\n******\na msg 3'
                          '4:b-id37:b msg 1\n******\nb msg 2\n******\nb msg 3e',
                          self._get_file_commit_messages())

    def test_uncommit_all_at_once(self):
        uncommit.uncommit(self.tree.branch, tree=self.tree, revno=1)
        self.assertEquals(u'one\n******\ntwo\n******\nthree',
                          self._get_commit_message())
        self.assertEquals(u'd4:a-id37:a msg 1\n******\na msg 2\n******\na msg 3'
                          '4:b-id37:b msg 1\n******\nb msg 2\n******\nb msg 3e',
                          self._get_file_commit_messages())


class TestReusingSavedCommitMessages(TestSavedCommitMessages, QuestionHelpers):

    def setUp(self):
        super(TestReusingSavedCommitMessages, self).setUp()
        self.tree = self.make_branch_and_tree('tree')
        self.config = self.tree.branch.get_config()
        self.config.set_user_option('per_file_commits', 'true')
        self.build_tree(['tree/a', 'tree/b'])
        self.tree.add(['a'], ['a-id'])
        self.tree.add(['b'], ['b-id'])
        rev1 = self.tree.commit('one', revprops=self._get_file_info_revprops(1))
        rev2 = self.tree.commit('two', revprops=self._get_file_info_revprops(2))
        uncommit.uncommit(self.tree.branch, tree=self.tree)
        self.build_tree_contents([('tree/a', 'new a content\n'),
                                  ('tree/b', 'new b content'),])

    def _get_commit_dialog(self, tree):
        # Ensure we will never use a dialog that can actually prompt the user
        # during the test suite. Test *can* and *should* override with the
        # correct question dialog type.
        dlg = commit.CommitDialog(tree)
        self._set_question_no(dlg)
        return dlg

    def test_setup_saved_messages(self):
        # Check the initial setup
        self.assertEquals(u'two', self._get_commit_message())
        self.assertEquals(u'd4:a-id7:a msg 24:b-id7:b msg 2e',
                          self._get_file_commit_messages())

    def test_messages_are_reloaded(self):
        dlg = self._get_commit_dialog(self.tree)
        self.assertEquals(u'two', dlg._get_global_commit_message())
        self.assertEquals(([u'a', u'b'],
                           [{ 'path': 'a',
                             'file_id': 'a-id', 'message': 'a msg 2',},
                           {'path': 'b',
                            'file_id': 'b-id', 'message': 'b msg 2',}],),
                          dlg._get_specific_files())

    def test_messages_are_consumed(self):
        dlg = self._get_commit_dialog(self.tree)
        dlg._do_commit()
        self.assertEquals(u'', self._get_commit_message())
        self.assertEquals(u'de', self._get_file_commit_messages())

    def test_messages_are_saved_on_cancel_if_required(self):
        dlg = self._get_commit_dialog(self.tree)
        self._set_question_yes(dlg) # Save messages
        dlg._do_cancel()
        self.assertEquals(u'two', self._get_commit_message())
        self.assertEquals(u'd4:a-id7:a msg 24:b-id7:b msg 2e',
                          self._get_file_commit_messages())

    def test_messages_are_cleared_on_cancel_if_required(self):
        dlg = self._get_commit_dialog(self.tree)
        self._set_question_no(dlg) # Don't save messages
        dlg._do_cancel()
        self.assertEquals(u'', self._get_commit_message())
        self.assertEquals(u'de',
                          self._get_file_commit_messages())
