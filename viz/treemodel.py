# -*- coding: UTF-8 -*-
"""Tree model.

"""

__copyright__ = "Copyright © 2005 Canonical Ltd."
__author__    = "Gary van der Merwe <garyvdm@gmail.com>"


import gtk
import gobject
import pango

from bzrlib.osutils import format_date

REVID = 0
NODE = 1
LINES = 2
LAST_LINES = 3
REVNO = 4
MESSAGE = 5
COMMITER = 6
TIMESTAMP = 7
REVISION = 8
PARENTS = 9
CHILDREN = 10

class TreeModel(gtk.TreeModel):

    
    def __init__ (self, branch, line_graph_data):
        self.revisions = {}
        self.branch = branch
        self.line_graph_data = line_graph_data
    
    def get_flags(self):
        return gtk.TREE_MODEL_LIST_ONLY
    
    def get_n_columns(self):
        return 11
    
    def get_column_type(self, index):
        if index == REVID: return gobject.TYPE_STRING
        if index == NODE: return gobject.TYPE_PYOBJECT
        if index == LINES: return gobject.TYPE_PYOBJECT
        if index == LAST_LINES: return gobject.TYPE_PYOBJECT
        if index == REVNO: return gobject.TYPE_STRING
        if index == MESSAGE: return gobject.TYPE_STRING
        if index == COMMITER: return gobject.TYPE_STRING
        if index == TIMESTAMP: return gobject.TYPE_STRING
        if index == REVISION: return gobject.TYPE_PYOBJECT
        if index == PARENTS: return gobject.TYPE_PYOBJECT
        if index == CHILDREN: return gobject.TYPE_PYOBJECT
        
    def get_iter(self, path):
        return path[0]
    
    def get_iter_from_string(self, path_string):
        raise NotImplementedError
    
    def get_string_from_iter(self, iter):
        raise NotImplementedError

    def get_iter_root(self):
        if len(self.line_graph_data) == 0: return None
        return 0
    
    def get_iter_first(self):
        if len(self.line_graph_data) == 0: return None
        return 0

    def get_path(self, iter):
        return iter
    
    def get_value(self, iter, column):
        (revid, node, lines, parents,
         children, revno_sequence) = self.line_graph_data[iter]
        if column == REVID: return revid
        if column == NODE: return node
        if column == LINES: return lines
        if column == PARENTS: return parents
        if column == CHILDREN: return children
        if column == LAST_LINES:
            if iter>0:
                return self.line_graph_data[iter-1][2]
            return []
        if column == REVNO: return ".".join(["%d" % (revno)
                                      for revno in revno_sequence])
        
        if revid in self.revisions:
            revision = self.revisions[revid]
            
            if column == REVISION: return revision
            if column == MESSAGE: return revision.message.split("\n")[0]
            if column == COMMITER: return revision.committer
            if column == TIMESTAMP: return format_date(revision.timestamp,
                                                       revision.timezone)
        return None
    
    def iter_next(self, iter):
        if iter < len(self.line_graph_data) - 1:
            return iter+1
        return None
    
    def iter_children(self, parent):
        if parent is None: return 0
        return None
    
    def iter_has_child(self, iter):
        return False
    
    def iter_n_children(self, iter):
        if iter is None: return len(self.line_graph_data)
        return 0
    
    def iter_nth_child(self, parent, n):
        if parent is None: return n
        return None
    
    def iter_parent(self, child):
        return None
    
    def ref_node(self, iter):
        revid = self.line_graph_data[iter][0]
        if revid not in self.revisions:
            revision = self.branch.repository.get_revisions([revid])[0]
            self.revisions[revid] = revision        

    def unref_node(self,iter):
        pass
    
    def get(self, iter, *column):
        raise NotImplementedError
    
    def foreach(self, func, user_data):
        raise NotImplementedError        

    def row_changed(self, path, iter):
        raise NotImplementedError

    def row_inserted(self, path, iter):
        raise NotImplementedError

    def row_has_child_toggled(self, path, iter):
        raise NotImplementedError

    def row_deleted(self, path):
        raise NotImplementedError

    def rows_reordered(self, path, iter, new_order):
        raise NotImplementedError

    def filter_new(self, root=None):
        raise NotImplementedError
