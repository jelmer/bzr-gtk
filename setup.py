#!/usr/bin/env python2.4
"""GTK+ Frontends for various Bazaar commands."""

from distutils.core import setup

setup(
    name = "gtk",
    version = "0.8.2",
    description = "GTK+ Frontends for various Bazaar commands",
    license = "GNU GPL v2",
    package_dir = {"bzrlib.plugins.gtk": ".","bzrlib.plugins.gtk.viz": "viz", "bzrlib.plugins.gtk.annotate": "annotate"},
    packages = ["bzrlib.plugins.gtk","bzrlib.plugins.gtk.viz","bzrlib.plugins.gtk.annotate"],
)
