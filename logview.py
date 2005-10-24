# Copyright (C) 2005 Dan Loda <danloda@gmail.com>

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

import pygtk
pygtk.require("2.0")
import gtk
import pango

from bzrlib.osutils import format_date


class LogView(gtk.ScrolledWindow):
    """ Custom widget for commit log details.

    A variety of bzr tools may need to implement such a thing. This is a
    start.
    """

    def __init__(self, revision=None):
        gtk.ScrolledWindow.__init__(self)
        self.parent_id_widgets = []
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.set_shadow_type(gtk.SHADOW_NONE)
        self._create()

        if revision is not None:
            self.set_revision(revision)

    def set_revision(self, revision):
        self.revision_id.set_text(revision.revision_id)
        self.committer.set_text(revision.committer)
        self.timestamp.set_text(format_date(revision.timestamp,
                                                  revision.timezone))
        self.message_buffer.set_text(revision.message)
        self._add_parents(revision.parent_ids)

    def _add_parents(self, parent_ids):
        for widget in self.parent_id_widgets:
            self.table.remove(widget)
            
        self.parent_id_widgets = []

        if len(parent_ids):
            self.table.resize(4 + len(parent_ids), 2)

            align = gtk.Alignment(1.0, 0.5)
            align.show()
            self.table.attach(align, 0, 1, 3, 4, gtk.FILL, gtk.FILL)
            self.parent_id_widgets.append(align)

            label = gtk.Label()
            if len(parent_ids) > 1:
                label.set_markup("<b>Parent Ids:</b>")
            else:
                label.set_markup("<b>Parent Id:</b>")
            label.show()
            align.add(label)

            for i, parent_id in enumerate(parent_ids):
                align = gtk.Alignment(0.0, 0.5)
                self.parent_id_widgets.append(align)
                self.table.attach(align, 1, 2, i + 3, i + 4,
                                  gtk.EXPAND | gtk.FILL, gtk.FILL)
                align.show()
                label = gtk.Label(parent_id)
                label.set_selectable(True)
                label.show()
                align.add(label)

    def _create(self):
        vbox = gtk.VBox(False, 6)
        vbox.set_border_width(6)
        vbox.pack_start(self._create_headers(), expand=False, fill=True)
        vbox.pack_start(self._create_message_view())
        self.add_with_viewport(vbox)
        vbox.show()

    def _create_headers(self):
        self.table = gtk.Table(rows=4, columns=2)
        self.table.set_row_spacings(6)
        self.table.set_col_spacings(6)
        self.table.show()
        
        align = gtk.Alignment(1.0, 0.5)
        label = gtk.Label()
        label.set_markup("<b>Committer:</b>")
        align.add(label)
        self.table.attach(align, 0, 1, 0, 1, gtk.FILL, gtk.FILL)
        align.show()
        label.show()

        align = gtk.Alignment(0.0, 0.5)
        self.committer = gtk.Label()
        self.committer.set_selectable(True)
        align.add(self.committer)
        self.table.attach(align, 1, 2, 0, 1, gtk.EXPAND | gtk.FILL, gtk.FILL)
        align.show()
        self.committer.show()

        align = gtk.Alignment(1.0, 0.5)
        label = gtk.Label()
        label.set_markup("<b>Timestamp:</b>")
        align.add(label)
        self.table.attach(align, 0, 1, 1, 2, gtk.FILL, gtk.FILL)
        align.show()
        label.show()

        align = gtk.Alignment(0.0, 0.5)
        self.timestamp = gtk.Label()
        self.timestamp.set_selectable(True)
        align.add(self.timestamp)
        self.table.attach(align, 1, 2, 1, 2, gtk.EXPAND | gtk.FILL, gtk.FILL)
        align.show()
        self.timestamp.show()

        align = gtk.Alignment(1.0, 0.5)
        label = gtk.Label()
        label.set_markup("<b>Revision Id:</b>")
        align.add(label)
        self.table.attach(align, 0, 1, 2, 3, gtk.FILL, gtk.FILL)
        align.show()
        label.show()

        align = gtk.Alignment(0.0, 0.5)
        self.revision_id = gtk.Label()
        self.revision_id.set_selectable(True)
        align.add(self.revision_id)
        self.table.attach(align, 1, 2, 2, 3, gtk.EXPAND | gtk.FILL, gtk.FILL)
        align.show()
        self.revision_id.show()

        return self.table

    def _create_message_view(self):
        self.message_buffer = gtk.TextBuffer()
        tv = gtk.TextView(self.message_buffer)
        tv.set_editable(False)
        tv.set_wrap_mode(gtk.WRAP_WORD)
        tv.modify_font(pango.FontDescription("Monospace"))
        tv.show()
        return tv

