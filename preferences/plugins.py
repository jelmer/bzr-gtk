# Copyright (C) 2008 Jelmer Vernooij <jelmer@samba.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from gi.repository import Gtk


class PluginsPage(Gtk.VPaned):

    def __init__(self):
        GObject.GObject.__init__(self)
        self.set_border_width(12)
        self.set_position(216)

        scrolledwindow = Gtk.ScrolledWindow()
        scrolledwindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolledwindow.set_shadow_type(Gtk.ShadowType.IN)
        self.model = Gtk.ListStore(str, str)
        treeview = Gtk.TreeView()
        scrolledwindow.add(treeview)
        self.pack1(scrolledwindow, resize=True, shrink=False)

        self.table = Gtk.Table(columns=2)
        self.table.set_border_width(12)
        self.table.set_row_spacings(6)
        self.table.set_col_spacings(6)

        treeview.set_headers_visible(False)
        treeview.set_model(self.model)
        treeview.connect("row-activated", self.row_selected)

        cell = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn()
        column.pack_start(cell, True, True, 0)
        column.add_attribute(cell, "text", 0)
        treeview.append_column(column)

        cell = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn()
        column.pack_start(cell, True, True, 0)
        column.add_attribute(cell, "text", 1)
        treeview.append_column(column)

        import bzrlib.plugin
        plugins = bzrlib.plugin.plugins()
        plugin_names = plugins.keys()
        plugin_names.sort()
        for name in plugin_names:
            self.model.append([name, getattr(plugins[name], '__file__', None)])

        scrolledwindow = Gtk.ScrolledWindow()
        scrolledwindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolledwindow.add_with_viewport(self.table)
        self.pack2(scrolledwindow, resize=False, shrink=True)
        self.show()

    def row_selected(self, tv, path, tvc):
        import bzrlib
        p = bzrlib.plugin.plugins()[self.model[path][0]].module
        from inspect import getdoc

        for w in self.table.get_children():
            self.table.remove(w)

        if getattr(p, '__author__', None) is not None:
            align = Gtk.Alignment.new(0.0, 0.5)
            label = Gtk.Label()
            label.set_markup("<b>Author:</b>")
            align.add(label)
            self.table.attach(align, 0, 1, 0, 1, Gtk.AttachOptions.FILL, Gtk.AttachOptions.FILL)
            align.show()
            label.show()

            align = Gtk.Alignment.new(0.0, 0.5)
            author = Gtk.Label()
            author.set_text(p.__author__)
            author.set_selectable(True)
            align.add(author)
            self.table.attach(align, 1, 2, 0, 1, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, Gtk.AttachOptions.FILL)

        if getattr(p, '__version__', None) is not None:
            align = Gtk.Alignment.new(0.0, 0.5)
            label = Gtk.Label()
            label.set_markup("<b>Version:</b>")
            align.add(label)
            self.table.attach(align, 0, 1, 0, 1, Gtk.AttachOptions.FILL, Gtk.AttachOptions.FILL)
            align.show()
            label.show()

            align = Gtk.Alignment.new(0.0, 0.5)
            author = Gtk.Label()
            author.set_text(p.__version__)
            author.set_selectable(True)
            align.add(author)
            self.table.attach(align, 1, 2, 0, 1, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, Gtk.AttachOptions.FILL)

        if getdoc(p) is not None:
            align = Gtk.Alignment.new(0.0, 0.5)
            description = Gtk.Label()
            description.set_text(getdoc(p))
            description.set_selectable(True)
            align.add(description)
            self.table.attach(align, 0, 2, 1, 2, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, Gtk.AttachOptions.FILL)

        self.table.show_all()


