# -*- coding: UTF-8 -*-
"""Tree model.

"""

__copyright__ = "Copyright © 2005 Canonical Ltd."
__author__    = "Gary van der Merwe <garyvdm@gmail.com>"


import gtk
import gobject
import pango
import re
from xml.sax.saxutils import escape

from time import (strftime, localtime)

REVID      =  0
NODE       =  1
LINES      =  2
LAST_LINES =  3
REVNO      =  4
SUMMARY    =  5
MESSAGE    =  6
COMMITTER  =  7
TIMESTAMP  =  8
REVISION   =  9
PARENTS    = 10
CHILDREN   = 11

class TreeModel(gtk.GenericTreeModel):

    
    def __init__ (self, repository, line_graph_data):
        gtk.GenericTreeModel.__init__(self)
        self.revisions = {}
        self.repository = repository
        self.line_graph_data = line_graph_data
    
    def on_get_flags(self):
        return gtk.TREE_MODEL_LIST_ONLY
    
    def on_get_n_columns(self):
        return 12
    
    def on_get_column_type(self, index):
        if index == REVID:      return gobject.TYPE_STRING
        if index == NODE:       return gobject.TYPE_PYOBJECT
        if index == LINES:      return gobject.TYPE_PYOBJECT
        if index == LAST_LINES: return gobject.TYPE_PYOBJECT
        if index == REVNO:      return gobject.TYPE_STRING
        if index == SUMMARY:    return gobject.TYPE_STRING
        if index == MESSAGE:    return gobject.TYPE_STRING
        if index == COMMITTER:  return gobject.TYPE_STRING
        if index == TIMESTAMP:  return gobject.TYPE_STRING
        if index == REVISION:   return gobject.TYPE_PYOBJECT
        if index == PARENTS:    return gobject.TYPE_PYOBJECT
        if index == CHILDREN:   return gobject.TYPE_PYOBJECT
        
    def on_get_iter(self, path):
        return path[0]
    
    def on_get_path(self, rowref):
        return rowref
    
    def on_get_value(self, rowref, column):
        if len(self.line_graph_data) > 0:
            (revid, node, lines, parents,
             children, revno_sequence) = self.line_graph_data[rowref]
        else:
            (revid, node, lines, parents,
             children, revno_sequence) = (None, (0, 0), (), (),
                                          (), ())
        if column == REVID: return revid
        if column == NODE: return node
        if column == LINES: return lines
        if column == PARENTS: return parents
        if column == CHILDREN: return children
        if column == LAST_LINES:
            if rowref>0:
                return self.line_graph_data[rowref-1][2]
            return []
        if column == REVNO: return ".".join(["%d" % (revno)
                                      for revno in revno_sequence])
        
        if revid is None:
            return None
        if revid not in self.revisions:
            revision = self.repository.get_revisions([revid])[0]
            self.revisions[revid] = revision
        else:
            revision = self.revisions[revid]
        
        if column == REVISION: return revision
        if column == SUMMARY: return escape(revision.get_summary())
        if column == MESSAGE: return escape(revision.message)
        if column == COMMITTER: return re.sub('<.*@.*>', '', 
                                             revision.committer).strip(' ')
        if column == TIMESTAMP: 
            return strftime("%Y-%m-%d %H:%M", localtime(revision.timestamp))

    def on_iter_next(self, rowref):
        if rowref < len(self.line_graph_data) - 1:
            return rowref+1
        return None
    
    def on_iter_children(self, parent):
        if parent is None: return 0
        return None
    
    def on_iter_has_child(self, rowref):
        return False
    
    def on_iter_n_children(self, rowref):
        if rowref is None: return len(self.line_graph_data)
        return 0
    
    def on_iter_nth_child(self, parent, n):
        if parent is None: return n
        return None
    
    def on_iter_parent(self, child):
        return None
