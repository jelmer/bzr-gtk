# -*- coding: UTF-8 -*-
"""Directed graph production.

This module contains the code to produce an ordered directed graph of a
bzr branch, such as we display in the tree view at the top of the bzrk
window.
"""

__copyright__ = "Copyright © 2005 Canonical Ltd."
__author__    = "Scott James Remnant <scott@ubuntu.com>"


from bzrlib.revision import Revision
from bzrlib.tsort import merge_sort

def linegraph(revisions, revisionparents, revindex):
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
    
    directparentcache = [None for revision in revisions]
    def getdirectparent(childrevid, childindex, childsparents):
        """Return the revision id of the direct parent
        
        The direct parent is the first parent with the same committer"""
        childrevision = revisions[childindex]
        directparent = directparentcache[childindex]
        if directparent is None:
            for parentrevid in childsparents:
                if parentrevid in revindex:
                    parentindex = revindex[parentrevid]
                    parentrevision = revisions[parentindex]
                    if childrevision.committer == parentrevision.committer:
                        # This may be a direct parent, but first check that
                        # for this parent, there are no other children, who are
                        # before us in the children list, for which this parent
                        # is also the direct parent.
                        # pc in all the below var name stands for parents child
                        first = True
                        for pcrevid in revisionchildren[parentindex]:
                            if pcrevid == childrevid:
                                break
                            pcindex = revindex[pcrevid]
                            pcdirectparent = getdirectparent(pcrevid,
                                                    pcindex,
                                                    revisionchildren[pcindex])
                            if pcdirectparent==parentrevid:
                                first = False
                                break
                        
                        if first:
                            directparent = parentrevid
                            break
            #no parents have the same commiter
            if directparent is None:
                directparent = ""
            directparentcache[childindex] = directparent
        return directparent
    
    def find_column_from_branchlineid(branchlineid):
        for index, column in enumerate(columns):
            if column is not None and column["branchlineid"] == branchlineid:
                return (index, column)
        return (None, None)
    
    def find_finished_child_column(index, children):
        for childrevid in children:
            childbranchlineid = branchlineids[revindex[childrevid]]
            (columnindex, column) = \
                find_column_from_branchlineid(childbranchlineid)
            if column is not None and column["maxindex"] <= index:
                return (columnindex, column)
        return (None, None)
    
    def has_no_nodes_between (column, startindex, endindex):
        for nodeindex in column["nodeindexes"]:
            if nodeindex > startindex and nodeindex < endindex:
                return False
        return True
    
    def append_line (column , startindex, endindex):
        column["lines"].append((startindex,endindex))
        if endindex > column["maxindex"] :
            column["maxindex"] = endindex
    
    def append_column (column, minindex):
        columnindex = None
        for (i, c) in enumerate(columns):
            if c is None or (c["branchlineid"] == "finished" \
                             and c["maxindex"] <= minindex):
                columnindex = i
                columns[columnindex] = column
                break
        if columnindex is None:
            columnindex = len(columns)
            columns.append(column)
        return columnindex
    
    # This will hold what we plan to put in each column.
    # The position of the item in this list indicates the column, and it
    # it may change if we need to make space for other things.
    # Each typle in the list is in the form:
    # (branchlineid, nodeindexes, lines, maxindex)
    # A item may be None to indicate that there is nothing in the column
    columns = []
    
    linegraph = []
    
    lastbranchlineid = 0
    branchlineids = []
    revisionchildren = [[] for revision in revisions]
    notdrawnlines = []
    
    for (index, revision) in enumerate(revisions):
        parents = [parent for parent in revisionparents[index] \
                   if parent!="null:"]
        for parentrevid in parents:
            if parentrevid in revindex:
                revisionchildren[revindex[parentrevid]]\
                    .append(revision.revision_id)
        
        children = revisionchildren[index]
        linegraph.append([revision, None,
                          [], parents, children])
        
        branchlineid = None
        #Try and see if we are the same branchline as one of our children
        #If we are, use the same branchlineid
        for childrevid in children: 
            childindex = revindex[childrevid]
            childsparents = revisionparents[childindex]
            childbranchlineid = branchlineids[childindex]
            
            if len(children) == 1 and len(childsparents) == 1: 
                # one-one relationship between parent and child
                branchlineid = childbranchlineid
                break
            
            #Is the current revision the direct parent of the child?
            if revision.revision_id == \
                    getdirectparent(childrevid, childindex, childsparents):
                branchlineid = childbranchlineid
                break
        
        if branchlineid is None:
            branchlineid = lastbranchlineid = lastbranchlineid + 1
        
        branchlineids.append(branchlineid)
        
        (columnindex, column) = find_column_from_branchlineid(branchlineid)
        
        if columnindex is None:
            (columnindex, column) = find_finished_child_column(index, children)

        
        if columnindex is None:
            minindex = index
            for childrevid in children:
                childindex = revindex[childrevid]
                if childindex<minindex:
                    minindex = childindex
            
            column = {"branchlineid": branchlineid,
                      "nodeindexes": [index],
                      "lines": [],
                      "maxindex": index}
            columnindex = append_column(column, minindex)
        else:
            column["branchlineid"] = branchlineid
            column["nodeindexes"].append(index)
        
        opentillparent = getdirectparent(revision.revision_id, index, parents)
        if opentillparent == "":
            if len(parents)>0:
                opentillparent = parents[0]
            else:
                opentillparent = None
        
        if opentillparent is not None and opentillparent in revindex:
            parentindex = revindex[opentillparent]
            if parentindex > column["maxindex"]:
                column["maxindex"] = parentindex
        
        for childrevid in children:
            childindex = revindex[childrevid]
            childbranchlineid = branchlineids[childindex]
            (childcolumnindex, childcolumn) = \
                find_column_from_branchlineid(childbranchlineid)
            
            if index-childindex == 1 or childcolumnindex is None:
                append_line(column,childindex,index)
            elif childcolumnindex >= columnindex and \
                    has_no_nodes_between(childcolumn, childindex, index):
                append_line(childcolumn,childindex,index)
            elif childcolumnindex > columnindex and \
                    has_no_nodes_between(column, childindex, index):
                append_line(column,childindex,index)
            elif childcolumnindex < columnindex and \
                    has_no_nodes_between(column, childindex, index):
                append_line(column,childindex,index)
            elif childcolumnindex < columnindex and \
                    has_no_nodes_between(childcolumn, childindex, index):
                append_line(childcolumn,childindex,index)
            else:
                append_column({"branchlineid": "line",
                                "nodeindexes": [],
                                "lines": [(childindex,index)],
                                "maxindex": index}, childindex)
        
        for (columnindex, column) in enumerate(columns):
            if column is not None and column["maxindex"] <= index \
                    and column["branchlineid"] != "finished":
                for nodeindex in column["nodeindexes"]:
                    linegraph[nodeindex][1] = (columnindex,
                                               branchlineids[nodeindex])
            
                for (childindex, parentindex) in column["lines"]:
                    notdrawnlines.append((columnindex, childindex, parentindex))
                
                column["branchlineid"] = "finished"
                column["nodeindexes"] = []
                column["lines"] = []
        
        for (lineindex,(columnindex, childindex, parentindex))\
                in enumerate(notdrawnlines):
            
            childnode = linegraph[childindex][1]
            parentnode = linegraph[parentindex][1]
            if childnode is not None and parentnode is not None:
                notdrawnlines[lineindex] = None
                if parentindex>childindex+1:
                    #out from the child to line
                    linegraph[childindex][2].append(
                        (childnode[0],    #the column of the child
                         columnindex,     #the column of the line
                         parentnode[1]))
                    
                    #down the line
                    for linepartindex in range(childindex+1, parentindex-1):
                        linegraph[linepartindex][2].append(
                            (columnindex, #the column of the line
                             columnindex, #the column of the line
                             parentnode[1]))
                    
                    #in to the parent
                    linegraph[parentindex-1][2].append(
                        (columnindex,     #the column of the line
                         parentnode[0],   #the column of the parent
                         parentnode[1]))
                else:
                    #child to parent
                    linegraph[childindex][2].append(
                        (childnode[0],    #the column of the child
                         parentnode[0],   #the column of the parent
                         parentnode[1]))
        
        notdrawnlines = [line for line in notdrawnlines if line is not None]
        

    return linegraph


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
