from gi.repository import GObject
from gi.repository import Gtk


RESPONSE_BREAK = 0
RESPONSE_CANCEL = Gtk.ResponseType.CANCEL

READ = "read"
WRITE = "write"


def acquire(branch, lock_type):
    if branch.get_physical_lock_status():
        dialog = LockDialog(branch)
        response = dialog.run()
        dialog.destroy()

        if response == RESPONSE_BREAK:
            branch.break_lock()
        else:
            return False

    if lock_type == READ:
        branch.lock_read()
    elif lock_type == WRITE:
        branch.lock_write()

    return True


def release(branch):
    if branch.get_physical_lock_status():
        dialog = LockDialog(branch)
        response = dialog.run()
        dialog.destroy()

        if response == RESPONSE_BREAK:
            branch.break_lock()
        elif response == RESPONSE_CANCEL:
            return False

    branch.unlock()

    return True


class LockDialog(Gtk.Dialog):

    def __init__(self, branch):
        GObject.GObject.__init__(self)

        self.branch = branch

        self.set_title('Lock Not Held')

        self.vbox.add(Gtk.Label(label='This operation cannot be completed as ' \
                                'another application has locked the branch.'))

        self.add_button('Break Lock', RESPONSE_BREAK)
        self.add_button(Gtk.STOCK_CANCEL, RESPONSE_CANCEL)

        self.vbox.show_all()
