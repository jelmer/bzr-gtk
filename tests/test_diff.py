# -*- coding: utf-8 -*-
# Copyright (C) 2007 Adeodato Simó <dato@net.com.org.es>
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

from cStringIO import StringIO
import os

from bzrlib import (
    conflicts,
    errors,
    tests,
    )
try:
    from bzrlib.tests.features import UnicodeFilenameFeature
except ImportError: # bzr < 2.5
    from bzrlib.tests import UnicodeFilenameFeature
from bzrlib.merge_directive import MergeDirective2

from bzrlib.plugins.gtk.diff import (
    DiffController,
    DiffView,
    iter_changes_to_status,
    MergeDirectiveController,
    )
eg_diff = """\
=== modified file 'tests/test_diff.py'
--- tests/test_diff.py	2008-03-11 13:18:28 +0000
+++ tests/test_diff.py	2008-05-08 22:44:02 +0000
@@ -20,7 +20,11 @@
 
 from bzrlib import tests
 
-from bzrlib.plugins.gtk.diff import DiffView, iter_changes_to_status
+from bzrlib.plugins.gtk.diff import (
+    DiffController,
+    DiffView,
+    iter_changes_to_status,
+    )
 
 
 class TestDiffViewSimple(tests.TestCase):
"""

class TestDiffViewSimple(tests.TestCase):

    def test_parse_colordiffrc(self):
        colordiffrc = '''\
newtext=blue
oldtext = Red
# now a comment and a blank line

diffstuff = #ffff00  
  # another comment preceded by whitespace
'''
        colors = {
                'newtext': 'blue',
                'oldtext': 'Red',
                'diffstuff': '#ffff00',
        }
        parsed_colors = DiffView.parse_colordiffrc(StringIO(colordiffrc))
        self.assertEqual(colors, parsed_colors)


class TestDiffView(tests.TestCaseWithTransport):

    def test_unicode(self):
        self.requireFeature(UnicodeFilenameFeature)

        tree = self.make_branch_and_tree('tree')
        self.build_tree([u'tree/\u03a9'])
        tree.add([u'\u03a9'], ['omega-id'])

        view = DiffView()
        view.set_trees(tree, tree.basis_tree())
        view.show_diff(None)
        buf = view.buffer
        start, end = buf.get_bounds()
        text = buf.get_text(start, end)
        self.assertContainsRe(text,
            "=== added file '\xce\xa9'\n"
            '--- .*\t1970-01-01 00:00:00 \\+0000\n'
            r'\+\+\+ .*\t\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d [+-]\d\d\d\d\n'
            '@@ -0,0 \\+1,1 @@\n'
            '\\+contents of tree/\xce\xa9\n'
            '\n'
            )


class MockDiffWidget(object):

    def set_diff_text_sections(self, sections):
        self.sections = list(sections)


class MockWindow(object):

    def __init__(self):
        self.diff = MockDiffWidget()
        self.merge_successful = False

    def set_title(self, title):
        self.title = title

    def _get_save_path(self, basename):
        return 'save-path'

    def _get_merge_target(self):
        return 'this'

    def destroy(self):
        pass

    def _merge_successful(self):
        self.merge_successful = True

    def _conflicts(self):
        self.conflicts = True

    def _handle_error(self, e):
        self.handled_error = e


class TestDiffController(tests.TestCaseWithTransport):

    def get_controller(self):
        window = MockWindow()
        return DiffController('load-path', eg_diff.splitlines(True), window)

    def test_get_diff_sections(self):
        controller = self.get_controller()
        controller = DiffController('.', eg_diff.splitlines(True),
                                    controller.window)
        sections = list(controller.get_diff_sections())
        self.assertEqual('Complete Diff', sections[0][0])
        self.assertIs(None, sections[0][1])
        self.assertEqual(eg_diff, sections[0][2])

        self.assertEqual('tests/test_diff.py', sections[1][0])
        self.assertEqual('tests/test_diff.py', sections[1][1])
        self.assertEqual(''.join(eg_diff.splitlines(True)[1:]),
                         sections[1][2])

    def test_initialize_window(self):
        controller = self.get_controller()
        controller.initialize_window(controller.window)
        self.assertEqual(2, len(controller.window.diff.sections))
        self.assertEqual('load-path - diff', controller.window.title)

    def test_perform_save(self):
        self.build_tree_contents([('load-path', 'foo')])
        controller = self.get_controller()
        controller.perform_save(None)
        self.assertFileEqual('foo', 'save-path')


