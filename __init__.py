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

"""Graphical support for Bazaar using GTK.

This plugin includes:
commit-notify     Start the graphical notifier of commits.
gannotate         GTK+ annotate. 
gbranch           GTK+ branching. 
gcheckout         GTK+ checkout. 
gcommit           GTK+ commit dialog.
gconflicts        GTK+ conflicts. 
gdiff             Show differences in working tree in a GTK+ Window. 
ghandle-patch     Display and optionally merge a merge directive or patch.
ginit             Initialise a new branch.
gmissing          GTK+ missing revisions dialog. 
gpreferences      GTK+ preferences dialog. 
gpush             GTK+ push.
gsend             GTK+ send merge directive.
gstatus           GTK+ status dialog.
gtags             Manage branch tags.
visualise         Graphically visualise this branch. 
"""

import sys

import bzrlib

version_info = (0, 94, 0, 'dev', 0)

if version_info[3] == 'final':
    version_string = '%d.%d.%d' % version_info[:3]
else:
    version_string = '%d.%d.%d%s%d' % version_info
__version__ = version_string

required_bzrlib = (1, 3)

def check_bzrlib_version(desired):
    """Check that bzrlib is compatible.

    If version is < bzr-gtk version, assume incompatible.
    """
    bzrlib_version = bzrlib.version_info[:2]
    try:
        from bzrlib.trace import warning
    except ImportError:
        # get the message out any way we can
        from warnings import warn as warning
    if bzrlib_version < desired:
        from bzrlib.errors import BzrError
        warning('Installed Bazaar version %s is too old to be used with bzr-gtk'
                ' %s.' % (bzrlib.__version__, __version__))
        raise BzrError('Version mismatch: %r, %r' % (version_info, bzrlib.version_info) )


if version_info[2] == "final":
    check_bzrlib_version(required_bzrlib)

from bzrlib.trace import warning
if __name__ != 'bzrlib.plugins.gtk':
    warning("Not running as bzrlib.plugins.gtk, things may break.")

from bzrlib.lazy_import import lazy_import
lazy_import(globals(), """
from bzrlib import (
    branch,
    builtins,
    errors,
    merge_directive,
    workingtree,
    )
""")

from bzrlib.commands import Command, register_command, display_command
from bzrlib.errors import NotVersionedError, BzrCommandError, NoSuchFile
from bzrlib.option import Option

import os.path

def import_pygtk():
    try:
        import pygtk
    except ImportError:
        raise errors.BzrCommandError("PyGTK not installed.")
    pygtk.require('2.0')
    return pygtk


def set_ui_factory():
    import_pygtk()
    from ui import GtkUIFactory
    import bzrlib.ui
    bzrlib.ui.ui_factory = GtkUIFactory()


def data_path():
    return os.path.dirname(__file__)


def icon_path(*args):
    basedirs = [os.path.join(data_path()),
             "/usr/share/bzr-gtk", 
             "/usr/local/share/bzr-gtk"]
    for basedir in basedirs:
        path = os.path.join(basedir, 'icons', *args)
        if os.path.exists(path):
            return path
    return None


class GTKCommand(Command):
    """Abstract class providing GTK specific run commands."""

    def open_display(self):
        pygtk = import_pygtk()
        try:
            import gtk
        except RuntimeError, e:
            if str(e) == "could not open display":
                raise NoDisplayError
        set_ui_factory()
        return gtk

    def run(self):
        self.open_display()
        dialog = self.get_gtk_dialog(os.path.abspath('.'))
        dialog.run()


class cmd_gbranch(GTKCommand):
    """GTK+ branching.
    
    """

    def get_gtk_dialog(self, path):
        from bzrlib.plugins.gtk.branch import BranchDialog
        return BranchDialog(path)


class cmd_gcheckout(GTKCommand):
    """ GTK+ checkout.
    
    """
    
    def get_gtk_dialog(self, path):
        from bzrlib.plugins.gtk.checkout import CheckoutDialog
        return CheckoutDialog(path)



class cmd_gpush(GTKCommand):
    """ GTK+ push.
    
    """
    takes_args = [ "location?" ]

    def run(self, location="."):
        (br, path) = branch.Branch.open_containing(location)
        self.open_display()
        from push import PushDialog
        dialog = PushDialog(br.repository, br.last_revision(), br)
        dialog.run()



