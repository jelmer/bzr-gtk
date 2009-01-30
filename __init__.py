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
from bzrlib import errors
from bzrlib.commands import plugin_cmds

import os.path

version_info = (0, 96, 0, 'dev', 1)

if version_info[3] == 'final':
    version_string = '%d.%d.%d' % version_info[:3]
else:
    version_string = '%d.%d.%d%s%d' % version_info
__version__ = version_string

required_bzrlib = (1, 6)

def check_bzrlib_version(desired):
    """Check that bzrlib is compatible.

    If version is < bzr-gtk version, assume incompatible.
    """
    bzrlib_version = bzrlib.version_info[:2]
    if bzrlib_version < desired:
        from bzrlib.trace import warning
        from bzrlib.errors import BzrError
        warning('Installed Bazaar version %s is too old to be used with bzr-gtk'
                ' %s.' % (bzrlib.__version__, __version__))
        raise BzrError('Version mismatch: %r, %r' % (version_info, bzrlib.version_info) )


if version_info[2] == "final":
    check_bzrlib_version(required_bzrlib)

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
    plugin_cmds.register_lazy("cmd_%s" % cmd, aliases, "bzrlib.plugins.gtk.commands")


import gettext
gettext.install('olive-gtk')

# Let's create a specialized alias to protect '_' from being erased by other
# uses of '_' as an anonymous variable (think pdb for one).
_i18n = gettext.gettext

class NoDisplayError(errors.BzrCommandError):
    """gtk could not find a proper display"""

    def __str__(self):
        return "No DISPLAY. Unable to run GTK+ application."


def test_suite():
    from unittest import TestSuite
    import tests
    import sys
    default_encoding = sys.getdefaultencoding()
    try:
        result = TestSuite()
        try:
            import_pygtk()
        except errors.BzrCommandError:
            return result
        result.addTest(tests.test_suite())
    finally:
        if sys.getdefaultencoding() != default_encoding:
            reload(sys)
            sys.setdefaultencoding(default_encoding)
    return result
