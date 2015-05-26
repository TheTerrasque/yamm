import Tkinter as tK
import logging
from lib.utils import get_base_path, os

logfile = os.path.join(get_base_path(), "ui.log")

logging.basicConfig(filename=logfile, filemode="w")

from lib.gui_components import initialize_uimodules, Search, open_window, DownloadModules, CALLBACK, tkMessageBox

from lib import moddb
import os.path

import argparse

mdb = moddb.ModDb()

DLDIR = os.path.join(get_base_path(), "files")

L = logging.getLogger("YAMM.YammiUI")

CALLBACK["downloadmod"] = lambda modlist: open_window(DownloadModules, [modlist, DLDIR])

L.debug("Download directory: %s", DLDIR)

def handle_url_schema(url):
    print url
    root = tK.Tk()
    root.withdraw()
    result = None
    
    schema, command, value = url.split(":", 2)
    if command == "service":
        if tkMessageBox.askyesno("Add service", "Do you want to add this service? \n\n%s" % value):
            mdb.add_service(value)

    if command == "mod":
        result = mdb.get_module(value)
        if not result:
            tkMessageBox.showerror("Could not find mod", "Could not find the mod '%s' in the database." % value)

    root.destroy()
    return result

def main(mod=None):    
    initialize_uimodules()
    root = tK.Tk()
    
    app = Search(root, mdb)
    
    if mod:
        CALLBACK["showmod"](mod)
    
    root.mainloop()
    
    # Usually the root is already destroyed by now (X button to close window)
    try:
        root.destroy()
    except:
        pass

def cmd_args():
    parser = argparse.ArgumentParser(description='YAMM ui module')

    parser.add_argument('--url', help='URL scheme handling')
    
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = cmd_args()
    mod = None
    
    if args.url:
        try:
            mod = handle_url_schema(args.url)
        except:
            L.exception("Could not handle url %s", args.url)
            
    main(mod)
