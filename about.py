# Copyright (C) 2007 by Jelmer Vernooij <jelmer@samba.org>
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

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

import gtk
import bzrlib

class AboutDialog(gtk.AboutDialog):
    def __init__(self):
        super(AboutDialog, self).__init__()
        self.set_name("Bazaar")
        self.set_version(bzrlib.version_string)
        self.set_website("http://bazaar-vcs.org/")
        self.set_license("GNU GPLv2")
        self.set_icon(gtk.gdk.pixbuf_new_from_file("bzr-icon-64.png"))
        self.connect ("response", lambda d, r: d.destroy())
