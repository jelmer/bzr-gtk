#!/usr/bin/env python
# API Info for bzr-gtk

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

bzr_plugin_name = "gtk"

# versions ending in 'exp' mean experimental mappings
# versions ending in 'dev' mean development version
# versions ending in 'final' mean release (well tested, etc)
bzr_plugin_version = (0, 99, 1, 'final', 0)

#FIXME: fill this in automatically somehow
bzr_commands = []

bzr_compatible_versions = [(1, 6, 0), (1, 7, 0), (1, 8, 0), (1, 9, 0),
                           (1, 10, 0), (1, 11, 0), (1, 12, 0), (1, 13, 0),
                           (1, 15, 0),
                           (1, 17, 0),
                           (2, 1, 0),
                           (2, 2, 0),
                           (2, 3, 0),
                           ]

bzr_minimum_version = bzr_compatible_versions[0]

bzr_maximum_version = bzr_compatible_versions[-1]