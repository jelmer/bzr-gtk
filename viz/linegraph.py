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

def linegraph(revisions, revisionparents, maxnum):
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
    
    #This will hold the lines we have not yet added to lines
    #The position of the item in this list indicates the column, and it
    #it may change if we need to make space for other branches.
    #Each typle in the list is in the form (child index, parent revision)
    #A item may be None to indicate that there is no line for a column
    activelines = []
    
    linegraph = []
    
    for (index, revision) in enumerate(revisions):
        parents = [parent for parent in revisionparents[index]\
                   if parent!="null:"]
        
        revnodecolumn = None
        
        #This will hold a list of lines whose parent is this rev
        linesforcurrentrev = []
        
        children = []
        
        #We should maybe should pop None's at the end of activelines.
        #I'm not sure what will cost more: resizing the list, or
        #have this loop ittrate more.
        
        #Find lines that end at this rev
        for (column, activeline) in enumerate(activelines):
            if (activeline is not None):
                (childindex, parentrevid) = activeline
                if parentrevid == revision.revision_id:
                    linesforcurrentrev.append((childindex, parentrevid, column))
                    activelines[column] = None
                    children.append(linegraph[childindex][0].revision_id)
                    
                    #The node column for this rev will be the smallest
                    #column for the lines that end at this rev
                    #The smallest column is the first one we get to.
                    if revnodecolumn is None:
                        revnodecolumn = column
        
        #This will happen for the latest revision
        if revnodecolumn is None:
            revnodecolumn = 0
        
        color = 0
        
        #We now have every thing (except for the lines) so we can add
        #our tuple to our list.
        linegraph.append((revision, (revnodecolumn, color),
                          [], parents, children))
        
        #add all the line bits to the rev that the line passes
        for (childindex, parentrevid, column) in linesforcurrentrev:
            if index>childindex+1:
                #out from the child to line
                linegraph[childindex][2].append(
                    (linegraph[childindex][1][0], #the column of the child
                     column,                      #the column of the line
                     color))
                
                #down the line
                for linepartindex in range(childindex+1, index-1):
                    linegraph[linepartindex][2].append(
                        (column,                  #the column of the line
                         column,                  #the column of the line
                         color))
                
                #in to the parent
                linegraph[index-1][2].append(
                    (column,                      #the column of the line
                     revnodecolumn,               #the column of the parent
                     color))
            else:
                #child to parent
                linegraph[childindex][2].append(
                    (linegraph[childindex][1][0], #the column of the child
                     revnodecolumn,               #the column of the parent
                     color))
                
        for parentrevid in parents:
            column = revnodecolumn
            line = (index,parentrevid)
            while True:
                if column<len(activelines):
                    if activelines[column] is None:
                        #An empty column. Put line here
                        activelines[column] = line
                        break
                    else:
                        if activelines[column][0] == index:
                            #This column is allready used for a line for
                            #this rev, Move along.
                            column += 1
                        else:
                            #This column is allready used for a line for
                            #another rev. Insert this line at this column,
                            #and in the process, move all the other lines out.
                            activelines.insert(column, line)
                            break
                else:
                    #no more columns, so add one to the end
                    activelines.append(line)
                    break
        if maxnum is not None and index > maxnum:
            break

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
