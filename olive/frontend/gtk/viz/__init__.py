# Modified for use with Olive:
# Copyright (C) 2006 by Szilveszter Farkas (Phanatic) <szilveszter.farkas@gmail.com>
# Original copyright holder:
# Copyright (C) 2005 by Canonical Ltd. (Scott James Remnant <scott@ubuntu.com>)
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

"""GTK+ Branch Visualisation.

This is a bzr plugin that adds a new 'visualise' (alias: 'viz') command
which opens a GTK+ window to allow you to see the history of the branch
and relationships between revisions in a visual manner.

It's somewhat based on a screenshot I was handed of gitk.  The top half
of the window shows the revisions in a list with a graph drawn down the
left hand side that joins them up and shows how they relate to each other.
The bottom hald of the window shows the details for the selected revision.
"""

__copyright__ = "Copyright © 2005 Canonical Ltd."
__author__    = "Scott James Remnant <scott@ubuntu.com>"

