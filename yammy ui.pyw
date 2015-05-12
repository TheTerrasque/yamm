import Tkinter as tK
from lib.gui_components import initialize_uimodules, Search, open_window, DownloadModules, CALLBACK
from lib.utils import get_base_path
from lib import moddb
import os.path

mdb = moddb.ModDb()

DLDIR = os.path.join(get_base_path(), "files")

import logging
L = logging.getLogger("YAMM.YammiUI")

CALLBACK["downloadmod"] = lambda modlist: open_window(DownloadModules, [modlist, DLDIR])

L.debug("Download directory: %s", DLDIR)

def main():    
    initialize_uimodules()
    
    root = tK.Tk()
    app = Search(root, mdb)
    root.mainloop()
    
    # Usually the root is already destroyed by now (X button to close window)
    try:
        root.destroy()
    except:
        pass

if __name__ == "__main__":
    main()
