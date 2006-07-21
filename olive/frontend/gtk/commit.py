# Copyright (C) 2006 by Szilveszter Farkas (Phanatic) <szilveszter.farkas@gmail.com>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import sys

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass
try:
    import gtk
    import gtk.glade
except:
    sys.exit(1)

import olive.backend.commit as commit
import olive.backend.errors as errors

class OliveCommit:
    """ Display Commit dialog and perform the needed actions. """
    def __init__(self, gladefile, comm):
        """ Initialize the Commit dialog. """
        self.gladefile = gladefile
        self.glade = gtk.glade.XML(self.gladefile, 'window_commit')
        
        self.comm = comm
        
        self.window = self.glade.get_widget('window_commit')
        
        # Dictionary for signal_autoconnect
        dic = { "on_button_commit_commit_clicked": self.commit,
                "on_button_commit_cancel_clicked": self.close }
        
        # Connect the signals to the handlers
        self.glade.signal_autoconnect(dic)
    
    def display(self):
        """ Display the Push dialog. """
        self.window.show_all()
    
    def commit(self, widget):
        from dialog import OliveDialog
        dialog = OliveDialog(self.gladefile)
        
        textview = self.glade.get_widget('textview_commit')
        textbuffer = textview.get_buffer()
        start, end = textbuffer.get_bounds()
        message = textbuffer.get_text(start, end)
        
        checkbutton_local = self.glade.get_widget('checkbutton_commit_local')
        checkbutton_strict = self.glade.get_widget('checkbutton_commit_strict')
        checkbutton_force = self.glade.get_widget('checkbutton_commit_force')
        
        try:
            commit.commit([self.comm.get_path()], message, None,
                          checkbutton_force.get_active(),
                          checkbutton_strict.get_active(),
                          checkbutton_local.get_active())
        except errors.NotBranchError:
            dialog.error_dialog('Directory is not a branch.')
            return
        except errors.LocalRequiresBoundBranch:
            dialog.error_dialog('Local commit requires a bound branch.')
            return
        except errors.EmptyMessageError:
            dialog.error_dialog('Commit message is empty.')
            return
        except errors.NoChangesToCommitError:
            dialog.error_dialog('No changes to commit. Try force commit.')
            return
        except errors.ConflictsInTreeError:
            dialog.error_dialog('Conflicts in tree. Please resolve them first.')
            return
        except errors.StrictCommitError:
            dialog.error_dialog('Strict commit failed. There are unknown files.')
            return
        except errors.BoundBranchOutOfDate, errmsg:
            dialog.error_dialog('Bound branch is out of date: %s' % errmsg)
            return
        except:
            raise
        
        self.close()
        self.comm.refresh_right()
        
    def close(self, widget=None):
        self.window.destroy()
