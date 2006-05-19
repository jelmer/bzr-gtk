#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""GTK+ Branch Visualisation.

This is a bzr plugin that adds a new 'visualise' (alias: 'viz') command
which opens a GTK+ window to allow you to see the history of the branch
and relationships between revisions in a visual manner.

It's somewhat based on a screenshot I was handed of gitk.  The top half
of the window shows the revisions in a list with a graph drawn down the
left hand side that joins them up and shows how they relate to each other.
The bottom hald of the window shows the details for the selected revision.
"""

__copyright__ = "Copyright © 2005 Canonical Ltd."
__author__    = "Scott James Remnant <scott@ubuntu.com>"


from bzrlib.commands import Command, register_command
from bzrlib.option import Option
from bzrlib.branch import Branch


class cmd_visualise(Command):
    """Graphically visualise this branch.

    Opens a graphical window to allow you to see the history of the branch
    and relationships between revisions in a visual manner,

    The default starting point is latest revision on the branch, you can
    specify a starting point with -r revision.
    """
    takes_options = [
        "revision",
        Option('limit', "maximum number of revisions to display",
               int, 'count')]
    takes_args = [ "location?" ]
    aliases = [ "visualize", "vis", "viz" ]

    def run(self, location=".", revision=None, limit=None):
        (branch, path) = Branch.open_containing(location)
        branch.lock_read()
        branch.repository.lock_read()
        try:
            if revision is None:
                revid = branch.last_revision()
                if revid is None:
                    return
            else:
                (revno, revid) = revision[0].in_history(branch)

            from bzrkapp import BzrkApp
                
            app = BzrkApp()
            app.show(branch, revid, limit)
        finally:
            branch.repository.unlock()
            branch.unlock()
        app.main()


register_command(cmd_visualise)
