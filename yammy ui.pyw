import Tkinter as tK
ROOT = tK.Tk()

class Loader:
    def __init__(self, root):
        self.root = root
        self.show()
        
    def show(self):  
        self.top = tK.Toplevel()
        self.top.overrideredirect(1)

        frame = tK.Frame(self.top)
        frame.pack(fill=tK.BOTH, expand=1)
        tK.Label(frame, text="Loading YAMM..", font=("Helvetica", 32), padx=10, pady=10, relief=tK.RAISED).pack(fill=tK.X)
        
        width = 200
        height = 50
        scrnWt = (self.root.winfo_screenwidth() /2) - (width / 2)
        scrnHt = (self.root.winfo_screenheight()/2) - (height / 2)
        self.top.geometry( '+%d+%d' % (scrnWt, scrnHt) )

        self.root.withdraw()        
        self.top.update( )

    def exit(self):
        self.root.deiconify()
        self.top.destroy()

LOADER = Loader(ROOT)

import logging
from lib.utils import get_config_path, os

logfile = os.path.join(get_config_path(), "yamm_ui.log")

logging.basicConfig(filename=logfile, filemode="w")

from lib.gui_components import initialize_uimodules, Search, open_window, DownloadModules, CALLBACK, tkMessageBox, Setup

from lib import moddb
import os.path

import argparse

mdb = moddb.ModDb()

DLDIR = os.path.join(get_config_path(), "files")

L = logging.getLogger("YAMM.YammiUI")

#CALLBACK["downloadmod"] = lambda modlist: open_window(DownloadModules, [modlist, DLDIR])


def handle_url_schema(url):
    result = None
    
    def add_a_service(url, pre=""):
        if mdb.get_services().filter(url=url).count():
            #if not pre:
            #    tkMessageBox.showinfo("Already added", "Service is already in database")
            return
        if tkMessageBox.askyesno("Add service", "%sDo you want to add this service? \n\n%s" % (pre, url), parent=ROOT):
            service, suggests = mdb.add_service(url)
            for suggest in suggests:
                preinfo = "'%s' suggests you should also add this service.\n\n" % service.name
                add_a_service(suggest, preinfo)
            return True
        
    command, value = url.split(":", 1)
    if command == "service":
        if add_a_service(value):
            mdb.update_services()
        
    if command == "mod":            
        result = mdb.get_module(value)
        if not result:
            tkMessageBox.showerror("Could not find mod", "Could not find the mod '%s' in the database." % value)
    return result

def main(mod=None):
    initialize_uimodules()
    
    app = Search(ROOT, mdb)
    
    if mod:
        CALLBACK["showmod"](mod)
    
    ROOT.mainloop()
    
    # Usually the root is already destroyed by now (X button to close window)
    try:
        ROOT.destroy()
    except:
        pass

def cmd_args():
    parser = argparse.ArgumentParser(description='YAMM ui module')

    parser.add_argument('--url', help='URL scheme handling')
    parser.add_argument('--setup', help='Handle setup. Needs elevated access', action="store_true")
    
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = cmd_args()
    mod = None
    LOADER.exit()
    
    if args.setup:
        app = Setup(ROOT)
        ROOT.mainloop()
    else:
        if args.url:
            
            try:
                schema, data = args.url.split(":", 1)
                if schema == "yamm":
                    for val in data.split("|"):
                        mod = handle_url_schema(val)
            except:
                L.exception("Could not handle url %s", args.url)
                
        main(mod)
