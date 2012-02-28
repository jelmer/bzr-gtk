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

__all__ = [
    'load_tests',
    'MockMethod',
    'MockProperty',
    ]

import os


def load_tests(basic_tests, module, loader):
    if module == 'discover':
        here = os.path.abspath(os.path.dirname(__file__))
        basic_tests.addTest(loader.discover(here))
    else:
        full_name = "%s.%s" % (__name__, module)
        basic_tests.addTest(loader.loadTestsFromModuleNames([full_name]))
    return basic_tests


class MockMethod(object):

    @classmethod
    def bind(klass, test_instance, obj, method_name, return_value=None):
        original_method = getattr(obj, method_name)
        test_instance.addCleanup(setattr, obj, method_name, original_method)
        setattr(obj, method_name, klass(return_value))

    def __init__(self, return_value=None):
        self.called = False
        self.call_count = 0
        self.args = None
        self.kwargs = None
        self.return_value = return_value

    def __call__(self, *args, **kwargs):
        self.called = True
        self.call_count += 1
        self.args = args
        self.kwargs = kwargs
        return self.return_value


class MockProperty(MockMethod):

    @classmethod
    def bind(klass, test_instance, obj, method_name, return_value=None):
        original_method = getattr(obj, method_name)
        test_instance.addCleanup(setattr, obj, method_name, original_method)
        mock = klass(return_value)
        setattr(obj, method_name, property(mock.get_value, mock.set_value))
        return mock

    def get_value(self, other):
        self.called = True
        return self.return_value

    def set_value(self, other, value):
        self.called = True
        self.return_value = value
