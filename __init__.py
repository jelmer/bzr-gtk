# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""Graphical support for Bazaar using GTK.

This plugin includes:
gannotate         GTK+ annotate.
gbranch           GTK+ branching.
gcheckout         GTK+ checkout.
gcommit           GTK+ commit dialog.
gconflicts        GTK+ conflicts.
gdiff             Show differences in working tree in a GTK+ Window.
ginit             Initialise a new branch.
gloom             GTK+ loom browse dialog
gmerge            GTK+ merge dialog
gmissing          GTK+ missing revisions dialog.
gpreferences      GTK+ preferences dialog.
gpush             GTK+ push.
gsend             GTK+ send merge directive.
gstatus           GTK+ status dialog.
gtags             Manage branch tags.
visualise         Graphically visualise this branch.
"""

from __future__ import absolute_import

import os
import sys

if getattr(sys, "frozen", None) is not None: # we run bzr.exe

    # FIXME: Unless a better packaging solution is found, the following
    # provides a workaround for https://bugs.launchpad.net/bzr/+bug/388790 Also
    # see https://code.edge.launchpad.net/~vila/bzr-gtk/388790-windows-setup
    # for more details about while it's needed.

    # NOTE: _lib must be ahead of bzrlib or sax.saxutils (in olive) fails
    here = os.path.dirname(__file__)
    sys.path.insert(0, os.path.join(here, '_lib'))
    sys.path.append(os.path.join(here, '_lib/gtk-2.0'))


import bzrlib
import bzrlib.api
from bzrlib.commands import plugin_cmds

from bzrlib.plugins.gtk.info import (
    bzr_plugin_version as version_info,
    bzr_compatible_versions,
    )

if version_info[3] == 'final':
    version_string = '%d.%d.%d' % version_info[:3]
else:
    version_string = '%d.%d.%d%s%d' % version_info
__version__ = version_string

bzrlib.api.require_any_api(bzrlib, bzr_compatible_versions)

if __name__ != 'bzrlib.plugins.gtk':
    from bzrlib.trace import warning
    warning("Not running as bzrlib.plugins.gtk, things may break.")


def set_ui_factory():
    from bzrlib.plugins.gtk.ui import GtkUIFactory
    import bzrlib.ui
    bzrlib.ui.ui_factory = GtkUIFactory()


def data_basedirs():
    return [os.path.dirname(__file__),
             "/usr/share/bzr-gtk", 
             "/usr/local/share/bzr-gtk"]


def data_path(*args):
    for basedir in data_basedirs():
        path = os.path.join(basedir, *args)
        if os.path.exists(path):
            return path
    return None


def icon_path(*args):
    return data_path(os.path.join('icons', *args))


commands = {
    "gannotate": ["gblame", "gpraise"],
    "gbranch": [],
    "gcheckout": [],
    "gcommit": ["gci"],
    "gconflicts": [],
    "gdiff": [],
    "ginit": [],
    "gmerge": [],
    "gmissing": [],
    "gpreferences": [],
    "gpush": [],
    "gsend": [],
    "gstatus": ["gst"],
    "gtags": [],
    "visualise": ["visualize", "vis", "viz", 'glog'],
    }

try:
    from bzrlib.plugins import loom
except ImportError:
    pass # Loom plugin doesn't appear to be present
else:
    commands["gloom"] = []

for cmd, aliases in commands.iteritems():
    plugin_cmds.register_lazy("cmd_%s" % cmd, aliases,
                              "bzrlib.plugins.gtk.commands")

def save_commit_messages(*args):
    from bzrlib.plugins.gtk import commitmsgs
    commitmsgs.save_commit_messages(*args)

try:
    from bzrlib.hooks import install_lazy_named_hook
except ImportError:
    from bzrlib.branch import Branch
    Branch.hooks.install_named_hook('post_uncommit',
                                    save_commit_messages,
                                    "Saving commit messages for gcommit")
else:
    install_lazy_named_hook("bzrlib.branch", "Branch.hooks",
        'post_uncommit', save_commit_messages, "Saving commit messages for gcommit")

try:
    from bzrlib.registry import register_lazy
except ImportError:
    from bzrlib import config
    option_registry = getattr(config, "option_registry", None)
    if option_registry is not None:
        config.option_registry.register_lazy('nautilus_integration',
                'bzrlib.plugins.gtk.config', 'opt_nautilus_integration')
else:
    register_lazy("bzrlib.config", "option_registry",
        'nautilus_integration', 'bzrlib.plugins.gtk.config',
        'opt_nautilus_integration')


def load_tests(basic_tests, module, loader):
    testmod_names = [
        'tests',
        ]
    import sys
    default_encoding = sys.getdefaultencoding()
    try:
        result = basic_tests
        try:
            import gi.repository.Gtk
        except ImportError:
            return basic_tests
        basic_tests.addTest(loader.loadTestsFromModuleNames(
                ["%s.%s" % (__name__, tmn) for tmn in testmod_names]))
    finally:
        if sys.getdefaultencoding() != default_encoding:
            reload(sys)
            sys.setdefaultencoding(default_encoding)
    return basic_tests

