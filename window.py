
from gi.repository import Gdk
from gi.repository import Gtk


class Window(Gtk.Window):

    def __init__(self, parent=None):
        Gtk.Window.__init__(self, type=Gtk.WindowType.TOPLEVEL)
        self._parent = parent

        self.connect('key-press-event', self._on_key_press)

    def _on_key_press(self, widget, event):
        keyname = Gdk.keyval_name(event.keyval)
        if event.get_state() & Gdk.ModifierType.CONTROL_MASK:
            if keyname is "w":
                self.destroy()
                if self._parent is None:
                    Gtk.main_quit()
            elif keyname is "q":
                Gtk.main_quit()

