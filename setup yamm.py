import os
import _winreg as winreg
from lib.utils import get_base_path

def setup_registry():
    python = r"C:\Python27\pythonw.exe"
    this = os.path.join(get_base_path(), "yammy ui.pyw")
    
    if not os.path.exists(python):
        L.info("Could not find python at %s", python)
        return
    
    yamm = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, r"yamm")
    
    winreg.SetValueEx(yamm, "URL Protocol", 0, winreg.REG_SZ, "")
    winreg.SetValue(yamm, "", winreg.REG_SZ, "URL:yamm")
    
    yamm_cmd = winreg.CreateKey(yamm, r"shell\open\command")
    winreg.SetValue(yamm_cmd, "", winreg.REG_SZ, '"%s" "%s" "--url" "%%1"' %(python, this))
    
    winreg.CloseKey(yamm_cmd)
    winreg.CloseKey(yamm)
    
    print "URL Handler installed"

if __name__ == "__main__":
    setup_registry()