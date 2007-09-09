# -*- coding: UTF-8 -*-
"""Directed graph production.

This module contains the code to produce an ordered directed graph of a
bzr branch, such as we display in the tree view at the top of the bzrk
window.
"""

__copyright__ = "Copyright © 2005 Canonical Ltd."
__author__    = "Scott James Remnant <scott@ubuntu.com>"

from bzrlib.tsort import merge_sort

def linegraph(branch, start, maxnum):
    """Produce a directed graph of a bzr branch.

    Returns a list of tuples of (revid,
                                 node,
                                 lines,
                                 parents,
                                 children,
                                 revno_sequence).

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
       
    mainline = branch.revision_history()
    graph_parents = branch.repository.get_revision_graph(start)
    graph_children = {}
    for revid in graph_parents.keys():
        graph_children[revid] = []

    merge_sorted_revisions = merge_sort(
        graph_parents,
        start,
        mainline,
        generate_revno=True)
    
    revid_index = {}
    revno_index = {}
    branch_lines = {}
    linegraph = []    
    
    for (index, (sequence_number,
                 revid,
                 merge_depth,
                 revno_sequence,
                 end_of_merge)) in enumerate(merge_sorted_revisions):
        
        revid_index[revid] = index
        
        branch_id = revno_sequence[0:-1]
        
        parents = graph_parents[revid]
        for parent_revid in parents:
            graph_children[parent_revid].append(revid)
        
        children = graph_children[revid]
        
        color = reduce(lambda x, y: x+y, branch_id, 0)
        linegraph.append((revid,
                          (0, color),
                          [],
                          parents,
                          children,
                          revno_sequence))
    
    return (linegraph, revid_index)


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
