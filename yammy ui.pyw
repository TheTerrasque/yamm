import Tkinter as tK
from lib.gui_components import initialize_uimodules, Search

from lib import moddb

mdb = moddb.ModDb()
DLDIR = "files/"

import logging
L = logging.getLogger("YAMM.YammiUI")

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
