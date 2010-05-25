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

"""cmenu.ui path"""

import os
import sys

from bzrlib.plugins.gtk import _i18n

UIFILENAMES = ["/usr/share/olive/cmenu.ui",
                  "/usr/local/share/olive/cmenu.ui",
                  "/opt/share/olive/cmenu.ui",
                  "/opt/local/share/olive/cmenu.ui",
                  "~/share/olive/cmenu.ui",
                 ]

# Get the glade file name
if sys.platform == 'win32':
    UIFILENAMES = [os.path.join(os.path.dirname(sys.executable),
                                   "share/olive/cmenu.ui")]

dir_ = os.path.split(os.path.dirname(__file__))[0]
# Check first if we are running from source
UIFILENAMES.insert(0, os.path.join(dir_, "cmenu.ui"))

UIFILENAME = None

for path in UIFILENAMES:
    path = os.path.expanduser(path)
    if os.path.isfile(path):
        UIFILENAME = path
        break

if UIFILENAME is None:
    # Fail
    print _i18n('Context menu file (cmenu.ui) cannot be found.')
    sys.exit(1)
