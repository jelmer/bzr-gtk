#!/bin/sh

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

# Generate translation template

if [ -x po/olive-gtk.pot ]; then
    rm po/olive-gtk.pot
    touch po/olive-gtk.pot
else
    touch po/olive-gtk.pot
fi
xgettext -L python -o po/olive-gtk.pot olive-gtk
xgettext -j -o po/olive-gtk.pot olive.glade
xgettext -j -o po/olive-gtk.pot *.py
cd olive/
xgettext -j -o ../po/olive-gtk.pot *.py
#cd viz
#xgettext -j -o ../../../../po/olive-gtk.pot *.py