class cmd_gdiff(GTKCommand):
    """Show differences in working tree in a GTK+ Window.
    
    Otherwise, all changes for the tree are listed.
    """
    takes_args = ['filename?']
    takes_options = ['revision']

    @display_command
    def run(self, revision=None, filename=None):
        set_ui_factory()
        wt = workingtree.WorkingTree.open_containing(".")[0]
        wt.lock_read()
        try:
            branch = wt.branch
            if revision is not None:
                if len(revision) == 1:
                    tree1 = wt
                    revision_id = revision[0].in_history(branch).rev_id
                    tree2 = branch.repository.revision_tree(revision_id)
                elif len(revision) == 2:
                    revision_id_0 = revision[0].in_history(branch).rev_id
                    tree2 = branch.repository.revision_tree(revision_id_0)
                    revision_id_1 = revision[1].in_history(branch).rev_id
                    tree1 = branch.repository.revision_tree(revision_id_1)
            else:
                tree1 = wt
                tree2 = tree1.basis_tree()

            from diff import DiffWindow
            import gtk
            window = DiffWindow()
            window.connect("destroy", gtk.main_quit)
            window.set_diff("Working Tree", tree1, tree2)
            if filename is not None:
                tree_filename = wt.relpath(filename)
                try:
                    window.set_file(tree_filename)
                except NoSuchFile:
                    if (tree1.path2id(tree_filename) is None and 
                        tree2.path2id(tree_filename) is None):
                        raise NotVersionedError(filename)
                    raise BzrCommandError('No changes found for file "%s"' % 
                                          filename)
            window.show()

            gtk.main()
        finally:
            wt.unlock()


def start_viz_window(branch, revisions, limit=None):
    """Start viz on branch with revision revision.
    
    :return: The viz window object.
    """
    from viz import BranchWindow
    return BranchWindow(branch, revisions, limit)


class cmd_visualise(Command):
    """Graphically visualise this branch.

    Opens a graphical window to allow you to see the history of the branch
    and relationships between revisions in a visual manner,

    The default starting point is latest revision on the branch, you can
    specify a starting point with -r revision.
    """
    takes_options = [
        "revision",
        Option('limit', "Maximum number of revisions to display.",
               int, 'count')]
    takes_args = [ "locations*" ]
    aliases = [ "visualize", "vis", "viz" ]

    def run(self, locations_list, revision=None, limit=None):
        set_ui_factory()
        if locations_list is None:
            locations_list = ["."]
        revids = []
        for location in locations_list:
            (br, path) = branch.Branch.open_containing(location)
            if revision is None:
                revids.append(br.last_revision())
            else:
                (revno, revid) = revision[0].in_history(br)
                revids.append(revid)
        import gtk
        pp = start_viz_window(br, revids, limit)
        pp.connect("destroy", lambda w: gtk.main_quit())
        pp.show()
        gtk.main()


class cmd_gannotate(GTKCommand):
    """GTK+ annotate.
    
    Browse changes to FILENAME line by line in a GTK+ window.
    """

    takes_args = ["filename", "line?"]
    takes_options = [
        Option("all", help="Show annotations on all lines."),
        Option("plain", help="Don't highlight annotation lines."),
        Option("line", type=int, argname="lineno",
               help="Jump to specified line number."),
        "revision",
    ]
    aliases = ["gblame", "gpraise"]
    
    def run(self, filename, all=False, plain=False, line='1', revision=None):
        gtk = self.open_display()

        try:
            line = int(line)
        except ValueError:
            raise BzrCommandError('Line argument ("%s") is not a number.' % 
                                  line)

        from annotate.gannotate import GAnnotateWindow
        from annotate.config import GAnnotateConfig
        from bzrlib.bzrdir import BzrDir

        wt, br, path = BzrDir.open_containing_tree_or_branch(filename)
        if wt is not None:
            tree = wt
        else:
            tree = br.basis_tree()

        file_id = tree.path2id(path)

        if file_id is None:
            raise NotVersionedError(filename)
        if revision is not None:
            if len(revision) != 1:
                raise BzrCommandError("Only 1 revion may be specified.")
            revision_id = revision[0].in_history(br).rev_id
            tree = br.repository.revision_tree(revision_id)
        else:
            revision_id = getattr(tree, 'get_revision_id', lambda: None)()

        window = GAnnotateWindow(all, plain)
        window.connect("destroy", lambda w: gtk.main_quit())
        config = GAnnotateConfig(window)
        window.show()
        br.lock_read()
        if wt is not None:
            wt.lock_read()
        try:
            window.annotate(tree, br, file_id)
            window.jump_to_line(line)
            gtk.main()
        finally:
            br.unlock()
            if wt is not None:
                wt.unlock()



