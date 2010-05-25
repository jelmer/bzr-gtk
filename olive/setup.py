#!/usr/bin/python

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
        import subprocess
        self.data_files.extend(self._compile_po_files())
        install_data.run(self)
        try:
            subprocess.check_call('gtk-update-icon-cache '
                                  '-f -t /usr/share/icons/hicolor')
        except OSError:
            pass

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
                dest = os.path.dirname(
                    os.path.join('share', 'locale', lang,
                                 'LC_MESSAGES', 'olive-gtk.mo'))
                data_files.append((dest, [mo]))
        return data_files


if __name__ == '__main__':
    setup(
        name = "olive-gtk",
        version = "0.99.0",
        description = "GTK+ Explorer for Bazaar",
        license = "GNU GPL v2 or later",
        scripts = ['olive-gtk'],
        url = "http://bazaar-vcs.org/Olive",
        packages = [
            "olive",
        ],
        data_files=[('share/olive', ['cmenu.ui',]),
                    ('share/applications', ['olive-gtk.desktop', ]),
                    ('share/pixmaps', ['icons/olive-gtk.png']),
                    ],
        cmdclass={'install_data': InstallData}
        )
