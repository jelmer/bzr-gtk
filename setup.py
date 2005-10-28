#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""GTK+ Branch Visualisation plugin for bzr."""

__copyright__ = "Copyright © 2005 Canonical Ltd."
__author__    = "Scott James Remnant <scott@ubuntu.com>"


from distutils.core import setup


setup(name="bzrk",
      version="0.2",
      description="GTK+ Branch Visualisation plugin for bzr",
      author="Scott James Remnant",
      author_email="scott@ubuntu.com",
      license="GNU GPL v2",

      package_dir = { "bzrlib.plugins.bzrk": "." },
      packages = [ "bzrlib.plugins.bzrk" ],
      )
