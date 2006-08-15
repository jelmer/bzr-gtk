#!/usr/bin/env python

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

from distutils.core import setup

setup(name='Olive',
      version='0.1',
      description='Olive - Graphical frontend for Bazaar-NG',
      author='Szilveszter Farkas (Phanatic)',
      author_email='szilveszter.farkas@gmail.com',
      url='https://launchpad.net/products/olive/',
      packages=['olive', 'olive.backend', 'olive.frontend',
                'olive.frontend.gtk', 'olive.frontend.gtk.viz'],
      scripts=['olive-gtk'],
      data_files=[('share/olive', ['olive.glade',
                                   'oliveicon2.png',
                                   'cmenu.ui',
                                   'icons/commit.png',
                                   'icons/commit16.png',
                                   'icons/diff.png',
                                   'icons/diff16.png',
                                   'icons/log.png',
                                   'icons/log16.png',
                                   'icons/pull.png',
                                   'icons/pull16.png',
                                   'icons/push.png',
                                   'icons/push16.png',
                                   'icons/refresh.png']),
                  ('share/applications', ['olive-gtk.desktop'])
                 ]
     )