class cmd_gcommit(GTKCommand):
    """GTK+ commit dialog

    Graphical user interface for committing revisions"""

    aliases = [ "gci" ]
    takes_args = []
    takes_options = []

    def run(self, filename=None):
        import os
        self.open_display()
        from commit import CommitDialog
        from bzrlib.errors import (BzrCommandError,
                                   NotBranchError,
                                   NoWorkingTree)

        wt = None
        br = None
        try:
            (wt, path) = workingtree.WorkingTree.open_containing(filename)
            br = wt.branch
        except NoWorkingTree, e:
            from dialog import error_dialog
            error_dialog(_('Directory does not have a working tree'),
                         _('Operation aborted.'))
            return 1 # should this be retval=3?

        # It is a good habit to keep things locked for the duration, but it
        # could cause difficulties if someone wants to do things in another
        # window... We could lock_read() until we actually go to commit
        # changes... Just a thought.
        wt.lock_write()
        try:
            dlg = CommitDialog(wt)
            return dlg.run()
        finally:
            wt.unlock()


class cmd_gstatus(GTKCommand):
    """GTK+ status dialog

    Graphical user interface for showing status 
    information."""
    
    aliases = [ "gst" ]
    takes_args = ['PATH?']
    takes_options = []

    def run(self, path='.'):
        import os
        gtk = self.open_display()
        from status import StatusDialog
        (wt, wt_path) = workingtree.WorkingTree.open_containing(path)
        status = StatusDialog(wt, wt_path)
        status.connect("destroy", gtk.main_quit)
        status.run()


class cmd_gsend(GTKCommand):
    """GTK+ send merge directive.

    """
    def run(self):
        (br, path) = branch.Branch.open_containing(".")
        gtk = self.open_display()
        from bzrlib.plugins.gtk.mergedirective import SendMergeDirectiveDialog
        from StringIO import StringIO
        dialog = SendMergeDirectiveDialog(br)
        if dialog.run() == gtk.RESPONSE_OK:
            outf = StringIO()
            outf.writelines(dialog.get_merge_directive().to_lines())
            mail_client = br.get_config().get_mail_client()
            mail_client.compose_merge_request(dialog.get_mail_to(), "[MERGE]", 
                outf.getvalue())

            


class cmd_gconflicts(GTKCommand):
    """GTK+ conflicts.
    
    Select files from the list of conflicts and run an external utility to
    resolve them.
    """
    def run(self):
        (wt, path) = workingtree.WorkingTree.open_containing('.')
        self.open_display()
        from bzrlib.plugins.gtk.conflicts import ConflictsDialog
        dialog = ConflictsDialog(wt)
        dialog.run()


class cmd_gpreferences(GTKCommand):
    """ GTK+ preferences dialog.

    """
    def run(self):
        self.open_display()
        from bzrlib.plugins.gtk.preferences import PreferencesWindow
        dialog = PreferencesWindow()
        dialog.run()


class cmd_gmissing(Command):
    """ GTK+ missing revisions dialog.

    """
    takes_args = ["other_branch?"]
    def run(self, other_branch=None):
        pygtk = import_pygtk()
        try:
            import gtk
        except RuntimeError, e:
            if str(e) == "could not open display":
                raise NoDisplayError

        from bzrlib.plugins.gtk.missing import MissingWindow
        from bzrlib.branch import Branch

        local_branch = Branch.open_containing(".")[0]
        if other_branch is None:
            other_branch = local_branch.get_parent()
            
            if other_branch is None:
                raise errors.BzrCommandError("No peer location known or specified.")
        remote_branch = Branch.open_containing(other_branch)[0]
        set_ui_factory()
        local_branch.lock_read()
        try:
            remote_branch.lock_read()
            try:
                dialog = MissingWindow(local_branch, remote_branch)
                dialog.run()
            finally:
                remote_branch.unlock()
        finally:
            local_branch.unlock()


