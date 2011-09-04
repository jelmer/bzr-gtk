# Copyright (C) 2011 Curtis Hovey <sinzui.is@verizon.net>
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

"""Test the BranchTreeModel functionality."""

from time import (
    strftime,
    localtime,
    )

from bzrlib import (
    tests,
    )

from bzrlib.plugins.gtk.branchview.treemodel import BranchTreeModel


class BranchTreeModelTestCase(tests.TestCaseWithMemoryTransport):

    def make_test_branch(self, revid, message=None, committer=None):
        builder = self.make_branch_builder('test')
        builder.build_snapshot(
            revid, None, [('add', ('', 'root-id', 'directory', None))],
            message=message, committer=committer)
        return builder.get_branch()

    def test_init(self):
        branch = self.make_test_branch('A')
        revision = branch.repository.get_revision('A')
        branch.tags.set_tag('2.0', revision.revision_id)
        model = BranchTreeModel(branch, [])
        self.assertEqual(branch, model.branch)
        self.assertEqual(branch.repository, model.repository)
        self.assertEqual({'A': [u'2.0']}, model.tags)
        self.assertEqual({}, model.revisions)
        self.assertEqual([], model.line_graph_data)

    def test_add_tag_create(self):
        branch = self.make_test_branch('A')
        revision = branch.repository.get_revision('A')
        model = BranchTreeModel(branch, [])
        model.add_tag('2.0', revision.revision_id)
        self.assertEqual({'A': [u'2.0']}, model.tags)

    def test_add_tag_append(self):
        branch = self.make_test_branch('A')
        revision = branch.repository.get_revision('A')
        branch.tags.set_tag('2.0', revision.revision_id)
        model = BranchTreeModel(branch, [])
        model.add_tag('2.1', revision.revision_id)
        self.assertEqual({'A': ['2.0', '2.1']}, model.tags)

    def test_line_graph_item_to_model_row(self):
        branch = self.make_test_branch(
            'A', message='badger', committer='fnord')
        revision = branch.repository.get_revision('A')
        branch.tags.set_tag('2.0', revision.revision_id)
        model = BranchTreeModel(branch, [])
        data_item = (
            revision.revision_id, (1, 0), (5, 6, 0.5), ('B'), ('C'), [12, 34])
        row = model._line_graph_item_to_model_row(0, data_item)
        self.assertEqual(revision.revision_id, row[0], 'Wrong revid.')
        self.assertEqual((1, 0), row[1], 'Wrong node.')
        self.assertEqual((5, 6, 0.5), row[2], 'Wrong lines.')
        self.assertEqual([], row[3], 'Wrong last_lines.')
        self.assertEqual('12.34', row[4], 'Wrong revno.')
        self.assertEqual('badger', row[5], 'Wrong summary.')
        self.assertEqual('badger', row[6], 'Wrong message.')
        self.assertEqual('fnord', row[7], 'wrong committer.')
        self.assertEqual(
            strftime("%Y-%m-%d %H:%M", localtime(revision.timestamp)),
            row[8], 'Wrong timestamp.')
        self.assertEqual(revision, row[9], 'Wrong revision.')
        self.assertEqual(('B'), row[10], 'Wrong parents.')
        self.assertEqual(('C'), row[11], 'Wrong children.')
        self.assertEqual(['2.0'], row[12], 'Wrong tags.')
        self.assertEqual('fnord', row[13], 'Wrong authors.')

    def test_set_line_graph_data(self):
        branch = self.make_test_branch(
            'A', message='badger', committer='fnord')
        rev_id = branch.repository.get_revision('A').revision_id
        model = BranchTreeModel(branch, [])
        data = [(rev_id, (2, 0), (3, 4, 0.5), None, None, [1, 2])]
        model.set_line_graph_data(data)
        self.assertEqual(data, model.line_graph_data)
        tree_iter = model.get_iter_first()
        self.assertEqual(rev_id, model.get_value(tree_iter, 0))
