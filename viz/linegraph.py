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

    Returns a tuple of (line_graph, revid_index, columns_len) where
    * line_graph is a list of tuples of (revid,
                                         node,
                                         lines,
                                         parents,
                                         children,
                                         revno_sequence),
    * revid_index is a dict of each revision with the key being the revid, and
      the value the row index, and
    * columns_len is the number of columns need to draw the line graph.
    

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
    
    # FIXME: This should be configurable
    BROKEN_LINE_LENGTH = 32
    
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
    revno_index = {}
    
    # This will hold an item for each "branch". For a revisions, the revsion
    # number less the least significant digit is the branch_id, and used as the
    # key for the dict. Hence revision with the same revsion number less the
    # least significant digit are considered to be in the same branch line.
    # e.g.: for revisions 290.12.1 and 290.12.2, the branch_id would be 290.12,
    # and these two revisions will be in the same branch line. Each value is
    # a list of rev_indexes in the branch.
    branch_lines = {}
    
    linegraph = []    
    
    for (rev_index, (sequence_number,
                     revid,
                     merge_depth,
                     revno_sequence,
                     end_of_merge)) in enumerate(merge_sorted_revisions):
        if maxnum and rev_index >= maxnum:
            break
        revid_index[revid] = rev_index
        revno_index[revno_sequence] = rev_index
        
        branch_id = revno_sequence[0:-1]
        
        branch_line = None
        if branch_id not in branch_lines:
            branch_line = []
            branch_lines[branch_id] = branch_line
        else:
            branch_line = branch_lines[branch_id]
        
        branch_line.append(rev_index)
        
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
        
        # Find the col_index for the direct parent branch. This will be the
        # starting point when looking for a free column.
        parent_col_index = 0
        parent_index = None
        if len(branch_id) > 1:
            parent_revno = branch_id[0:-1]
            if parent_revno in revno_index:
                parent_index = revno_index[parent_revno]
                parent_node = linegraph[parent_index][1]
                if parent_node:
                    parent_col_index = parent_node[0]
                
        
        col_search_order = _branch_line_col_search_order(columns,
                                                         parent_col_index)
        color = reduce(lambda x, y: x+y, branch_id, 0)
        cur_cont_line = []
        
        line_range = []
        last_rev_index = None
        for rev_index in branch_line:
            if last_rev_index:
                if rev_index - last_rev_index > BROKEN_LINE_LENGTH:
                    line_range.append(last_rev_index+1)
                    line_range.append(rev_index-1)
                else:
                    line_range.extend(range(last_rev_index+1, rev_index))
            
            line_range.append(rev_index)
            last_rev_index = rev_index
        
        if parent_index:
            if parent_index - last_rev_index > BROKEN_LINE_LENGTH:
                line_range.append(last_rev_index+1)
            else:
                line_range.extend(range(last_rev_index+1, parent_index))
        
        col_index = _find_free_column(columns,
                                      empty_column,
                                      col_search_order,
                                      line_range)
        node = (col_index, color)
        for rev_index in branch_line:
            linegraph[rev_index][1] = node
            columns[col_index][rev_index] = True
        
        for rev_index in branch_line:
            (sequence_number,
                 revid,
                 merge_depth,
                 revno_sequence,
                 end_of_merge) = merge_sorted_revisions[rev_index]
            
            linegraph[rev_index][4] = graph_children[revid]
            col_index = linegraph[rev_index][1][0]
            
            for parent_revid in graph_parents[revid]:
                if parent_revid in revid_index:
                    
                    parent_index = revid_index[parent_revid]                            
                    parent_node = linegraph[parent_index][1]
                    if parent_node:
                        parent_col_index = parent_node[0]
                    else:
                        parent_col_index = None
                    col_search_order = \
                            _line_col_search_order(columns,
                                                   parent_col_index,
                                                   col_index)
                        
                    # If this line is really long, break it.
                    if len(branch_id) > 0 and \
                       parent_index - rev_index > BROKEN_LINE_LENGTH:
                        child_line_col_index = \
                            _find_free_column(columns,
                                              empty_column,
                                              col_search_order,
                                              (rev_index + 1,))
                        _mark_column_as_used(columns,
                                             child_line_col_index,
                                             (rev_index + 1,))
                        parent_col_line_index = \
                            _find_free_column(columns,
                                              empty_column,
                                              col_search_order,
                                              (parent_index - 1,))
                        _mark_column_as_used(columns,
                                             parent_col_line_index,
                                             (parent_index - 1,))
                        lines.append((rev_index,
                                      parent_index,
                                      (child_line_col_index,
                                       parent_col_line_index)))
                    else :
                        line_col_index = col_index
                        if parent_index - rev_index >1:
                            line_range = range(rev_index + 1, parent_index)
                            line_col_index = \
                                _find_free_column(columns,
                                                  empty_column,
                                                  col_search_order,
                                                  line_range)
                            _mark_column_as_used(columns,
                                                 line_col_index,
                                                 line_range)
                        lines.append((rev_index,
                                      parent_index,
                                      (line_col_index,)))
    
    for (child_index, parent_index, line_col_indexes) in lines:
        (child_col_index, child_color) = linegraph[child_index][1]
        (parent_col_index, parent_color) = linegraph[parent_index][1]
        
        if len(line_col_indexes) == 1:
            if parent_index - child_index == 1:
                linegraph[child_index][2].append(
                    (child_col_index,
                     parent_col_index,
                     parent_color))
            else:
                # line from the child's column to the lines column
                linegraph[child_index][2].append(
                    (child_col_index,
                     line_col_indexes[0],
                     parent_color))
                # lines down the line's column
                for line_part_index in range(child_index+1, parent_index-1):
                    linegraph[line_part_index][2].append(
                        (line_col_indexes[0],   
                         line_col_indexes[0],
                         parent_color))
                # line from the line's column to the parent's column
                linegraph[parent_index-1][2].append(
                    (line_col_indexes[0],
                     parent_col_index,
                     parent_color))
        else:
            # Broken line
            # line from the child's column to the lines column
            linegraph[child_index][2].append(
                (child_col_index,
                 line_col_indexes[0],
                 parent_color))
            # Broken line end
            linegraph[child_index+1][2].append(
                (line_col_indexes[0],
                 None,
                 parent_color))
            
            # Broken line end 
            linegraph[parent_index-2][2].append(
                (None,
                 line_col_indexes[1],
                 parent_color))
            # line from the line's column to the parent's column
            linegraph[parent_index-1][2].append(
                (line_col_indexes[1],
                 parent_col_index,
                 parent_color))
            
    
    return (linegraph, revid_index, len(columns))

def _branch_line_col_search_order(columns, parent_col_index):
    return range(parent_col_index, len(columns)) + \
           range(parent_col_index-1, -1, -1)

def _line_col_search_order(columns, parent_col_index, child_col_index):
    dest_col_indexes = []
    if parent_col_index is not None:
        dest_col_indexes.append(parent_col_index)
    else:
        dest_col_indexes.append(child_col_index)
    dest_col_indexes.append(child_col_index)
    dest_col_indexes.sort()
    col_search_order = range(dest_col_indexes[1], dest_col_indexes[0] -1, -1) 
    i = 1
    while dest_col_indexes[1] + i < len(columns) or \
          dest_col_indexes[0] - i > -1:
        if dest_col_indexes[1] + i < len(columns):
            col_search_order.append(dest_col_indexes[1] + i)
        if dest_col_indexes[0] - i > -1:
            col_search_order.append(dest_col_indexes[0] - i)
        i += 1
    return col_search_order

def _find_free_column(columns, empty_column, col_search_order, line_range):
    for col_index in col_search_order:
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
    return col_index

def _mark_column_as_used(columns, col_index, line_range):
    column = columns[col_index]
    for row_index in line_range:
        column[row_index] = True    

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
