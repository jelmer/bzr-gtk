# Copyright (C) 2007 John Arbash Meinel <john@arbash-meinel.com>
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

from bzrlib import (
    tests,
    revision,
    )

from bzrlib.plugins.gtk import commit


# TODO: All we need is basic ancestry code to test this, we shouldn't need a
# TestCaseWithTransport, just a TestCaseWithMemoryTransport or somesuch.

class TestPendingRevisions(tests.TestCaseWithTransport):

    def test_pending_revisions_none(self):
        tree = self.make_branch_and_tree('.')
        tree.commit('one')

        self.assertIs(None, commit.pending_revisions(tree))

    def test_pending_revisions_simple(self):
        tree = self.make_branch_and_tree('tree')
        rev_id1 = tree.commit('one')
        tree2 = tree.bzrdir.sprout('tree2').open_workingtree()
        rev_id2 = tree2.commit('two')
        tree.merge_from_branch(tree2.branch)
        self.assertEqual([rev_id1, rev_id2], tree.get_parent_ids())

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
        rev_id3 = tree2.commit('three')
        tree3 = tree2.bzrdir.sprout('tree3').open_workingtree()
        rev_id4 = tree3.commit('four')
        rev_id5 = tree3.commit('five')
        tree.merge_from_branch(tree2.branch)
        tree.merge_from_branch(tree3.branch)
        self.assertEqual([rev_id1, rev_id3, rev_id5], tree.get_parent_ids())

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

    def test_no_pending(self):
        tree = self.make_branch_and_tree('tree')
        rev_id1 = tree.commit('one')

        dlg = commit.CommitDialog(tree)
        # TODO: assert that the pending box is hidden
        commit_col = dlg._treeview_files.get_column(0)
        self.assertEqual('Commit', commit_col.get_title())

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
        # TODO: assert that the pending box is set to show
        commit_col = dlg._treeview_files.get_column(0)
        self.assertEqual('Commit*', commit_col.get_title())

        values = [(r[0], r[1], r[2], r[3]) for r in dlg._pending_store]
        self.assertEqual([(rev_id2, '2007-10-01', 'Joe Foo', 'two')], values)

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
        tree.merge_from_branch(tree3.branch)

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
        self.assertEqual([('a-id', 'a', True, 'a', 'added'),
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
        self.assertEqual([('b-id', 'd', True, 'b/ => d/', 'renamed'),
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
        self.assertEqual([('a-id', 'a', True, 'a', 'modified'),
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
        self.assertEqual([('b-id', 'd', True, 'b/ => d/', 'renamed'),
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
        self.assertEqual([('a-id', 'a', True, 'a => a/', 'kind changed'),
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
        self.assertEqual([('a-id', 'a', True, 'a', 'removed'),
                          ('b-id', 'b', True, 'b/', 'removed'),
                         ], values)
