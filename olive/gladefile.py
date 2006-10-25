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

"""Glade file name"""

import os
import sys


# Get the glade file name
if sys.platform == 'win32':
    GLADEFILENAME = os.path.join(os.path.dirname(sys.executable),
                                 "share/olive/olive.glade")
else:
    GLADEFILENAME = "/usr/share/olive/olive.glade"

if not os.path.isfile(GLADEFILENAME):
    # Load from sources directory if not installed
    dir_ = os.path.split(os.path.dirname(__file__))[0]
    GLADEFILENAME = os.path.join(dir_, "olive.glade")
    # Check again
    if not os.path.isfile(GLADEFILENAME):
        # Fail
        print _('Glade file cannot be found.')
        sys.exit(1)
