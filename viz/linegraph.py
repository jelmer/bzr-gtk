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
    
    # We get the mainline so we can pass it to merge_sort to make merge_sort
    # run faster.
    mainline = branch.revision_history()
    graph_parents = branch.repository.get_revision_graph(start)
    graph_children = {}
    for revid in graph_parents.iterkeys():
        graph_children[revid] = []

    merge_sorted_revisions = merge_sort(
        graph_parents,
        start,
        mainline,
        generate_revno=True)
    
    revid_index = {}
    
    # This will hold an item for each "branch". For a revisions, the revsion
    # number less the least significant digit is the branch_id, and used as the
    # key for the dict. Hence revision with the same revsion number less the
    # least significant digit are considered to be in the same branch line.
    # e.g.: for revisions 290.12.1 and 290.12.2, the branch_id would be 290.12,
    # and these two revisions will be in the same branch line. Each value is
    # a list of [rev_indexes, min_index, max_index, col_index].
    branch_lines = {}
    BL_REV_INDEXES = 0
    BL_MIN_INDEX = 1
    BL_MAX_INDEX = 2
    BL_COL_INDEX = 3
    
    linegraph = []    
    
    for (rev_index, (sequence_number,
                     revid,
                     merge_depth,
                     revno_sequence,
                     end_of_merge)) in enumerate(merge_sorted_revisions):
        
        revid_index[revid] = rev_index
        
        branch_id = revno_sequence[0:-1]
        
        branch_line = None
        if branch_id not in branch_lines:
            branch_line = [[],        # BL_REV_INDEXES
                           rev_index, # BL_MIN_INDEX
                           0,         # BL_MAX_INDEX
                           None]      # BL_COL_INDEX
            branch_lines[branch_id] = branch_line
        else:
            branch_line = branch_lines[branch_id]
        
        branch_line[BL_REV_INDEXES].append(rev_index)
        if rev_index > branch_line[BL_MAX_INDEX]:
            branch_line[BL_MAX_INDEX] = rev_index
        
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
        """Compaire branch_id's first by the number of digits, then reversed
        by their value"""
        len_x = len(x)
        len_y = len(y)
        if len_x == len_y:
            return -cmp(x, y)
        return cmp(len_x, len_y)
    
    branch_ids.sort(branch_id_cmp)
    # This will hold a tuple of (child_index, parent_index, col_index) for each
    # line that needs to be drawn. If col_index is not none, then the line is
    # drawn along that column, else the the line can be drawn directly between
    # the child and parent because either the child and parent are in the same
    # branch line, or the child and parent are 1 row apart.
    lines = []
    empty_column = [False for i in range(len(graph_parents))]
    # This will hold a bit map for each cell. If the cell is true, then the
    # cell allready contains a node or line. This use when deciding what column
    # to place a branch line or line in, without it overlaping something else.
    columns = [list(empty_column)]
    
    
    for branch_id in branch_ids:
        branch_line = branch_lines[branch_id]
        
        
        parent_col_index = 0
        if len(branch_id) > 1:
            parent_branch_id = branch_id[0:-2]
            parent_col_index = branch_lines[parent_branch_id][BL_COL_INDEX]
        
        branch_line[BL_COL_INDEX] = append_line(columns,
                                               (branch_line[BL_MIN_INDEX],
                                                branch_line[BL_MAX_INDEX]),
                                               empty_column,
                                               parent_col_index,
                                               False)
        color = reduce(lambda x, y: x+y, branch_id, 0)
        col_index = branch_line[BL_COL_INDEX]
        node = (col_index, color)        
        
        for rev_index in branch_line[BL_REV_INDEXES]:
            (sequence_number,
                 revid,
                 merge_depth,
                 revno_sequence,
                 end_of_merge) = merge_sorted_revisions[rev_index]
            
            linegraph[rev_index][1] = node
            linegraph[rev_index][4] = graph_children[revid]
            
            for parent_revid in graph_parents[revid]:
                if parent_revid in revid_index:
                    parent_index = revid_index[parent_revid]
                    parent_revno = merge_sorted_revisions[parent_index][3]
                    parent_branch_id = parent_revno[0:-1]
                    col_index = None
                    if branch_id != parent_branch_id and \
                                    parent_index - rev_index > 1:
                        col_index = append_line(columns,
                                                (rev_index+1, parent_index-1),
                                                empty_column,
                                                branch_line[BL_COL_INDEX],
                                                True)
                    lines.append((rev_index, parent_index, col_index))
    
    for (child_index, parent_index, line_col_index) in lines:
        child_col_index = linegraph[child_index][1][0]
        
        parent_node = linegraph[parent_index][1]
        parent_col_index = parent_node[0]
        color = parent_node[1]
        
        if line_col_index:
            linegraph[child_index][2].append(
                (child_col_index,
                 line_col_index,
                 color))
            for line_part_index in range(child_index+1, parent_index-1):
                linegraph[line_part_index][2].append(
                    (line_col_index,   
                     line_col_index,
                     color))
            linegraph[parent_index-1][2].append(
                (line_col_index,
                 parent_col_index,
                 color))
        else:
            linegraph[child_index][2].append(
                (child_col_index,
                 parent_col_index,
                 color))
            for line_part_index in range(child_index+1, parent_index):
                linegraph[line_part_index][2].append(
                    (parent_col_index,   
                     parent_col_index,
                     color))
                    
    
    return (linegraph, revid_index)

def append_line(columns, line, empty_column, starting_col_index, search_inwards):
    line_range = range(line[0], line[1]+1)
    if search_inwards:
        col_order = range(starting_col_index, -1, -1) + \
                    range(starting_col_index+1, len(columns))
    else:
        col_order = range(starting_col_index, len(columns)) + \
                    range(starting_col_index-1, -1, -1)
    
    for col_index in col_order:
        column = columns[col_index]
        has_overlaping_line = False
        for row_index in line_range:
            if column[row_index]:
                has_overlaping_line = True
                break
        if not has_overlaping_line:
            break
    else:
        col_index = len(columns)
        column = list(empty_column)
        columns.append(column)
    
    for row_index in line_range:
        column[row_index] = True
    return col_index

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
