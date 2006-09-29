#!/usr/bin/env python2.4
"""GTK+ Frontends for various Bazaar commands."""

from distutils.core import setup

setup(
    name = "gtk",
    version = "0.11.0",
    maintainer = "Jelmer Vernooij",
    maintainer_email = "jelmer@samba.org",
    description = "GTK+ Frontends for various Bazaar commands",
    license = "GNU GPL v2",
    package_dir = {
        "bzrlib.plugins.gtk": ".",
        "bzrlib.plugins.gtk.viz": "viz", 
        "bzrlib.plugins.gtk.annotate": "annotate"
        },
    packages = [
        "bzrlib.plugins.gtk",
        "bzrlib.plugins.gtk.viz",
        "bzrlib.plugins.gtk.annotate"
        ],
)