class TestMergeDirectiveController(tests.TestCaseWithTransport):

    def make_this_other_directive(self):
        this = self.make_branch_and_tree('this')
        this.commit('first commit')
        other = this.bzrdir.sprout('other').open_workingtree()
        self.build_tree_contents([('other/foo', 'bar')])
        other.add('foo')
        other.commit('second commit')
        other.lock_write()
        try:
            directive = MergeDirective2.from_objects(other.branch.repository,
                                                     other.last_revision(), 0,
                                                     0, 'this')
        finally:
            other.unlock()
        return this, other, directive

    def make_merged_window(self, directive):
        window = MockWindow()
        controller = MergeDirectiveController('directive', directive, window)
        controller.perform_merge(window)
        return window

    def test_perform_merge_success(self):
        this, other, directive = self.make_this_other_directive()
        window = self.make_merged_window(directive)
        self.assertTrue(window.merge_successful)
        self.assertEqual(other.last_revision(), this.get_parent_ids()[1])
        self.assertFileEqual('bar', 'this/foo')

    def test_perform_merge_conflicts(self):
        this, other, directive = self.make_this_other_directive()
        self.build_tree_contents([('this/foo', 'bar')])
        this.add('foo')
        this.commit('message')
        window = self.make_merged_window(directive)
        self.assertFalse(window.merge_successful)
        self.assertTrue(window.conflicts)
        self.assertEqual(other.last_revision(), this.get_parent_ids()[1])
        self.assertFileEqual('bar', 'this/foo')

    def test_perform_merge_uncommitted_changes(self):
        this, other, directive = self.make_this_other_directive()
        self.build_tree_contents([('this/foo', 'bar')])
        this.add('foo')
        window = self.make_merged_window(directive)
        self.assertIsInstance(window.handled_error, errors.UncommittedChanges)


class Test_IterChangesToStatus(tests.TestCaseWithTransport):

    def assertStatusEqual(self, expected, tree):
        values = iter_changes_to_status(tree.basis_tree(), tree)
        self.assertEqual(expected, values)

    def test_status_added(self):
        tree = self.make_branch_and_tree('tree')
        self.build_tree(['tree/a', 'tree/b/', 'tree/b/c'])
        tree.add(['a', 'b', 'b/c'], ['a-id', 'b-id', 'c-id'])

        self.assertStatusEqual(
            [('a-id', 'a', 'added', 'a'),
             ('b-id', 'b', 'added', 'b/'),
             ('c-id', 'b/c', 'added', 'b/c'),
            ], tree)

    def test_status_renamed(self):
        tree = self.make_branch_and_tree('tree')
        self.build_tree(['tree/a', 'tree/b/', 'tree/b/c'])
        tree.add(['a', 'b', 'b/c'], ['a-id', 'b-id', 'c-id'])
        rev_id1 = tree.commit('one')

        tree.rename_one('b', 'd')
        tree.rename_one('a', 'd/a')

        self.assertStatusEqual(
            [('b-id', 'd', 'renamed', 'b/ => d/'),
             ('a-id', 'd/a', 'renamed', 'a => d/a'),
            ], tree)

    def test_status_modified(self):
        tree = self.make_branch_and_tree('tree')
        self.build_tree(['tree/a'])
        tree.add(['a'], ['a-id'])
        rev_id1 = tree.commit('one')

        self.build_tree_contents([('tree/a', 'new contents for a\n')])

        self.assertStatusEqual(
            [('a-id', 'a', 'modified', 'a'),
            ], tree)

    def test_status_renamed_and_modified(self):
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

        self.assertStatusEqual(
            [('b-id', 'd', 'renamed', 'b/ => d/'),
             ('a-id', 'd/a', 'renamed and modified', 'a => d/a'),
             ('c-id', 'd/c', 'modified', 'd/c'),
            ], tree)

    def test_status_kind_changed(self):
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

        self.assertStatusEqual(
            [('a-id', 'a', 'kind changed', 'a => a/'),
            # ('b-id', 'c', True, 'b => c/', 'renamed and modified'),
            ], tree)

    def test_status_removed(self):
        tree = self.make_branch_and_tree('tree')
        self.build_tree(['tree/a', 'tree/b/'])
        tree.add(['a', 'b'], ['a-id', 'b-id'])
        tree.commit('one')

        os.remove('tree/a')
        tree.remove('b', force=True)

        self.assertStatusEqual(
            [('a-id', 'a', 'removed', 'a'),
             ('b-id', 'b', 'removed', 'b/'),
            ], tree)

    def test_status_missing_file(self):
        this = self.make_branch_and_tree('this')
        self.build_tree(['this/foo'])
        this.add(['foo'], ['foo-id'])
        this.commit('add')

        other = this.bzrdir.sprout('other').open_workingtree()

        os.remove('this/foo')
        this.remove('foo', force=True)
        this.commit('remove')

        f = open('other/foo', 'wt')
        try:
            f.write('Modified\n')
        finally:
            f.close()
        other.commit('modified')

        this.merge_from_branch(other.branch)
        conflicts.resolve(this)

        self.assertStatusEqual(
            [('foo-id', 'foo.OTHER', 'missing', 'foo.OTHER'),],
            this)

    def test_status_missing_directory(self):
        this = self.make_branch_and_tree('this')
        self.build_tree(['this/foo/', 'this/foo/bar'])
        this.add(['foo', 'foo/bar'], ['foo-id', 'bar-id'])
        this.commit('add')

        other = this.bzrdir.sprout('other').open_workingtree()

        os.remove('this/foo/bar')
        os.rmdir('this/foo')
        this.remove('foo', force=True)
        this.commit('remove')

        f = open('other/foo/bar', 'wt')
        try:
            f.write('Modified\n')
        finally:
            f.close()
        other.commit('modified')

        this.merge_from_branch(other.branch)
        conflicts.resolve(this)

        self.assertStatusEqual(
            [('foo-id', u'foo', 'added', u'foo/'),
             ('bar-id', u'foo/bar.OTHER', 'missing', u'foo/bar.OTHER'),],
            this)
