#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""Directed graph production.

This module contains the code to produce an ordered directed graph of a
bzr branch, such as we display in the tree view at the top of the bzrk
window.
"""

__copyright__ = "Copyright © 2005 Canonical Ltd."
__author__    = "Scott James Remnant <scott@ubuntu.com>"


from bzrlib.tsort import merge_sort


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


class RevisionProxy(object):
    """A revision proxy object.

    This will demand load the revision it represents when the committer or
    message attributes are accessed in order to populate them. It is 
    constructed with the revision id and parent_ids list and a repository
    object to request the revision from when needed.
    """

    def __init__(self, revid, parent_ids, repository):
        self.revision_id = revid
        self.parent_ids = parent_ids
        self._repository = repository
        self._revision = None

    def _get_attribute_getter(attr):
        def get_attribute(self):
            if self._revision is None:
                self._load()
            return getattr(self._revision, attr)
        return get_attribute
    committer = property(_get_attribute_getter('committer'))
    message = property(_get_attribute_getter('message'))
    properties = property(_get_attribute_getter('properties'))
    timestamp = property(_get_attribute_getter('timestamp'))
    timezone = property(_get_attribute_getter('timezone'))

    def _load(self):
        """Load the revision object."""
        self._revision = self._repository.get_revision(self.revision_id)


class DistanceMethod(object):

    def __init__(self, branch, start):
        self.branch = branch
        self.start = start
        self.revisions = {}
        self.children = {}
        self.children_of_id = {start: set()}
        self.parent_ids_of = {}
        self.colours = { start: 0 }
        self.last_colour = 0
        self.direct_parent_of = {}
        self.graph = {}

    def fill_caches(self):
        graph = self.branch.repository.get_revision_graph_with_ghosts([self.start])
        for revid in graph.ghosts:
            self.cache_revision(DummyRevision(revid))
        for revid, parents in graph.get_ancestors().items():
            self.cache_revision(RevisionProxy(revid, parents, self.branch.repository))

    def cache_revision(self, revision):
        "Set the caches for a newly retrieved revision."""
        revid = revision.revision_id
        # Build a revision cache
        self.revisions[revid] = revision
        # Build a children dictionary
        for parent_id in revision.parent_ids:
            self.children_of_id.setdefault(parent_id, set()).add(revision)
        # Build a parents dictionnary, where redundant parents will be removed,
        # and that will be passed along tothe rest of program.
        if len(revision.parent_ids) != len(set(revision.parent_ids)):
            # fix the parent_ids list.
            parent_ids = []
            parent_ids_set = set()
            for parent_id in revision.parent_ids:
                if parent_id in parent_ids_set:
                    continue
                parent_ids.append(parent_id)
                parent_ids_set.add(parent_id)
            revision.parent_ids = parent_ids
        self.parent_ids_of[revision] = list(revision.parent_ids)
        self.graph[revid] = revision.parent_ids

    def make_children_map(self):
        revisions = self.revisions
        return dict((revisions[revid], c)
                    for (revid, c) in self.children_of_id.iteritems())

    def sort_revisions(self, sorted_revids, maxnum):
        revisions = self.revisions
        parent_ids_of = self.parent_ids_of
        children_of_id = self.children_of_id
        # Try to compact sequences of revisions on the same branch.
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
            for child in children_of_id[revid]:
                # postpone if any child is missing
                if child.revision_id not in distances:
                    if expected_id not in pending_ids:
                        pending_ids.append(expected_id)
                    expected_id = pending_ids.pop(0)
                    skipped_revids.append(revid)
                    sorted_revids[:0] = skipped_revids
                    del skipped_revids[:]
                    break
            else:
                # all children are here, push!
                distances[revid] = len(distances)
                if maxnum is not None and len(distances) > maxnum:
                    # bail out early if a limit was specified
                    sorted_revids[:0] = skipped_revids
                    for revid in sorted_revids:
                        distances[revid] = len(distances)
                    break
                # all parents will need to be pushed as soon as possible
                for parent in parent_ids_of[revision]:
                    if parent not in pending_ids:
                        pending_ids.insert(0, parent)
                if not pending_ids:
                    break
                expected_id = pending_ids.pop(0)
                # if the next expected revid has already been skipped, requeue
                # the skipped ids, except those that would go right back to the
                # skipped list.
                if expected_id in skipped_revids:
                    pos = skipped_revids.index(expected_id)
                    sorted_revids[:0] = skipped_revids[pos:]
                    del skipped_revids[pos:]
        self.distances = distances
        return sorted(distances, key=distances.get)

    def choose_colour(self, revid):
        revision = self.revisions[revid]
        children_of_id = self.children_of_id
        parent_ids_of = self.parent_ids_of
        colours = self.colours
        # choose colour
        the_children = children_of_id[revid]
        if len(the_children) == 1:
            [child] = the_children
            if len(parent_ids_of[child]) == 1:
                # one-one relationship between parent and child, same
                # colour
                colours[revid] = colours[child.revision_id]
            else:
                self.choose_colour_one_child(revision, child)
        else:
            self.choose_colour_many_children(revision, the_children)

    def choose_colour_one_child(self, revision, child):
        revid = revision.revision_id
        direct_parent_of = self.direct_parent_of
        revisions = self.revisions
        # one child with multiple parents, the first parent with
        # the same committer gets the colour
        direct_parent = direct_parent_of.get(child)
        if direct_parent is None:
            # if it has not been found yet, find it now and remember
            for parent_id in self.parent_ids_of[child]:
                parent_revision = revisions[parent_id]
                if parent_revision.committer == child.committer:
                    # found the first parent with the same committer
                    direct_parent = parent_revision
                    direct_parent_of[child] = direct_parent
                    break
        if direct_parent == revision:
            self.colours[revid] = self.colours[child.revision_id]
        else:
            self.colours[revid] = self.last_colour = self.last_colour + 1

    def choose_colour_many_children(self, revision, the_children):
        """Colour revision revision."""
        revid = revision.revision_id
        direct_parent_of = self.direct_parent_of
        # multiple children, get the colour of the last displayed child
        # with the same committer which does not already have its colour
        # taken
        available = {}
        for child in the_children:
            if child.committer != revision.committer:
                continue
            direct_parent = direct_parent_of.get(child)
            if direct_parent == revision:
                self.colours[revid] = self.colours[child.revision_id]
                break
            # FIXME: Colouring based on whats been displayed MUST be done with 
            # knowledge of the revisions being output.
            # until the refactoring to fold graph() into this more compactly is
            # done, I've disabled this reuse. RBC 20060403
            # if direct_parent is None:
            #     available[child] = distances[child.revision_id] 
            #   .. it will be something like available[child] =  \
            #  revs[child.revision_id][0] - which is the sequence number
        else:
            if available:
                sorted_children = sorted(available, key=available.get)
                child = sorted_children[-1]
                direct_parent_of[child] = revision
                self.colours[revid] = self.colours[child.revision_id]
            else:
                # no candidate children is available, pick the next
                # colour
                self.colours[revid] = self.last_colour = self.last_colour + 1


