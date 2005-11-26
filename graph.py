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
            # Get the parent from the cache, or put it in the cache
            try:
                parent = revisions[parent_id]
            except KeyError:
                try:
                    parent = branch.get_revision(parent_id)
                except NoSuchRevision:
                    parent = DummyRevision(parent_id)
                revisions[parent_id] = parent
            children.setdefault(parent, set()).add(revision)

            # Check whether there's any point re-processing this
            if parent_id in distances and distances[parent_id] >= distance:
                continue

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

    # Topologically sorted revids, with the most recent revisions first
    sorted_revids = sorted(distances, key=distances.get)

    # Build a parents dictionnary, where redundant parents will be removed, and
    # that will be passed along tothe rest of program.
    parent_ids_of = {}
    for revision in revisions.itervalues():
        if len(revision.parent_ids) == len(set(revision.parent_ids)):
            parent_ids_of[revision] = list(revision.parent_ids)
        else:
            # remove duplicate parent revisions
            parent_ids = []
            parent_ids_set = set()
            for parent_id in revision.parent_ids:
                if parent_id in parent_ids_set:
                    continue
                parent_ids.append(parent_id)
                parent_ids_set.add(parent_id)
            parent_ids_of[revision] = parent_ids

    # Count the number of children of each revision, so we can release memory
    # for ancestry data as soon as it's not going to be needed anymore.
    pending_count_of = {}
    for parent, the_children in children.iteritems():
        pending_count_of[parent.revision_id] = len(the_children)

    # Build the ancestry dictionnary by examining older revisions first, and
    # remove revision parents that are ancestors of other parents of the same
    # revision.
    ancestor_ids_of = {}
    for revid in reversed(sorted_revids):
        revision = revisions[revid]
        parent_ids = parent_ids_of[revision]
        # ignore candidate parents which are an ancestor of another parent
        redundant_ids = []
        for candidate_id in list(parent_ids):
            for parent_id in list(parent_ids):
                if candidate_id in ancestor_ids_of[parent_id]:
                    redundant_ids.append(candidate_id)
                    parent_ids.remove(candidate_id)
                    children_of_candidate = children[revisions[candidate_id]]
                    children_of_candidate.remove(revision)
                    break
        ancestor_ids = set(parent_ids)
        for parent_id in parent_ids:
            ancestor_ids.update(ancestor_ids_of[parent_id])
        for parent_id in parent_ids + redundant_ids:
            pending_count = pending_count_of[parent_id] - 1
            pending_count_of[parent_id] = pending_count
            if pending_count == 0:
                ancestor_ids_of[parent_id] = None
        ancestor_ids_of[revid] = ancestor_ids

    return (sorted_revids, revisions, colours, children, parent_ids_of)

def graph(revids, revisions, colours, parent_ids):
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
                for parent_id in parent_ids[revisions[revid]]:
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