class cmd_ginit(GTKCommand):
    def run(self):
        self.open_display()
        from initialize import InitDialog
        dialog = InitDialog(os.path.abspath(os.path.curdir))
        dialog.run()


class cmd_gtags(GTKCommand):
    def run(self):
        br = branch.Branch.open_containing('.')[0]
        
        gtk = self.open_display()
        from tags import TagsWindow
        window = TagsWindow(br)
        window.show()
        gtk.main()


commands = [
    cmd_gannotate, 
    cmd_gbranch,
    cmd_gcheckout, 
    cmd_gcommit, 
    cmd_gconflicts, 
    cmd_gdiff,
    cmd_ginit,
    cmd_gmissing, 
    cmd_gpreferences, 
    cmd_gpush, 
    cmd_gsend,
    cmd_gstatus,
    cmd_gtags,
    cmd_visualise
    ]

for cmd in commands:
    register_command(cmd)


class cmd_commit_notify(GTKCommand):
    """Run the bzr commit notifier.

    This is a background program which will pop up a notification on the users
    screen when a commit occurs.
    """

    def run(self):
        from notify import NotifyPopupMenu
        gtk = self.open_display()
        menu = NotifyPopupMenu()
        icon = gtk.status_icon_new_from_file(icon_path("bzr-icon-64.png"))
        icon.connect('popup-menu', menu.display)

        import cgi
        import dbus
        import dbus.service
        import pynotify
        from bzrlib.bzrdir import BzrDir
        from bzrlib import errors
        from bzrlib.osutils import format_date
        from bzrlib.transport import get_transport
        if getattr(dbus, 'version', (0,0,0)) >= (0,41,0):
            import dbus.glib
        from bzrlib.plugins.dbus import activity
        bus = dbus.SessionBus()
        # get the object so we can subscribe to callbacks from it.
        broadcast_service = bus.get_object(
            activity.Broadcast.DBUS_NAME,
            activity.Broadcast.DBUS_PATH)

        def catch_branch(revision_id, urls):
            # TODO: show all the urls, or perhaps choose the 'best'.
            url = urls[0]
            try:
                if isinstance(revision_id, unicode):
                    revision_id = revision_id.encode('utf8')
                transport = get_transport(url)
                a_dir = BzrDir.open_from_transport(transport)
                branch = a_dir.open_branch()
                revno = branch.revision_id_to_revno(revision_id)
                revision = branch.repository.get_revision(revision_id)
                summary = 'New revision %d in %s' % (revno, url)
                body  = 'Committer: %s\n' % revision.committer
                body += 'Date: %s\n' % format_date(revision.timestamp,
                    revision.timezone)
                body += '\n'
                body += revision.message
                body = cgi.escape(body)
                nw = pynotify.Notification(summary, body)
                def start_viz(notification=None, action=None, data=None):
                    """Start the viz program."""
                    pp = start_viz_window(branch, revision_id)
                    pp.show()
                def start_branch(notification=None, action=None, data=None):
                    """Start a Branch dialog"""
                    from bzrlib.plugins.gtk.branch import BranchDialog
                    bd = BranchDialog(remote_path=url)
                    bd.run()
                nw.add_action("inspect", "Inspect", start_viz, None)
                nw.add_action("branch", "Branch", start_branch, None)
                nw.set_timeout(5000)
                nw.show()
            except Exception, e:
                print e
                raise
        broadcast_service.connect_to_signal("Revision", catch_branch,
            dbus_interface=activity.Broadcast.DBUS_INTERFACE)
        pynotify.init("bzr commit-notify")
        gtk.main()

register_command(cmd_commit_notify)


