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

    Returns a list of tuples of (revision, node, lines, parents, children).

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
    
    rev_index = {}
    
    
    merge_sorted_revisions = merge_sort(
        graph_parents,
        start,
        mainline,
        generate_revno=True)
    
    revids = [revid for (sequence_number,
                 revid,
                 merge_depth,
                 revno_sequence,
                 end_of_merge) in merge_sorted_revisions]
    
    revisions = branch.repository.get_revisions(revids)
    linegraph = []
    
    for (index, (sequence_number,
                 revid,
                 merge_depth,
                 revno_sequence,
                 end_of_merge)) in enumerate(merge_sorted_revisions):
        
        revision = revisions[index]
        rev_index[revid] = index
        
        color = reduce(lambda x, y: x+y, revno_sequence[0:-2], 0)
        
        parents = [parent for parent in graph_parents[revid] \
                   if parent!="null:"]
        
        for parent_revid in parents:
            graph_children[parent_revid].append(revid)
        
        children = graph_children[revid]
        
        for child_revid in children:
            child_index = rev_index[child_revid]
            child_merge_depth = merge_sorted_revisions[child_index][2]
            #out from the child to line
            linegraph[child_index][2].append(
                (child_merge_depth,    #the column of the child
                 merge_depth,     #the column of the line
                 color))
            
            for line_part_index in range(child_index+1, index):
                linegraph[line_part_index][2].append(
                    (merge_depth,    #the column of the child
                     merge_depth,     #the column of the line
                     color))
        
        linegraph.append((revision, (merge_depth, color),
                          [], parents, children))

    return (linegraph, rev_index, revisions)


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
