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
    def getdirectparent(childindex, childsparents):
        """Return the revision id of the direct parent
        
        The direct parent is the first parent with the same committer"""
        childrevision = revisions[childindex]
        directparent = directparentcache[childindex]
        if directparent is None:
            for parentrevid in childsparents:
                parentrevision = revisions[revindex[parentrevid]]
                if childrevision.committer == parentrevision.committer:
                    directparent = parentrevid
                    break
            #no parents have the same commiter
            if directparent is None:
                directparent = ""
            directparentcache[childindex] = directparent
        return directparent
        

    
    #This will hold the lines we have not yet added to lines
    #The position of the item in this list indicates the column, and it
    #it may change if we need to make space for other branches.
    #Each typle in the list is in the form (child index, parent revision)
    #A item may be None to indicate that there is no line for a column
    activelines = []
    
    linegraph = []
    
    lastcolor = 0
    
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
        
        color = None
        
        #Try and see if we are the same "branch" as one of our children
        #If we are, use the childs color
        for childrevid in children:
            childindex = revindex[childrevid]
            childsparents = revisionparents[childindex]
            if len(children) == 1 and len(childsparents) == 1: 
                # one-one relationship between parent and child, same colour
                #1st [1] selects the node
                #2nd [1] selects the color
                color = linegraph[childindex][1][1]
                break
            
            #Is the current revision the direct parent of the child?
            if revision.revision_id == getdirectparent(childindex, childsparents):
                color = linegraph[childindex][1][1]
                break
        
        if color is None:
            color = lastcolor = lastcolor + 1
        
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
                            #This column is allready used for a line for another
                            #rev. Insert her.
                            
                            #See if there is a None after us that we could
                            #move the lines after us into
                            movetocolumn = None
                            for i in \
                                    range(column+1,len(activelines)):
                                if activelines[i] is None:
                                    movetocolumn = i
                                    break
                            
                            if movetocolumn is None:
                                #No None was found. Insert line here
                                activelines.insert(column, line)
                            else:
                                #Move the lines after us out to the None
                                for movecolumn in \
                                        reversed(range(column,movetocolumn)):
                                    activelines[movecolumn+1] = \
                                        activelines[movecolumn]
                                #And put line here
                                activelines[column] = line
                            
                            break
                else:
                    #no more columns, so add one to the end
                    activelines.append(line)
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
