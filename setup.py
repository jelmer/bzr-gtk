#!/usr/bin/env python2.4
"""GTK+ Frontends for various Bazaar commands."""

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



setup(
    name = "bzr-gtk",
    version = "0.14.0",
    maintainer = "Jelmer Vernooij",
    maintainer_email = "jelmer@samba.org",
    description = "GTK+ Frontends for various Bazaar commands",
    license = "GNU GPL v2",
    scripts=['olive-gtk'],
    package_dir = {
        "bzrlib.plugins.gtk": ".",
        "bzrlib.plugins.gtk.viz": "viz", 
        "bzrlib.plugins.gtk.annotate": "annotate",
        "bzrlib.plugins.gtk.olive": "olive"
        },
    packages = [
		"olive",
        "bzrlib.plugins.gtk",
        "bzrlib.plugins.gtk.viz",
        "bzrlib.plugins.gtk.annotate",
        "bzrlib.plugins.gtk.olive"
        ],
      data_files=[('share/olive', ['olive.glade',
                                   'oliveicon2.png',
                                   'cmenu.ui',
                                  ]),
                  ('share/olive/icons', [\
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
	cmdclass={'install_data': InstallData}
)
