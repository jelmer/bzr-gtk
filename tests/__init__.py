# Copyright (C) 2007, 2008 Jelmer Vernooij <jelmer@samba.org>
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


def load_tests(basic_tests, module, loader):
    testmod_names = [
        'test_annotate_config',
        'test_avatarsbox',
        'test_commit',
        'test_diff',
        'test_history',
        'test_graphcell',
        'test_linegraph',
        'test_revisionview',
        'test_treemodel',
        ]

    basic_tests.addTest(loader.loadTestsFromModuleNames(
            ["%s.%s" % (__name__, tmn) for tmn in testmod_names]))
    return basic_tests


class MockMethod():

    @classmethod
    def bind(klass, test_instance, obj, method_name):
        original_method = getattr(obj, method_name)
        test_instance.addCleanup(setattr, obj, method_name, original_method)
        setattr(obj, method_name, klass())

    def __init__(self):
        self.called = False
        self.args = None
        self.kwargs = None

    def __call__(self, *args, **kwargs):
        self.called = True
        self.args = args
        self.kwargs = kwargs
