# Copyright (C) 2005 Dan Loda <danloda@gmail.com>
# Copyright (C) 2007 Jelmer Vernooij <jelmer@samba.org>

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


class LogView(gtk.Notebook):
    """ Custom widget for commit log details.

    A variety of bzr tools may need to implement such a thing. This is a
    start.
    """

    def __init__(self, revision=None, scroll=True, tags=[],
                 show_children=False):
        gtk.Notebook.__init__(self)
        self.show_children = show_children
        self._create_general()
        self._create_relations()
        self._show_callback = None
        self._go_callback = None
        self._clicked_callback = None

        if revision is not None:
            self.set_revision(revision, tags=tags)

    def set_show_callback(self, callback):
        self._show_callback = callback

    def set_go_callback(self, callback):
        self._go_callback = callback

    def set_revision(self, revision, tags=[], children=[]):
        self._revision = revision
        self.revision_id.set_text(revision.revision_id)
        if revision.committer is not None:
            self.committer.set_text(revision.committer)
        else:
            self.committer.set_text("")
        author = revision.properties.get('author', '')
        if author != '':
            self.author.set_text(author)
            self.author.show()
            self.author_label.show()
        else:
            self.author.hide()
            self.author_label.hide()

        if revision.timestamp is not None:
            self.timestamp.set_text(format_date(revision.timestamp,
                                                revision.timezone))
        self.message_buffer.set_text(revision.message)
        try:
            self.branchnick_label.set_text(revision.properties['branch-nick'])
        except KeyError:
            self.branchnick_label.set_text("")

        self._add_parents_or_children(revision.parent_ids,
                                      self.parents_widgets,
                                      self.parents_table)
        
        if self.show_children:
            self._add_parents_or_children(children,
                                          self.children_widgets,
                                          self.children_table)
        
        self._add_tags(tags)

    def _show_clicked_cb(self, widget, revid, parentid):
        """Callback for when the show button for a parent is clicked."""
        self._show_callback(revid, parentid)

    def _go_clicked_cb(self, widget, revid):
        """Callback for when the go button for a parent is clicked."""
        self._go_callback(revid)

    def _add_tags(self, tags):
        if tags == []:
            self.tags_list.hide()
            self.tags_label.hide()
            return

        for widget in self.tags_widgets:
            self.tags_list.remove(widget)

        self.tags_widgets = []

        for tag in tags:
            widget = gtk.Label(tag)
            widget.set_selectable(True)
            self.tags_widgets.append(widget)
            self.tags_list.add(widget)
        self.tags_list.show_all()
        self.tags_label.show_all()
        
    def _add_parents_or_children(self, revids, widgets, table):
        while len(widgets) > 0:
            widget = widgets.pop()
            table.remove(widget)
        
        table.resize(max(len(revids), 1), 2)

        for idx, revid in enumerate(revids):
            align = gtk.Alignment(0.0, 0.0)
            widgets.append(align)
            table.attach(align, 1, 2, idx, idx + 1,
                                      gtk.EXPAND | gtk.FILL, gtk.FILL)
            align.show()

            hbox = gtk.HBox(False, spacing=6)
            align.add(hbox)
            hbox.show()

            image = gtk.Image()
            image.set_from_stock(
                gtk.STOCK_FIND, gtk.ICON_SIZE_SMALL_TOOLBAR)
            image.show()

            if self._show_callback is not None:
                button = gtk.Button()
                button.add(image)
                button.connect("clicked", self._show_clicked_cb,
                               self._revision.revision_id, revid)
                hbox.pack_start(button, expand=False, fill=True)
                button.show()

            if self._go_callback is not None:
                button = gtk.Button(revid)
                button.connect("clicked", self._go_clicked_cb, revid)
            else:
                button = gtk.Label(revid)
            button.set_use_underline(False)
            hbox.pack_start(button, expand=False, fill=True)
            button.show()

    def _create_general(self):
        vbox = gtk.VBox(False, 6)
        vbox.set_border_width(6)
        vbox.pack_start(self._create_headers(), expand=False, fill=True)
        vbox.pack_start(self._create_message_view())
        self.append_page(vbox, tab_label=gtk.Label("General"))
        vbox.show()

    def _create_relations(self):
        vbox = gtk.VBox(False, 6)
        vbox.set_border_width(6)
        vbox.pack_start(self._create_parents(), expand=False, fill=True)
        if self.show_children:
            vbox.pack_start(self._create_children(), expand=False, fill=True)
        self.append_page(vbox, tab_label=gtk.Label("Relations"))
        vbox.show()
        
    def _create_headers(self):
        self.table = gtk.Table(rows=5, columns=2)
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
        self.author_label = gtk.Label()
        self.author_label.set_markup("<b>Author:</b>")
        align.add(self.author_label)
        self.table.attach(align, 0, 1, 1, 2, gtk.FILL, gtk.FILL)
        align.show()
        self.author_label.show()

        align = gtk.Alignment(0.0, 0.5)
        self.author = gtk.Label()
        self.author.set_selectable(True)
        align.add(self.author)
        self.table.attach(align, 1, 2, 1, 2, gtk.EXPAND | gtk.FILL, gtk.FILL)
        align.show()
        self.author.show()
        self.author.hide()

        align = gtk.Alignment(1.0, 0.5)
        label = gtk.Label()
        label.set_markup("<b>Committer:</b>")
        align.add(label)
        self.table.attach(align, 0, 1, 2, 3, gtk.FILL, gtk.FILL)
        align.show()
        label.show()

        align = gtk.Alignment(0.0, 0.5)
        self.committer = gtk.Label()
        self.committer.set_selectable(True)
        align.add(self.committer)
        self.table.attach(align, 1, 2, 2, 3, gtk.EXPAND | gtk.FILL, gtk.FILL)
        align.show()
        self.committer.show()

        align = gtk.Alignment(0.0, 0.5)
        label = gtk.Label()
        label.set_markup("<b>Branch nick:</b>")
        align.add(label)
        self.table.attach(align, 0, 1, 3, 4, gtk.FILL, gtk.FILL)
        label.show()
        align.show()

        align = gtk.Alignment(0.0, 0.5)
        self.branchnick_label = gtk.Label()
        self.branchnick_label.set_selectable(True)
        align.add(self.branchnick_label)
        self.table.attach(align, 1, 2, 3, 4, gtk.EXPAND | gtk.FILL, gtk.FILL)
        self.branchnick_label.show()
        align.show()

        align = gtk.Alignment(1.0, 0.5)
        label = gtk.Label()
        label.set_markup("<b>Timestamp:</b>")
        align.add(label)
        self.table.attach(align, 0, 1, 4, 5, gtk.FILL, gtk.FILL)
        align.show()
        label.show()

        align = gtk.Alignment(0.0, 0.5)
        self.timestamp = gtk.Label()
        self.timestamp.set_selectable(True)
        align.add(self.timestamp)
        self.table.attach(align, 1, 2, 4, 5, gtk.EXPAND | gtk.FILL, gtk.FILL)
        align.show()
        self.timestamp.show()

        align = gtk.Alignment(1.0, 0.5)
        self.tags_label = gtk.Label()
        self.tags_label.set_markup("<b>Tags:</b>")
        align.add(self.tags_label)
        align.show()
        self.table.attach(align, 0, 1, 5, 6, gtk.FILL, gtk.FILL)
        self.tags_label.show()

        align = gtk.Alignment(0.0, 0.5)
        self.tags_list = gtk.VBox()
        align.add(self.tags_list)
        self.table.attach(align, 1, 2, 5, 6, gtk.EXPAND | gtk.FILL, gtk.FILL)
        align.show()
        self.tags_list.show()
        self.tags_widgets = []

        return self.table

    
    def _create_parents(self):
        hbox = gtk.HBox(True, 3)
        
        self.parents_table = self._create_parents_or_children_table(
            "<b>Parents:</b>")
        self.parents_widgets = []
        hbox.pack_start(self.parents_table)

        hbox.show()
        return hbox

    def _create_children(self):
        hbox = gtk.HBox(True, 3)
        self.children_table = self._create_parents_or_children_table(
            "<b>Children:</b>")
        self.children_widgets = []
        hbox.pack_start(self.children_table)
        hbox.show()
        return hbox
        
    def _create_parents_or_children_table(self, text):
        table = gtk.Table(rows=1, columns=2)
        table.set_row_spacings(3)
        table.set_col_spacings(6)
        table.show()

        label = gtk.Label()
        label.set_markup(text)
        align = gtk.Alignment(0.0, 0.5)
        align.add(label)
        table.attach(align, 0, 1, 0, 1, gtk.FILL, gtk.FILL)
        label.show()
        align.show()

        return table
    


    def _create_message_view(self):
        self.message_buffer = gtk.TextBuffer()
        tv = gtk.TextView(self.message_buffer)
        tv.set_editable(False)
        tv.set_wrap_mode(gtk.WRAP_WORD)
        tv.modify_font(pango.FontDescription("Monospace"))
        tv.show()
        return tv

