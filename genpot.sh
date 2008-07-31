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

if [ "$1" = "" ]; then
    POT=po/olive-gtk.pot
else
    # Used for debugging
    POT=$1 
fi

XGETTEXT="xgettext -o $POT"
PY_XGETTEXT="$XGETTEXT -L python --from-code=ASCII --keyword=_i18n"

if [ -x $POT ]; then
    rm $POT
    touch $POT
else
    touch $POT
fi
$PY_XGETTEXT olive-gtk
$XGETTEXT -j olive.glade

for d in . annotate branchview olive preferences viz ;
do
   $PY_XGETTEXT -j $d/*.py
done
