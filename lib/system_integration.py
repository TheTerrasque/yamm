import os
import _winreg as winreg
from lib.utils import get_base_path
import shutil

def setup_registry():
    python = r"C:\Python27\pythonw.exe"
    this = os.path.join(get_base_path(), "yammy ui.pyw")
    
    if not os.path.exists(python):
        return
    
    yamm = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, r"yamm")
    
    winreg.SetValueEx(yamm, "URL Protocol", 0, winreg.REG_SZ, "")
    winreg.SetValue(yamm, "", winreg.REG_SZ, "URL:yamm")
    
    yamm_cmd = winreg.CreateKey(yamm, r"shell\open\command")
    winreg.SetValue(yamm_cmd, "", winreg.REG_SZ, '"%s" "%s" "--url" "%%1"' %(python, this))
    
    winreg.CloseKey(yamm_cmd)
    winreg.CloseKey(yamm)
    
    return True

def setup_modorganizer(path = None):
    exe = "ModOrganizer.exe"
    script = "plugin_MO.py"
    src = os.path.join(get_base_path(), "utils", script)
    
    def install(path):
        target = os.path.join(path, "plugins", script)
        shutil.copyfile(src, target)
    
    paths = [
        r"C:\Program Files (x86)\Mod Organizer",
        r"C:\Program Files\Mod Organizer",
    ]
   
    if path:
        paths.append(path)
    
    for path in paths:
        full = os.path.join(path, exe)
        if os.path.exists(full):
            install(path)
            return True
            
if __name__ == "__main__":
    print "Starting setup of YAMM\n\n"
    try:
        setup_registry()
        print ""
        setup_modorganizer()
    except Exception as e:
        print e
    raw_input("\nInstall finished")