def distances(branch, start):
    """Sort the revisions.

    Traverses the branch revision tree starting at start and produces an
    ordered list of revisions such that a revision always comes after
    any revision it is the parent of.

    Returns a tuple of (revids, revisions, colours, children)
    """
    distance = DistanceMethod(branch, start)
    distance.fill_caches()
    distance.merge_sorted = merge_sort(distance.graph, distance.start)
    children = distance.make_children_map()
    
    for seq, revid, merge_depth, end_of_merge in distance.merge_sorted:
        distance.choose_colour(revid)

    revisions = distance.revisions
    colours = distance.colours
    parent_ids_of = distance.parent_ids_of
    return (revisions, colours, children, parent_ids_of, distance.merge_sorted)


def graph(revisions, colours, merge_sorted):
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
    if not len(merge_sorted):
        return
    # split merge_sorted into a map:
    revs = {}
    # FIXME: get a hint on this from the merge_sorted data rather than
    # calculating it ourselves
    # mapping from rev_id to the sequence number of the next lowest rev
    next_lower_rev = {}
    # mapping from rev_id to next-in-branch-revid - may be None for end
    # of branch
    next_branch_revid = {}
    # the stack we are in in the sorted data for determining which 
    # next_lower_rev to set. It is a stack which has one list at each
    # depth - the ids at that depth that need the same id allocated.
    current_stack = [[]]
    for seq, revid, indent, end_merge in merge_sorted:
        revs[revid] = (seq, indent, end_merge)
        if indent == len(current_stack):
            # new merge group starts
            current_stack.append([revid])
        elif indent == len(current_stack) - 1:
            # part of the current merge group
            current_stack[-1].append(revid)
        else:
            # end of a merge group
            while current_stack[-1]:
                stack_rev_id = current_stack[-1].pop()
                # record the next lower rev for this rev:
                next_lower_rev[stack_rev_id] = seq
                # if this followed a non-end-merge rev in this group note that
                if len(current_stack[-1]):
                    if not revs[current_stack[-1][-1]][2]:
                        next_branch_revid[current_stack[-1][-1]] = stack_rev_id
            current_stack.pop()
            # append to the now-current merge group
            current_stack[-1].append(revid)
    # assign a value to all the depth 0 revisions
    while current_stack[-1]:
        stack_rev_id = current_stack[-1].pop()
        # record the next lower rev for this rev:
        next_lower_rev[stack_rev_id] = len(merge_sorted)
        # if this followed a non-end-merge rev in this group note that
        if len(current_stack[-1]):
            if not revs[current_stack[-1][-1]][2]:
                next_branch_revid[current_stack[-1][-1]] = stack_rev_id

    # a list of the current revisions we are drawing lines TO indicating
    # the sequence of their lines on the screen.
    # i.e. [A, B, C] means that the line to A, to B, and to C are in
    # (respectively), 0, 1, 2 on the screen.
    hanging = [merge_sorted[0][1]]
    for seq, revid, indent, end_merge in merge_sorted:
        # a list of the lines to draw: their position in the
        # previous row, their position in this row, and the colour
        # (which is the colour they are routing to).
        lines = []

        new_hanging = []

        for h_idx, hang in enumerate(hanging):
            # one of these will be the current lines node:
            # we are drawing a line. h_idx 
            if hang == revid:
                # we have found the current lines node
                node = (h_idx, colours[revid])

                # note that we might have done the main parent
                drawn_parents = set()

                def draw_line(from_idx, to_idx, revision_id):
                    try:
                        n_idx = new_hanging.index(revision_id)
                    except ValueError:
                        # force this to be vertical at the place this rev was
                        # drawn.
                        new_hanging.insert(to_idx, revision_id)
                        n_idx = to_idx
                    lines.append((from_idx, n_idx, colours[revision_id]))

                
                # we want to draw a line to the next commit on 'this' branch
                if not end_merge:
                    # drop this line first.
                    parent_id = next_branch_revid[revid]
                    draw_line(h_idx, h_idx, parent_id)
                    # we have drawn this parent
                    drawn_parents.add(parent_id)
                else:
                    # this is the last revision in a 'merge', show where it came from
                    if len(revisions[revid].parent_ids) > 1:
                        # having > 1
                        # parents means this commit was a merge, and being
                        # the end point of a merge group means that all
                        # the parent revisions were merged into branches
                        # to the left of this before this was committed
                        # - so we want to show this as a new branch from
                        # those revisions.
                        # to do this, we show the parent with the lowest
                        # sequence number, which is the one that this
                        # branch 'spawned from', and no others.
                        # If this sounds like a problem, remember that:
                        # if the parent was not already in our mainline
                        # it would show up as a merge into this making
                        # this not the end of a merge-line.
                        lowest = len(merge_sorted)
                        for parent_id in revisions[revid].parent_ids:
                            if revs[parent_id][0] < lowest:
                                lowest = revs[parent_id][0]
                        assert lowest != len(merge_sorted)
                        draw_line(h_idx, len(new_hanging), merge_sorted[lowest][1])
                        drawn_parents.add(merge_sorted[lowest][1])
                    elif len(revisions[revid].parent_ids) == 1:
                        # only one parent, must show this link to be useful.
                        parent_id = revisions[revid].parent_ids[0]
                        draw_line(h_idx, len(new_hanging), parent_id)
                        drawn_parents.add(parent_id)
                
                # what do we want to draw lines to from here:
                # each parent IF its relevant.
                #
                # Now we need to hang its parents, we put them at the point
                # the old column was so anything to the right of this has
                # to move outwards to make room.  We also try and collapse
                # hangs to keep the graph small.
                # RBC: we do not draw lines to parents that were already merged
                # unless its the last revision in a merge group.
                for parent_id in revisions[revid].parent_ids:
                    if parent_id in drawn_parents:
                        continue
                    parent_seq = revs[parent_id][0]
                    parent_depth = revs[parent_id][1]
                    if parent_depth == indent + 1:
                        # The parent was a merge into this branch determine if
                        # it was already merged into the mainline via a
                        # different merge: if all revisions between us and
                        # parent_seq have a indent greater than there are no
                        # revisions with a lower indent than us.
                        # We do not use 'parent_depth < indent' because that
                        # would allow un-uniqueified merges to show up, and
                        # merge_sorted should take care of that for us (but
                        # does not trim the values)
                        if parent_seq < next_lower_rev[revid]:
                            draw_line(h_idx, len(new_hanging), parent_id)
                    elif parent_depth == indent and parent_seq == seq + 1:
                        # part of this branch
                        draw_line(h_idx, len(new_hanging), parent_id)
            else:
                # draw a line from the previous position of this line to the 
                # new position.
                # h_idx is the old position.
                # new_indent is the new position. 
                draw_line(h_idx, len(new_hanging), hang)
        # we've calculated the row, assign new_hanging to hanging to setup for
        # the next row
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
