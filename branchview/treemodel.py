# -*- coding: UTF-8 -*-
"""BranchTreeModel."""

__copyright__ = "Copyright © 2005 Canonical Ltd."
__author__ = "Gary van der Merwe <garyvdm@gmail.com>"


from gi.repository import Gtk
from gi.repository import GObject
from xml.sax.saxutils import escape

from bzrlib.config import parse_username
from bzrlib.revision import NULL_REVISION

from time import (
    strftime,
    localtime,
    )


REVID = 0
NODE = 1
LINES = 2
LAST_LINES = 3
REVNO = 4
SUMMARY = 5
MESSAGE = 6
COMMITTER = 7
TIMESTAMP = 8
REVISION = 9
PARENTS = 10
CHILDREN = 11
TAGS = 12
AUTHORS = 13


class BranchTreeModel(Gtk.ListStore):
    """A model of branch's merge history."""

    def __init__(self, branch, line_graph_data):
        super(BranchTreeModel, self).__init__(
            GObject.TYPE_STRING,
            GObject.TYPE_PYOBJECT,
            GObject.TYPE_PYOBJECT,
            GObject.TYPE_PYOBJECT,
            GObject.TYPE_STRING,
            GObject.TYPE_STRING,
            GObject.TYPE_STRING,
            GObject.TYPE_STRING,
            GObject.TYPE_STRING,
            GObject.TYPE_PYOBJECT,
            GObject.TYPE_PYOBJECT,
            GObject.TYPE_PYOBJECT,
            GObject.TYPE_PYOBJECT,
            GObject.TYPE_STRING)
        self.revisions = {}
        self.branch = branch
        self.repository = branch.repository
        if self.branch.supports_tags():
            self.tags = self.branch.tags.get_reverse_tag_dict()
        else:
            self.tags = {}
        self.set_line_graph_data(line_graph_data)

    def add_tag(self, tag, revid):
        self.branch.tags.set_tag(tag, revid)
        try:
            self.tags[revid].append(tag)
        except KeyError:
            self.tags[revid] = [tag]

    def _line_graph_item_to_model_row(self, rowref, data):
        revid, node, lines, parents, children, revno_sequence = data
        if rowref > 0:
            last_lines = self.line_graph_data[rowref - 1][2]
        else:
            last_lines = []
        revno = ".".join(["%d" % (revno) for revno in revno_sequence])
        tags = self.tags.get(revid, [])
        if not revid or revid == NULL_REVISION:
            revision = None
        elif revid not in self.revisions:
            revision = self.repository.get_revisions([revid])[0]
            self.revisions[revid] = revision
        else:
            revision = self.revisions[revid]
        if revision is None:
            summary = message = committer = timestamp = authors = None
        else:
            summary = escape(revision.get_summary())
            message = escape(revision.message)
            committer = parse_username(revision.committer)[0]
            timestamp = strftime(
                "%Y-%m-%d %H:%M", localtime(revision.timestamp))
            authors = ", ".join([
                parse_username(author)[0]
                for author in revision.get_apparent_authors()])
        return (revid, node, lines, last_lines, revno, summary, message,
                committer, timestamp, revision, parents, children, tags,
                authors)

    def set_line_graph_data(self, line_graph_data):
        self.clear()
        self.line_graph_data = line_graph_data
        for rowref, data in enumerate(self.line_graph_data):
            row = self._line_graph_item_to_model_row(rowref, data)
            self.append(row)
