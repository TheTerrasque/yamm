## downloadID = self.__organizer.downloadManager().startDownloadURLs(url_list_for_file)
## i*.h from http://sourceforge.net/p/modorganizer/code/ci/default/tree/source/uibase/

##
# Tannin @ http://forum.step-project.com/topic/4909-mod-organizer-automation/
# You probably don't want to read the source code. What you want is the headers in uibase starting with an I.
# Those are the interface classes and most have been exported in some way to python. The python class mobase.IPluginInstallerCustom
# corresponds to the C++ interface IPluginInstallerCustom found in iplugininstallercustom.h IPluginInstallerCustom derives from
# IPluginInstaller (in iplugininstaller.h) which derives from IPlugin (in - surprise! - iplugin.h) Your plugin has to implement the
# member functions declared "virtual" from each interface.
##

# http://sourceforge.net/p/modorganizer/code/ci/7a98e2c0541bdda56b7d2a5bd0549bb5005b3e4c/

# qt5
from PyQt5 import QtGui
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMessageBox

if "mobase" not in sys.modules:
    import mock_mobase as mobase
    
import logging
import os

import json
import mmap
import tempfile

L = logging.getLogger("YAMM.YammMOshim")

MMSIZE=16384
VERSION = 2

class RpcFunctionMMAP(object):
    _OLD = ""
    
    def __init__(self, organizer, filename="yamm_mo_rpc"):
        self._organizer = organizer
        self._fn = filename
        self._setup_rpc()
        
    def _setup_rpc(self):
        self._filename = os.path.join(tempfile.gettempdir(), self._fn)

        if not os.path.exists(self._filename):
            with open(self._filename, "wb") as f:
                f.write("Hello Python!\n")

        fn = open(self._filename, "r+")
        self._mmap = mmap.mmap(fn.fileno(), MMSIZE)
    
    def _poll(self):
        data = self._read()
        if data != self._OLD:
            result = self._handle_call(data)
            self._write(result)
        
    def _write(self, data):
        self._mmap.seek(0)
        tval = data + (" " * MMSIZE)
        tval = tval[:MMSIZE]
        self._mmap.write(tval)
        self._OLD = tval
    
    def _handle_call(self, data):
        try:
            jdata = json.loads(data)
            funcname = jdata["function"]
            kwargs = jdata.get("kwargs", {})
            args = jdata.get("args", [])
            result = getattr(self, funcname)(*args, **kwargs)
            jr = json.dumps({"result": result})
        except Exception as e:
            jr = json.dumps({
                "result": "ERROR",
                "error": "An error happened",
                "details": unicode(e)
            })
        return jr
        
    def _read(self):
        self._mmap.seek(0)
        val = self._mmap.read(MMSIZE).strip()
        return val

    def __del__(self):
        self._mmap.close()
        os.unlink(self._filename)

class RpcFunction(RpcFunctionMMAP):
    
    def version(self):
        "Return plugin version"
        return VERSION
    
    def get_mo_version(self):
        return [int(x) for x in self._organizer.appVersion().canonicalString().split(".")]
    
    def get_gamename(self):
        "Return name of active game"
        return str(self._organizer.gameInfo().type())
    
    def get_debug(self):
        # organizer / mobase : http://sourceforge.net/p/modorganizer/code/ci/default/tree/source/uibase/imoinfo.h
        return "Mobase: %s \n\nOrganizer: %s" % (str(dir(mobase)), str(dir(self._organizer)))
    
    def get_active_profile(self):
        return self._organizer.profileName()
    
    def install_mod(self, path, name=None, version=None):
        # Modinstance : http://sourceforge.net/p/modorganizer/code/ci/default/tree/source/uibase/imodinterface.h
        if name:
            modinstance = self._organizer.installMod(str(path), str(name))
        else:
            modinstance = self._organizer.installMod(str(path))
        if modinstance:
            return unicode(modinstance.name())

    def set_active(self, modname, state=True):
        # http://sourceforge.net/p/modorganizer/code/ci/default/tree/source/uibase/imodlist.h
        self._organizer.modList().setActive(str(modname), state)
    
    def get_mods(self):
        # http://sourceforge.net/p/modorganizer/code/ci/default/tree/source/uibase/imodlist.h
        modlist = self._organizer.modList().allMods()
        l = []
        for modname in modlist:
            modstate = self._organizer.modList().state(str(modname))
            mod = {
                "name": modname,
                "state": modstate,
                "active": bool(modstate & 0x2),
                "valid": bool(modstate & 0x20),
                "endorsed": bool(modstate & 0x10),
                "essential": bool(modstate & 0x4),
                "empty": bool(modstate & 0x8),
            }
            l.append(mod)
        return l
        

RPC=None
        
class IniEdit(mobase.IPluginTool):

    def __init__(self):
        super(IniEdit, self).__init__()
        self.__organizer = None
        self.__window = None
        self.__settings = None
        self.__parentWidget = None

    def init(self, organizer):
        import pyCfgResource_rc  # required to make icons available
        self.__organizer = organizer
        self.__window = None
        #start_rpc_thread(organizer)
        
        global RPC
        if not RPC:
            RPC = RpcFunction(organizer)
            self.rpc_poll_timer = QTimer()
            self.rpc_poll_timer.timeout.connect(RPC._poll)
            self.rpc_poll_timer.start(20)
        
        return True

    def name(self):
        return "YAMM Client"

    def author(self):
        return "Terrasque"

    def description(self):
        return "Installs mods and doesn't afraid of anything"

    def version(self):
        return mobase.VersionInfo(1, 0, VERSION, mobase.ReleaseType.final)

    def isActive(self):
        return True

    def settings(self):
        return []

    def displayName(self):
        return "YAMM Client"

    def tooltip(self):
        return "Downloads mods and doesn't afraid of anything"

    def icon(self):
        return QtGui.QIcon(":/pyCfg/pycfgicon")

    def setParentWidget(self, widget):
        self.__parentWidget = widget

    def display(self):
        QMessageBox.information(self.__parentWidget, "Plugin running", "YAMM plugin is running!\n\nMMAP file path used:\n%s" % RPC._filename)
        #self.__window = RpcWindow(self.__organizer)
        #self.__window.exec_()
        
def createPlugin():
    return IniEdit()