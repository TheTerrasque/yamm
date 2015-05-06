import Tkinter as tK
from lib.gui_components import initialize_uimodules, Search

from lib import moddb

mdb = moddb.ModDb()
DLDIR = "files/"

import logging
L = logging.getLogger("YAMM.YammiUI")

def main():    
    root = tK.Tk()
    initialize_uimodules()
    app = Search(root, mdb)
    root.mainloop()
    try:
        root.destroy()
    except:
        pass

if __name__ == "__main__":
    main()
