#!/usr/bin/python

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
from distutils.command.install_data import install_data
from distutils.dep_util import newer
from distutils.log import info
import glob
import os
import sys

class InstallData(install_data):
	def run(self):
		self.data_files.extend(self._compile_po_files())
		install_data.run(self)

	def _compile_po_files(self):
		data_files = []
		
		# Don't install language files on Win32
		if sys.platform == 'win32':
		    return data_files
		
		PO_DIR = 'po'
		for po in glob.glob(os.path.join(PO_DIR,'*.po')):
			lang = os.path.basename(po[:-3])
			# It's necessary to compile in this directory (not in po_dir)
			# because install_data can't rename file
			mo = os.path.join('build', 'mo', lang, 'olive-gtk.mo')
			
			directory = os.path.dirname(mo)
			if not os.path.exists(directory):
				info('creating %s' % directory)
				os.makedirs(directory)
			
			if newer(po, mo):
				# True if mo doesn't exist
				cmd = 'msgfmt -o %s %s' % (mo, po)
				info('compiling %s -> %s' % (po, mo))
				if os.system(cmd) != 0:
					raise SystemExit('Error while running msgfmt')

				dest = os.path.dirname(os.path.join('share', 'locale', lang, 'LC_MESSAGES', 'olive-gtk.mo'))
				data_files.append((dest, [mo]))
		
		return data_files

setup(name='Olive',
      version='0.11.0',
      description='Olive - Graphical frontend for Bazaar',
      author='Szilveszter Farkas (Phanatic)',
      author_email='szilveszter.farkas@gmail.com',
      url='http://bazaar-vcs.org/Olive',
      packages=['olive'],
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
                  ('share/applications', ['olive-gtk.desktop']),
                  ('share/pixmaps', ['icons/olive-gtk.png'])
                 ],
	cmdclass={'install_data': InstallData
			}
	)
