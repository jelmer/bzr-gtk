# Simple TortoiseSVN-like Bazaar plugin for the Windows Shell
# Published under the GNU GPL, v2 or later.
# Copyright (C) 2007 Jelmer Vernooij <jelmer@samba.org>

import pythoncom
from win32com.shell import shell, shellcon
import win32gui
import win32con

"""Windows shell extension that adds context menu items to Bazaar branches."""
class BazaarShellExtension:
    _reg_progid_ = "Bazaar.ShellExtension.ContextMenu"
    _reg_desc_ = "Bazaar Shell Extension"
    _reg_clsid_ = "{EEE9936B-73ED-4D45-80C9-AF918354F885}"
    _com_interfaces_ = [shell.IID_IShellExtInit, shell.IID_IContextMenu]
    _public_methods_ = [
    	"Initialize", # From IShellExtInit
	"QueryContextMenu", "InvokeCommand", "GetCommandString" # IContextMenu
	]

    def Initialize(self, folder, dataobj, hkey):
        self.dataobj = dataobj

    def QueryContextMenu(self, hMenu, indexMenu, idCmdFirst, idCmdLast, uFlags):
        format_etc = win32con.CF_HDROP, None, 1, -1, pythoncom.TYMED_HGLOBAL
        sm = self.dataobj.GetData(format_etc)
        num_files = shell.DragQueryFile(sm.data_handle, -1)
        if num_files>1:
            msg = "&Hello from Python (with %d files selected)" % num_files
        else:
            fname = shell.DragQueryFile(sm.data_handle, 0)
            msg = "&Hello from Python (with '%s' selected)" % fname
        idCmd = idCmdFirst
        items = []
        if (uFlags & 0x000F) == shellcon.CMF_NORMAL: # Check == here, since CMF_NORMAL=0
            print "CMF_NORMAL..."
            items.append(msg)
        elif uFlags & shellcon.CMF_VERBSONLY:
            print "CMF_VERBSONLY..."
            items.append(msg + " - shortcut")
        elif uFlags & shellcon.CMF_EXPLORE:
            print "CMF_EXPLORE..."
            items.append(msg + " - normal file, right-click in Explorer")
        elif uFlags & CMF_DEFAULTONLY:
            print "CMF_DEFAULTONLY...\r\n"
        else:
            print "** unknown flags", uFlags
        win32gui.InsertMenu(hMenu, indexMenu,
                            win32con.MF_SEPARATOR|win32con.MF_BYPOSITION,
                            0, None)
        indexMenu += 1
        for item in items:
            win32gui.InsertMenu(hMenu, indexMenu,
                                win32con.MF_STRING|win32con.MF_BYPOSITION,
                                idCmd, item)
            indexMenu += 1
            idCmd += 1

        win32gui.InsertMenu(hMenu, indexMenu,
                            win32con.MF_SEPARATOR|win32con.MF_BYPOSITION,
                            0, None)
        indexMenu += 1
        return idCmd-idCmdFirst # Must return number of menu items we added.

    def InvokeCommand(self, ci):
        mask, hwnd, verb, params, dir, nShow, hotkey, hicon = ci
	# FIXME: Run the actual command

    def GetCommandString(self, cmd, typ):
        return "Hello from Python!!"

registryKeys = [
	"*\\shellex\\ContextMenuHandlers", 
	"Directory\\Background\\shellex\\ContextMenuHandlers", 
	"Directory\\shellex\\ContextMenuHandlers", 
	"Folder\\shellex\\ContextmenuHandlers"
	]

def DllRegisterServer():
    import _winreg
    for keyname in registryKeys: 
	    key = _winreg.CreateKey(_winreg.HKEY_CLASSES_ROOT, keyname)
	    subkey = _winreg.CreateKey(key, "TortoiseBzr")
	    _winreg.SetValueEx(subkey, None, 0, _winreg.REG_SZ, BazaarShellExtension._reg_clsid_)
	    _winreg.CloseKey(subkey)
	    _winreg.CloseKey(key)

    print BazaarShellExtension._reg_desc_, "registration complete."

def DllUnregisterServer():
    import _winreg
    try:
	for keyname in registryKeys:
	    _winreg.DeleteKey(_winreg.HKEY_CLASSES_ROOT,
                                "%s\\TortoiseBzr" % keyname)
    except WindowsError, details:
        import errno
        if details.errno != errno.ENOENT:
            raise
    print BazaarShellExtension._reg_desc_, "unregistration complete."

if __name__ == '__main__':
    from win32com.server import register
    register.UseCommandLine(BazaarShellExtension,
                   finalize_register = DllRegisterServer,
                   finalize_unregister = DllUnregisterServer)
