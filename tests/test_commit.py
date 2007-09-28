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


class TestCommitDialog(tests.TestCaseWithTransport):

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
        delta = dlg._delta
        self.assertEqual([], delta.modified)
        self.assertEqual([], delta.renamed)
        self.assertEqual([], delta.removed)
        self.assertEqual([(u'a', 'a-id', 'file')], delta.added)
