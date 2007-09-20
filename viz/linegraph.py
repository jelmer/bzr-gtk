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
            branch_line = {"line_type": "branch_line",
                           "branch_id": branch_id,
                           "rev_indexes": [],
                           "min_index": index,
                           "max_index": 0}
            branch_lines[branch_id] = branch_line
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
    def branch_id_cmp(x, y):
        len_x = len(x)
        len_y = len(y)
        if len_x == len_y:
            return -cmp(x, y)
        return cmp(len_x, len_y)
        
    branch_ids.sort(branch_id_cmp)
    inter_branch_lines = {}
    all_lines = []
    
    for branch_id in branch_ids:
        branch_line = branch_lines[branch_id]
        branch_parent_revno = None
        all_lines.append(branch_line)
        
        for rev_index in branch_line["rev_indexes"]:
            (sequence_number,
                 revid,
                 merge_depth,
                 revno_sequence,
                 end_of_merge) = merge_sorted_revisions[rev_index]
            for parent_revid in graph_parents[revid]:
                if parent_revid in revid_index:
                    parent_index = revid_index[parent_revid]
                    if parent_index - rev_index > 1:
                        parent_revno = merge_sorted_revisions[parent_index][3]
                        parent_branch_id = parent_revno[0:-1]
                        if branch_id != parent_branch_id:
                            inter_branch_line = {"line_type": "inter_branch_line",
                                                 "min_index": rev_index,
                                                 "max_index": parent_index,
                                                 "child_branch_id": branch_id,
                                                 "parent_branch_id": parent_branch_id}
                            inter_branch_lines[(rev_index, parent_index)] = \
                                                                inter_branch_line
                            all_lines.append (inter_branch_line)
    
    columns = []
    for line in all_lines:
        for col_index, column in enumerate(columns):
            has_overlaping_line = False
            for col_line in column:
                if not (col_line["min_index"] >= line["max_index"] or \
                        col_line["max_index"] <=  line["min_index"]):
                    has_overlaping_line = True
                    break
            if not has_overlaping_line:
                break
        else:
            col_index = len(columns)
            columns.append([])
        line["col_index"] = col_index
        columns[col_index].append(line)

    for branch_line in branch_lines.itervalues():
        branch_id = branch_line["branch_id"]
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
                    inter_branch_line_id = (child_index, rev_index)
                    if inter_branch_line_id in inter_branch_lines:
                        inter_branch_line = \
                                    inter_branch_lines[inter_branch_line_id]
                        child_branch_id = inter_branch_line["child_branch_id"]
                        child_col_index = \
                                    branch_lines[child_branch_id]["col_index"]
                        inter_branch_line_col_index = \
                                                inter_branch_line["col_index"]
                        linegraph[child_index][2].append(
                            (child_col_index,
                             inter_branch_line_col_index,
                             color))
                        for line_part_index in range(child_index+1,
                                                     rev_index-1):
                            linegraph[line_part_index][2].append(
                                (inter_branch_line_col_index,   
                                 inter_branch_line_col_index,
                                 color))

                        linegraph[rev_index-1][2].append(
                            (inter_branch_line_col_index,
                             col_index,
                             color))

                    else:
                        child_revno_sequence = \
                                        merge_sorted_revisions[child_index][3]
                        child_branch_id = child_revno_sequence[0:-1]                    
                        child_col_index = \
                                    branch_lines[child_branch_id]["col_index"]
                        
                        linegraph[child_index][2].append(
                            (child_col_index,
                             col_index,
                             color))
                        for line_part_index in range(child_index+1, rev_index):
                            linegraph[line_part_index][2].append(
                                (col_index,   
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
