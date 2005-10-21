#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""Directed graph production.

This module contains the code to produce an ordered directed graph of a
bzr branch, such as we display in the tree view at the top of the bzrk
window.
"""

__copyright__ = "Copyright © 2005 Canonical Ltd."
__author__    = "Scott James Remnant <scott@ubuntu.com>"


from bzrlib.errors import NoSuchRevision


class DummyRevision(object):
    """Dummy bzr revision.

    Sometimes, especially in older bzr branches, a revision is referenced
    as the parent of another but not actually present in the branch's store.
    When this happens we use an instance of this class instead of the real
    Revision object (which we can't get).
    """

    def __init__(self, revid):
        self.revision_id = revid
        self.parent_ids = []
        self.committer = None
        self.message = self.revision_id


def distances(branch, start):
    """Sort the revisions.

    Traverses the branch revision tree starting at start and produces an
    ordered list of revisions such that a revision always comes after
    any revision it is the parent of.

    Returns a tuple of (revids, revisions, colours, children)
    """
    revisions = { start: branch.get_revision(start) }
    children = { revisions[start]: set() }
    distances = { start: 0 }
    colours = { start: 0 }
    last_colour = 0

    # Sort the revisions; the fastest way to do this is to visit each node
    # as few times as possible (by keeping the todo list in a set) and record
    # the largest distance to it before queuing up the children if we
    # increased the distance.  This produces the sort order we desire
    todo = set([ start ])
    while todo:
        revid = todo.pop()
        revision = revisions[revid]
        distance = distances[revid] + 1
        colour = colours[revid]

        found_same = False
        for parent_id in revision.parent_ids:
            # Check whether there's any point re-processing this
            if parent_id in distances and distances[parent_id] >= distance:
                continue

            # Get the parent from the cache, or put it in the cache
            try:
                parent = revisions[parent_id]
                children[parent].add(revision)
            except KeyError:
                try:
                    parent = revisions[parent_id] \
                             = branch.get_revision(parent_id)
                except NoSuchRevision:
                    parent = revisions[parent_id] = DummyRevision(parent_id)

                children[parent] = set([ revision ])

            # Penalise revisions a little at a fork if we think they're on
            # the same branch -- this makes the few few (at least) revisions
            # of a branch appear straight after the fork
            if not found_same and same_branch(revision, parent):
                found_same = True
                colours[parent_id] = colour
                if len(revision.parent_ids) > 1:
                    distances[parent_id] = distance + 10
                else:
                    distances[parent_id] = distance
            else:
                colours[parent_id] = last_colour = last_colour + 1
                distances[parent_id] = distance

            todo.add(parent_id)

    return ( sorted(distances, key=distances.get), revisions, colours,
             children )

def graph(revids, revisions, colours):
    """Produce a directed graph of a bzr branch.

    For each revision it then yields a tuple of (revision, node, lines).
    If the revision is only referenced in the branch and not present in the
    store, revision will be a DummyRevision object, otherwise it is the bzr
    Revision object with the meta-data for the revision.

    Node is a tuple of (column, colour) with column being a zero-indexed
    column number of the graph that this revision represents and colour
    being a zero-indexed colour (which doesn't specify any actual colour
    in particular) to draw the node in.

    Lines is a list of tuples which represent lines you should draw away
    from the revision, if you also need to draw lines into the revision
    you should use the lines list from the previous iteration.  Each
    typle in the list is in the form (start, end, colour) with start and
    end being zero-indexed column numbers and colour as in node.

    It's up to you how to actually draw the nodes and lines (straight,
    curved, kinked, etc.) and to pick the actual colours for each index.
    """
    hanging = revids[:1]
    for revid in revids:
        lines = []
        node = None

        new_hanging = []
        for h_idx, hang in enumerate(hanging):
            if hang == revid:
                # We've matched a hanging revision, so need to output a node
                # at this point
                node = (h_idx, colours[revid])

                # Now we need to hang its parents, we put them at the point
                # the old column was so anything to the right of this has
                # to move outwards to make room.  We also try and collapse
                # hangs to keep the graph small.
                for parent_id in revisions[revid].parent_ids:
                    try:
                        n_idx = new_hanging.index(parent_id)
                    except ValueError:
                        n_idx = len(new_hanging)
                        new_hanging.append(parent_id)
                    lines.append((h_idx, n_idx, colours[parent_id]))
            else:
                # Revision keeps on hanging, adjust for any change in the
                # graph shape and try to collapse hangs to keep the graph
                # small.
                try:
                    n_idx = new_hanging.index(hang)
                except ValueError:
                    n_idx = len(new_hanging)
                    new_hanging.append(hang)
                lines.append((h_idx, n_idx, colours[hang]))
        hanging = new_hanging

        yield (revisions[revid], node, lines)

def same_branch(a, b):
    """Return whether we think revisions a and b are on the same branch."""
    if len(a.parent_ids) == 1:
        # Defacto same branch if only parent
        return True
    elif a.committer == b.committer:
        # Same committer so may as well be
        return True
    else:
        return False