class cmd_gselftest(GTKCommand):
    """Version of selftest that displays a notification at the end"""

    takes_args = builtins.cmd_selftest.takes_args
    takes_options = builtins.cmd_selftest.takes_options
    _see_also = ['selftest']

    def run(self, *args, **kwargs):
        import cgi
        import sys
        default_encoding = sys.getdefaultencoding()
        # prevent gtk from blowing up later
        gtk = import_pygtk()
        # prevent gtk from messing with default encoding
        import pynotify
        if sys.getdefaultencoding() != default_encoding:
            reload(sys)
            sys.setdefaultencoding(default_encoding)
        result = builtins.cmd_selftest().run(*args, **kwargs)
        if result == 0:
            summary = 'Success'
            body = 'Selftest succeeded in "%s"' % os.getcwd()
        if result == 1:
            summary = 'Failure'
            body = 'Selftest failed in "%s"' % os.getcwd()
        pynotify.init("bzr gselftest")
        note = pynotify.Notification(cgi.escape(summary), cgi.escape(body))
        note.set_timeout(pynotify.EXPIRES_NEVER)
        note.show()


register_command(cmd_gselftest)


class cmd_test_gtk(GTKCommand):
    """Version of selftest that just runs the gtk test suite."""

    takes_options = ['verbose',
                     Option('one', short_name='1',
                            help='Stop when one test fails.'),
                     Option('benchmark', help='Run the benchmarks.'),
                     Option('lsprof-timed',
                     help='Generate lsprof output for benchmarked'
                          ' sections of code.'),
                     Option('list-only',
                     help='List the tests instead of running them.'),
                     Option('randomize', type=str, argname="SEED",
                     help='Randomize the order of tests using the given'
                          ' seed or "now" for the current time.'),
                    ]
    takes_args = ['testspecs*']

    def run(self, verbose=None, one=False, benchmark=None,
            lsprof_timed=None, list_only=False, randomize=None,
            testspecs_list=None):
        from bzrlib import __path__ as bzrlib_path
        from bzrlib.tests import selftest

        print '%10s: %s' % ('bzrlib', bzrlib_path[0])
        if benchmark:
            print 'No benchmarks yet'
            return 3

            test_suite_factory = bench_suite
            if verbose is None:
                verbose = True
            # TODO: should possibly lock the history file...
            benchfile = open(".perf_history", "at", buffering=1)
        else:
            test_suite_factory = test_suite
            if verbose is None:
                verbose = False
            benchfile = None

        if testspecs_list is not None:
            pattern = '|'.join(testspecs_list)
        else:
            pattern = ".*"

        try:
            result = selftest(verbose=verbose,
                              pattern=pattern,
                              stop_on_failure=one,
                              test_suite_factory=test_suite_factory,
                              lsprof_timed=lsprof_timed,
                              bench_history=benchfile,
                              list_only=list_only,
                              random_seed=randomize,
                             )
        finally:
            if benchfile is not None:
                benchfile.close()

register_command(cmd_test_gtk)


class cmd_ghandle_patch(GTKCommand):
    """Display a patch or merge directive, possibly merging.

    This is a helper, meant to be launched from other programs like browsers
    or email clients.  Since these programs often do not allow parameters to
    be provided, a "handle-patch" script is included.
    """

    takes_args = ['path']

    def run(self, path):
        try:
            from bzrlib.plugins.gtk.diff import (DiffWindow,
                                                 MergeDirectiveWindow)
            lines = open(path, 'rb').readlines()
            lines = [l.replace('\r\n', '\n') for l in lines]
            try:
                directive = merge_directive.MergeDirective.from_lines(lines)
            except errors.NotAMergeDirective:
                window = DiffWindow()
                window.set_diff_text(path, lines)
            else:
                window = MergeDirectiveWindow(directive, path)
                window.set_diff_text(path, directive.patch.splitlines(True))
            window.show()
            gtk = self.open_display()
            window.connect("destroy", gtk.main_quit)
        except Exception, e:
            from dialog import error_dialog
            error_dialog('Error', str(e))
            raise
        gtk.main()


register_command(cmd_ghandle_patch)


import gettext
gettext.install('olive-gtk')


class NoDisplayError(BzrCommandError):
    """gtk could not find a proper display"""

    def __str__(self):
        return "No DISPLAY. Unable to run GTK+ application."


def test_suite():
    from unittest import TestSuite
    import tests
    import sys
    default_encoding = sys.getdefaultencoding()
    try:
        result = TestSuite()
        try:
            import_pygtk()
        except errors.BzrCommandError:
            return result
        result.addTest(tests.test_suite())
    finally:
        if sys.getdefaultencoding() != default_encoding:
            reload(sys)
            sys.setdefaultencoding(default_encoding)
    return result
