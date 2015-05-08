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

# qt5
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, pyqtWrapperType, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QDialog, QHeaderView, QMessageBox, QColorDialog, QTreeWidgetItem,\
    QComboBox, QPushButton, QDoubleSpinBox, QHBoxLayout, QWidget, QSlider, QSpinBox, QLineEdit

if "mobase" not in sys.modules:
    import mock_mobase as mobase
    
import threading
import logging

import json
import time
import mmap

L = logging.getLogger("YAMM.YammMOshim")

def start_rpc(organizer):
    filename = r"C:\\Users\\Mikael\\yamm_mo_rpc"
    size=16384
    
    class RpcFunctions:
        def echo(self):
            return "Hello"
        
        def get_gamename(self):
            return str(organizer.gameInfo().type())

    funcs = RpcFunctions()
    
    def handle_data(data):
        try:
            jdata = json.loads(data)
            funcname = jdata["function"]
            kwargs = jdata.get("kwargs", {})
            args = jdata.get("args", [])
            result = getattr(funcs, funcname)(*args, **kwargs)
            jr = json.dumps({"result": result})
        except:
            jr = json.dumps({
                "result": "ERROR",
                "error": "An error happened"
            })
        return jr
            
    
    with open(filename, "wb") as f:
        f.write("Hello Python!\n")
    
    fn = open(filename, "r+")
    data = mmap.mmap(fn.fileno(), size)
    oldval = ""
    
    while True:
        data.seek(0)
        val = data.read(size)
        
        if val != oldval:
            val = handle_data(val)
            data.seek(0)
            tval = val + (" " * size)
            tval = tval[:size]
            data.write(tval)
            oldval = tval
        time.sleep(0.1)

DEBUG = False

def start_rpc_thread(organizer):
    t = threading.Thread(target=start_rpc, args=[organizer])
    t.daemon = True
    t.start()
    return t

if DEBUG:
    start_rpc(None)

class RpcWindow(QDialog):
    saveSettings = pyqtSignal(dict)

    def __init__(self,  settings,  parent=None):
        super(RpcWindow,  self).__init__(parent)
        
        self.__organizer = settings
        start_rpc_thread(settings)
        
        from pyCfgDialog import Ui_PyCfgDialog

        self.__ui = Ui_PyCfgDialog()
        self.__ui.setupUi(self)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.__lastSelectedCategory = ""

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
        start_rpc_thread(organizer)
        return True

    def name(self):
        return "YAMMClient"

    def author(self):
        return "Terrasque"

    def description(self):
        return "Installs mods and doesn't afraid of anything"

    def version(self):
        return mobase.VersionInfo(1, 0, 0, mobase.ReleaseType.final)

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
        self.__window = RpcWindow(self.__organizer)
        self.__window.exec_()
        
def createPlugin():
    return IniEdit()