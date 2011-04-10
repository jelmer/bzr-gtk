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

from gettext import (
    gettext,
    textdomain,
    bindtextdomain,
    bind_textdomain_codeset,
    )

# FIXME: We should find out LOCALEDIR at compile or run time. The current
# hardcoded path will work for most distributions, but not for e.g.
# Solaris and
# Windows
GETTEXT_PACKAGE = 'bzr-gtk'
LOCALEDIR = '/usr/share/locale'

bindtextdomain(GETTEXT_PACKAGE, LOCALEDIR)
bind_textdomain_codeset(GETTEXT_PACKAGE, 'UTF-8')
textdomain(GETTEXT_PACKAGE)

def _i18n(text):
    return gettext(text)
