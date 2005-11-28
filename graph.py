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
        # ignore candidate parents which are an ancestor of another parent, but
        # never ignore the leftmost parent
        redundant_ids = []
        ignorable_parent_ids = parent_ids[1:] # never ignore leftmost
        for candidate_id in ignorable_parent_ids: 
            for parent_id in list(parent_ids):
                if candidate_id in ancestor_ids_of[parent_id]:
                    redundant_ids.append(candidate_id)
                    parent_ids.remove(candidate_id)
                    children_of_candidate = children[revisions[candidate_id]]
                    children_of_candidate.remove(revision)
                    break
        # save the set of ancestors of that revision
        ancestor_ids = set(parent_ids)
        for parent_id in parent_ids:
            ancestor_ids.update(ancestor_ids_of[parent_id])
        ancestor_ids_of[revid] = ancestor_ids
        # discard ancestry data for revisions whose children are already done
        for parent_id in parent_ids + redundant_ids:
            pending_count = pending_count_of[parent_id] - 1
            pending_count_of[parent_id] = pending_count
            if pending_count == 0:
                ancestor_ids_of[parent_id] = None

    # Try to compact sequences of revisions on the same branch.
    direct_parent_of = {}
    distances = {}
    skipped_revids = []
    expected_id = sorted_revids[0]
    pending_ids = []
    while True:
        revid = sorted_revids.pop(0)
        if revid != expected_id:
            skipped_revids.append(revid)
            continue
        revision = revisions[revid]
        for child in children[revision]:
            # postpone if any child is missing
            if child.revision_id not in distances:
                if expected_id not in pending_ids:
                    pending_ids.append(expected_id)
                assert len(pending_ids) > 1
                expected_id = pending_ids.pop(0)
                skipped_revids.append(revid)
                sorted_revids[:0] = skipped_revids
                skipped_revids = []
                break
        else:
            # all children are here, push!
            distances[revid] = len(distances)
            # choose colour
            the_children = children[revision]
            if len(the_children) == 1:
                [child] = the_children
                if len(parent_ids_of[child]) == 1:
                    # one-one relationship between parent and child, same
                    # colour
                    colours[revid] = colours[child.revision_id]
                else:
                    # one child with multiple parents, the first parent with
                    # the same committer gets the colour
                    direct_parent = direct_parent_of.get(child)
                    if direct_parent is None:                        
                        for parent_id in parent_ids_of[child]:
                            parent_revision = revisions[parent_id]
                            if parent_revision.committer == child.committer:
                                direct_parent = parent_revision
                                direct_parent_of[child] = direct_parent
                                break
                    if direct_parent == revision:
                        colours[revid] = colours[child.revision_id]
                    else:
                        colours[revid] = last_colour = last_colour + 1
            else:
                # multiple children, get the colour of the last displayed child
                # with the same committer which does not already had its colour
                # taken
                available = {}
                for child in the_children:
                    if child.committer != revision.committer:
                        continue
                    direct_parent = direct_parent_of.get(child)
                    if direct_parent == revision:
                        colours[revid] = colours[child.revision_id]
                        break
                    if direct_parent is None:
                        available[child] = distances[child.revision_id]
                else:
                    if available:
                        sorted_children = sorted(available, key=available.get)
                        child = sorted_children[-1]
                        direct_parent_of[child] = revision
                        colours[revid] = colours[child.revision_id]
                    else:
                        # no candidate children is available, pick the next
                        # colour
                        colours[revid] = last_colour = last_colour + 1
            # all parents will need to be pushed as soon as possible
            for parent in parent_ids_of[revision]:
                if parent not in pending_ids:
                    pending_ids.insert(0, parent)
            if not pending_ids:
                break
            expected_id = pending_ids.pop(0)
            # if the next expected revid has already been skipped, requeue it
            # and its potential ancestors.
            if expected_id in skipped_revids:
                pos = skipped_revids.index(expected_id)
                sorted_revids[:0] = skipped_revids[pos:]
                del skipped_revids[pos:]

    sorted_revids = sorted(distances, key=distances.get)

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
