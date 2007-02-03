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
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.set_shadow_type(gtk.SHADOW_NONE)
        self._create()
        self._show_callback = None
        self._clicked_callback = None

        if revision is not None:
            self.set_revision(revision)

    def set_show_callback(self, callback):
        self._show_callback = callback

    def set_go_callback(self, callback):
        self._go_callback = callback

    def set_revision(self, revision):
        self._revision = revision
        self.revision_id.set_text(revision.revision_id)
        self.committer.set_text(revision.committer)
        self.timestamp.set_text(format_date(revision.timestamp,
                                            revision.timezone))
        self.message_buffer.set_text(revision.message)
        try:
            self.branchnick_label.set_text(revision.properties['branch-nick'])
        except KeyError:
            self.branchnick_label.set_text("")

        self._add_parents(revision.parent_ids)

    def _show_clicked_cb(self, widget, revid, parentid):
        """Callback for when the show button for a parent is clicked."""
        self._show_callback(revid, parentid)

    def _go_clicked_cb(self, widget, revid):
        """Callback for when the go button for a parent is clicked."""
        self._go_callback(revid)

    def _add_parents(self, parent_ids):
        for widget in self.parents_widgets:
            self.parents_table.remove(widget)
            
        self.parents_widgets = []
        self.parents_table.resize(max(len(parent_ids), 1), 2)

        for idx, parent_id in enumerate(parent_ids):
            align = gtk.Alignment(0.0, 0.0)
            self.parents_widgets.append(align)
            self.parents_table.attach(align, 1, 2, idx, idx + 1,
                                      gtk.EXPAND | gtk.FILL, gtk.FILL)
            align.show()

            hbox = gtk.HBox(False, spacing=6)
            align.add(hbox)
            hbox.show()

            image = gtk.Image()
            image.set_from_stock(
                gtk.STOCK_FIND, gtk.ICON_SIZE_SMALL_TOOLBAR)
            image.show()

            button = gtk.Button()
            button.add(image)
            button.set_sensitive(self._show_callback is not None)
            button.connect("clicked", self._show_clicked_cb,
                           self._revision.revision_id, parent_id)
            hbox.pack_start(button, expand=False, fill=True)
            button.show()

            button = gtk.Button(parent_id)
            button.set_use_underline(False)
            button.connect("clicked", self._go_clicked_cb, parent_id)
            hbox.pack_start(button, expand=False, fill=True)
            button.show()

    def _create(self):
        vbox = gtk.VBox(False, 6)
        vbox.set_border_width(6)
        vbox.pack_start(self._create_headers(), expand=False, fill=True)
        vbox.pack_start(self._create_parents_table(), expand=False, fill=True)
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
        label.set_markup("<b>Revision Id:</b>")
        align.add(label)
        self.table.attach(align, 0, 1, 0, 1, gtk.FILL, gtk.FILL)
        align.show()
        label.show()

        align = gtk.Alignment(0.0, 0.5)
        self.revision_id = gtk.Label()
        self.revision_id.set_selectable(True)
        align.add(self.revision_id)
        self.table.attach(align, 1, 2, 0, 1, gtk.EXPAND | gtk.FILL, gtk.FILL)
        align.show()
        self.revision_id.show()

        align = gtk.Alignment(1.0, 0.5)
        label = gtk.Label()
        label.set_markup("<b>Committer:</b>")
        align.add(label)
        self.table.attach(align, 0, 1, 1, 2, gtk.FILL, gtk.FILL)
        align.show()
        label.show()

        align = gtk.Alignment(0.0, 0.5)
        self.committer = gtk.Label()
        self.committer.set_selectable(True)
        align.add(self.committer)
        self.table.attach(align, 1, 2, 1, 2, gtk.EXPAND | gtk.FILL, gtk.FILL)
        align.show()
        self.committer.show()

        align = gtk.Alignment(0.0, 0.5)
        label = gtk.Label()
        label.set_markup("<b>Branch nick:</b>")
        align.add(label)
        self.table.attach(align, 0, 1, 2, 3, gtk.FILL, gtk.FILL)
        label.show()
        align.show()

        align = gtk.Alignment(0.0, 0.5)
        self.branchnick_label = gtk.Label()
        self.branchnick_label.set_selectable(True)
        align.add(self.branchnick_label)
        self.table.attach(align, 1, 2, 2, 3, gtk.EXPAND | gtk.FILL, gtk.FILL)
        self.branchnick_label.show()
        align.show()

        align = gtk.Alignment(1.0, 0.5)
        label = gtk.Label()
        label.set_markup("<b>Timestamp:</b>")
        align.add(label)
        self.table.attach(align, 0, 1, 3, 4, gtk.FILL, gtk.FILL)
        align.show()
        label.show()

        align = gtk.Alignment(0.0, 0.5)
        self.timestamp = gtk.Label()
        self.timestamp.set_selectable(True)
        align.add(self.timestamp)
        self.table.attach(align, 1, 2, 3, 4, gtk.EXPAND | gtk.FILL, gtk.FILL)
        align.show()
        self.timestamp.show()

        return self.table

    def _create_parents_table(self):
        self.parents_table = gtk.Table(rows=1, columns=2)
        self.parents_table.set_row_spacings(3)
        self.parents_table.set_col_spacings(6)
        self.parents_table.show()
        self.parents_widgets = []

        label = gtk.Label()
        label.set_markup("<b>Parents:</b>")
        align = gtk.Alignment(0.0, 0.5)
        align.add(label)
        self.parents_table.attach(align, 0, 1, 0, 1, gtk.FILL, gtk.FILL)
        label.show()
        align.show()

        return self.parents_table

    def _create_message_view(self):
        self.message_buffer = gtk.TextBuffer()
        tv = gtk.TextView(self.message_buffer)
        tv.set_editable(False)
        tv.set_wrap_mode(gtk.WRAP_WORD)
        tv.modify_font(pango.FontDescription("Monospace"))
        tv.show()
        return tv

