# Copyright (C) 2006 by Szilveszter Farkas (Phanatic) <szilveszter.farkas@gmail.com>
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

import sys
import os

def launch(path):
    """ Launch program associated with path """

    # Normalize filepath
    normpath = os.path.normpath(path) 
    
    if sys.platform == 'win32':
        # Windows is easy
        os.startfile(normpath)
    else:
        # Maybe Gnome?
        exe = search_exe('gnome-open')
        if exe != None:
            os.system("gnome-open %s" % normpath)
            return
        # Maybe KDE?
        exe = search_exe('kfmclient')
        if exe != None:
            os.system("kfmclient exec file:%s" % normpath)
            return

        # TODO: support other platforms
        print "DEBUG: file launch not supported on this platform."

def search_exe(exe):
    """ Search for given executable. """
    found = 0
    paths = os.environ['PATH'].split(os.pathsep)
    for path in paths:
        if os.path.exists(os.path.join(path,exe)):
            found = 1
            break
    if found:
        return True
    return None
