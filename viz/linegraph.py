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
        revno_index[revno_sequence] = index
        
        branch_id = revno_sequence[0:-1]
        
        branch_line = None
        if branch_id not in branch_lines:
            branch_line = {}
            branch_lines[branch_id] = branch_line
            branch_line["rev_indexes"] = []
            branch_line["min_index"] = index - 1            
            branch_line["max_index"] = 0
        else:
            branch_line = branch_lines[branch_id]
        branch_line["rev_indexes"].append(index)
        if index > branch_line["max_index"]:
            branch_line["max_index"] = index
        
        parents = graph_parents[revid]
        for parent_revid in parents:
            graph_children[parent_revid].append(revid)
        
        linegraph.append([revid,
                          None,
                          [],
                          parents,
                          None,
                          revno_sequence])

    branch_ids = branch_lines.keys()
    branch_ids.sort()
    columns = []
    
    for branch_id in branch_ids:
        branch_line = branch_lines[branch_id]
        if len(branch_id) >= 2:
            branch_parent_revno = branch_id[0:-1]
            if branch_parent_revno in revno_index:
                branch_line["max_index"] = revno_index[branch_parent_revno]
        
        col_index = None
        start_col_index = 0
        if branch_id:
            start_col_index = branch_lines[branch_id[0:-2]]["col_index"]+1
        for col_search_index in range(start_col_index,len(columns)):
            column = columns[col_search_index]
            clashing_lines = []
            for line in column:
                if (line["min_index"] <= branch_line["min_index"] and \
                    line["max_index"] >  branch_line["min_index"]) or \
                   (line["max_index"] >= branch_line["max_index"] and \
                    line["min_index"] <  branch_line["max_index"]):
                        clashing_lines.append(line)
            
            if not clashing_lines:
                col_index = col_search_index
                break
        
        if not col_index:
            col_index = len(columns)
            columns.append([])
        
        columns[col_index].append(branch_line)
        branch_line["col_index"] = col_index


    for branch_id in branch_ids:
        branch_line = branch_lines[branch_id]
        color = reduce(lambda x, y: x+y, branch_id, 0)
        col_index = branch_line["col_index"]
        node = (col_index, color)
        
        for rev_index in branch_line["rev_indexes"]:
            (sequence_number,
                 revid,
                 merge_depth,
                 revno_sequence,
                 end_of_merge) = merge_sorted_revisions[rev_index]
            children = graph_children[revid]
            
            linegraph[rev_index][1] = node
            linegraph[rev_index][4] = children
            for child_revid in children:
                if child_revid in revid_index:
                    child_index = revid_index[child_revid]
                    child_revno_sequence = \
                                        merge_sorted_revisions[child_index][3]
                    child_merge_depth = merge_sorted_revisions[child_index][2]
                    child_branch_id = child_revno_sequence[0:-1]
                    child_col_index = branch_lines[child_branch_id]["col_index"]
                    if child_merge_depth < merge_depth:
                        #out from the child to line
                        linegraph[child_index][2].append(
                            (child_col_index,
                             col_index,
                             color))
                        for line_part_index in range(child_index+1, rev_index):
                            linegraph[line_part_index][2].append(
                                (col_index,
                                 col_index,
                                 color))
                    else:
                        for line_part_index in range(child_index, rev_index-1):
                            linegraph[line_part_index][2].append(
                                (child_col_index,   
                                 child_col_index,
                                 color))

                        linegraph[rev_index-1][2].append(
                            (child_col_index,
                             col_index,
                             color))
    
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
