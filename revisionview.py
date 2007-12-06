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
import gobject

from bzrlib.osutils import format_date
from bzrlib.util import bencode

class RevisionView(gtk.Notebook):
    """ Custom widget for commit log details.

    A variety of bzr tools may need to implement such a thing. This is a
    start.
    """

    __gproperties__ = {
        'branch': (
            gobject.TYPE_PYOBJECT,
            'Branch',
            'The branch holding the revision being displayed',
            gobject.PARAM_CONSTRUCT_ONLY | gobject.PARAM_WRITABLE
        ),

        'revision': (
            gobject.TYPE_PYOBJECT,
            'Revision',
            'The revision being displayed',
            gobject.PARAM_READWRITE
        ),

        'file-id': (
            gobject.TYPE_PYOBJECT,
            'File Id',
            'The file id',
            gobject.PARAM_READWRITE
        )
    }


    def __init__(self, branch=None):
        gtk.Notebook.__init__(self)
        self.show_children = False

        self._create_general()
        self._create_relations()
        self._create_file_info_view()

        self.set_current_page(0)
        
        self._show_callback = None
        self._go_callback = None
        self._clicked_callback = None

        self._branch = branch

        if self._branch.supports_tags():
            self._tagdict = self._branch.tags.get_reverse_tag_dict()
        else:
            self._tagdict = {}

        self.set_file_id(None)

    def do_get_property(self, property):
        if property.name == 'branch':
            return self._branch
        elif property.name == 'revision':
            return self._revision
        elif property.name == 'file-id':
            return self._file_id
        else:
            raise AttributeError, 'unknown property %s' % property.name

    def do_set_property(self, property, value):
        if property.name == 'branch':
            self._branch = value
        elif property.name == 'revision':
            self._set_revision(value)
        elif property.name == 'file-id':
            self._file_id = value
        else:
            raise AttributeError, 'unknown property %s' % property.name

    def set_show_callback(self, callback):
        self._show_callback = callback

    def set_go_callback(self, callback):
        self._go_callback = callback

    def set_file_id(self, file_id):
        """Set a specific file id that we want to track.

        This just effects the display of a per-file commit message.
        If it is set to None, then all commit messages will be shown.
        """
        self.set_property('file-id', file_id)

    def set_revision(self, revision, children=[]):
        self.set_property('revision', revision)

    def _set_revision(self, revision, children=[]):
        if revision is None: return

        self._revision = revision
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
        

        file_info = revision.properties.get('file-info', None)
        if file_info is not None:
            file_info = bencode.bdecode(file_info.encode('UTF-8'))

        if file_info:
            if self._file_id is None:
                text = []
                for fi in file_info:
                    text.append('%(path)s\n%(message)s' % fi)
                self.file_info_buffer.set_text('\n'.join(text))
                self.file_info_box.show()
            else:
                text = []
                for fi in file_info:
                    if fi['file_id'] == self._file_id:
                        text.append(fi['message'])
                if text:
                    self.file_info_buffer.set_text('\n'.join(text))
                    self.file_info_box.show()
                else:
                    self.file_info_box.hide()
        else:
            self.file_info_box.hide()

    def _show_clicked_cb(self, widget, revid, parentid):
        """Callback for when the show button for a parent is clicked."""
        self._show_callback(revid, parentid)

    def _go_clicked_cb(self, widget, revid):
        """Callback for when the go button for a parent is clicked."""
        self._go_callback(revid)

    def _add_tags(self, *args):
        if self._tagdict.has_key(self._revision.revision_id):
            tags = self._tagdict[self._revision.revision_id]
        else:
            tags = []
            
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
        revision_id = gtk.Label()
        revision_id.set_selectable(True)
        self.connect('notify::revision', 
                lambda w, p: revision_id.set_text(self._revision.revision_id))
        align.add(revision_id)
        self.table.attach(align, 1, 2, 0, 1, gtk.EXPAND | gtk.FILL, gtk.FILL)
        align.show()
        revision_id.show()

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

        self.connect('notify::revision', self._add_tags)

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
        msg_buffer = gtk.TextBuffer()
        self.connect('notify::revision',
                lambda w, p: msg_buffer.set_text(self._revision.message))
        window = gtk.ScrolledWindow()
        window.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        window.set_shadow_type(gtk.SHADOW_IN)
        tv = gtk.TextView(msg_buffer)
        tv.set_editable(False)
        tv.set_wrap_mode(gtk.WRAP_WORD)
        tv.modify_font(pango.FontDescription("Monospace"))
        tv.show()
        window.add(tv)
        window.show()
        return window

    def _create_file_info_view(self):
        self.file_info_box = gtk.VBox(False, 6)
        self.file_info_box.set_border_width(6)
        self.file_info_buffer = gtk.TextBuffer()
        window = gtk.ScrolledWindow()
        window.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        window.set_shadow_type(gtk.SHADOW_IN)
        tv = gtk.TextView(self.file_info_buffer)
        tv.set_editable(False)
        tv.set_wrap_mode(gtk.WRAP_WORD)
        tv.modify_font(pango.FontDescription("Monospace"))
        tv.show()
        window.add(tv)
        window.show()
        self.file_info_box.pack_start(window)
        self.file_info_box.hide() # Only shown when there are per-file messages
        self.append_page(self.file_info_box, tab_label=gtk.Label('Per-file'))

