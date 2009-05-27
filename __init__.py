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
ginfo             GTK+ branch info dialog
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

import bzrlib
import bzrlib.api
from bzrlib import (
    config,
    errors,
    )
from bzrlib.commands import plugin_cmds

import os.path

version_info = (0, 96, 0, 'dev', 1)

if version_info[3] == 'final':
    version_string = '%d.%d.%d' % version_info[:3]
else:
    version_string = '%d.%d.%d%s%d' % version_info
__version__ = version_string

COMPATIBLE_BZR_VERSIONS = [(1, 6, 0), (1, 7, 0), (1, 8, 0), (1, 9, 0),
                           (1, 10, 0), (1, 11, 0), (1, 12, 0), (1, 13, 0),
                           (1, 15, 0),]

bzrlib.api.require_any_api(bzrlib, COMPATIBLE_BZR_VERSIONS)

if __name__ != 'bzrlib.plugins.gtk':
    from bzrlib.trace import warning
    warning("Not running as bzrlib.plugins.gtk, things may break.")

def import_pygtk():
    try:
        import pygtk
    except ImportError:
        raise errors.BzrCommandError("PyGTK not installed.")
    pygtk.require('2.0')
    return pygtk


def set_ui_factory():
    import_pygtk()
    from ui import GtkUIFactory
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


def open_display():
    pygtk = import_pygtk()
    try:
        import gtk
    except RuntimeError, e:
        if str(e) == "could not open display":
            raise NoDisplayError
    set_ui_factory()
    return gtk


commands = {
    "gannotate": ["gblame", "gpraise"],
    "gbranch": [],
    "gcheckout": [],
    "gcommit": ["gci"],
    "gconflicts": [],
    "gdiff": [],
    "ginit": [],
    "ginfo": [],
    "gmerge": [],
    "gmissing": [],
    "gpreferences": [],
    "gpush": [],
    "gselftest": [],
    "gsend": [],
    "gstatus": ["gst"],
    "gtags": [],
    "visualise": ["visualize", "vis", "viz"],
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


import gettext
gettext.install('olive-gtk')

# Let's create a specialized alias to protect '_' from being erased by other
# uses of '_' as an anonymous variable (think pdb for one).
_i18n = gettext.gettext

class NoDisplayError(errors.BzrCommandError):
    """gtk could not find a proper display"""

    def __str__(self):
        return "No DISPLAY. Unable to run GTK+ application."


credential_store_registry = getattr(config, "credential_store_registry", None)
if credential_store_registry is not None:
    try:
        credential_store_registry.register_lazy(
            "gnome-keyring", "bzrlib.plugins.gtk.keyring", "GnomeKeyringCredentialStore",
            help="The GNOME Keyring.", fallback=True)
    except TypeError:
    # Fallback credentials stores were introduced in Bazaar 1.15
        credential_store_registry.register_lazy(
            "gnome-keyring", "bzrlib.plugins.gtk.keyring", "GnomeKeyringCredentialStore",
            help="The GNOME Keyring.")


def load_tests(basic_tests, module, loader):
    testmod_names = [
        'tests',
        ]
    import sys
    default_encoding = sys.getdefaultencoding()
    try:
        result = basic_tests
        try:
            import_pygtk()
        except errors.BzrCommandError:
            return basic_tests
        basic_tests.addTest(loader.loadTestsFromModuleNames(
                ["%s.%s" % (__name__, tmn) for tmn in testmod_names]))
    finally:
        if sys.getdefaultencoding() != default_encoding:
            reload(sys)
            sys.setdefaultencoding(default_encoding)
    return basic_tests
