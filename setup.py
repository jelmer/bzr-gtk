#!/usr/bin/env python

from distutils.core import setup

setup(
    name = "gannotate",
    version = "0.6",
    description = "GTK+ annotate plugin for bzr",
    author = "Dan Loda",
    author_email = "danloda@gmail.com",
    license = "GNU GPL v2",
    package_dir = {"bzrlib.plugins.gannotate": "."},
    packages = ["bzrlib.plugins.gannotate"],
)

