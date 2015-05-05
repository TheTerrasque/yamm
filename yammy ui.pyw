import Tkinter as tK

from lib import moddb
import webbrowser
import os
import urllib
from threading import Thread
from Queue import Queue
import logging
L = logging.getLogger("YAMM.YammiUI")

from lib.utils import get_filesize_display

mdb = moddb.ModDb()
DLDIR = "files/"

def show_mod_window(mod):
    top = tK.Toplevel()
    ModuleInfo(top, mod)

def download_modules(modulelist):
    top = tK.Toplevel()
    DownloadModules(top, modulelist)

def dlfile(queue):
    def handle_next_entry():
        mod, path, hook, active, completehook, overwrite =  queue.get()
        msg = ""
        
        def mahook(count, blocksize, totalsize):
            if count % 5 != 0:
                return
            dl = count * blocksize
            percent = int(( float(dl) / totalsize) * 100)
            hook(dl, totalsize, percent, active)
        
        if not overwrite and os.path.exists(path):
                msg = "[-o-]  %s - Already downloaded"
                if not mod.check_file(path, True):
                    msg = "[/o\]  %s - File is damaged"
        else:
            urllib.urlretrieve(mod.get_url(), path, mahook)
            msg = "[\o/]  %s - Completed"
        completehook(active, path, msg)
    
    while True:
        handle_next_entry()

DLQUEUE = Queue()
DLTHREADS = []
for x in range(2):
    DLTHREAD = Thread(target=dlfile, args = (DLQUEUE, ))
    DLTHREAD.daemon = True
    DLTHREAD.start()
    
class DownloadModules:
   
    def __init__(self, master, modlist):
        self.mods = modlist
        self.setup_widgets(master)
        self.master = master
        

        for mod in modlist:
            self.modsbox.insert(tK.END, "[00%%]   %-30s  (%s)" % (mod.mod.name, mod.mod.filesize and get_filesize_display(mod.mod.filesize) or "N/A"))
        
    def setup_widgets(self, master):
        master.title("Modules Download Window")
        master.minsize(width=400,  height=500)
        
        frame = tK.Frame(master)
        frame.pack(fill=tK.BOTH, expand=1)
        
        title = tK.Label(frame, text="Mods to download")
        title.pack(fill=tK.X)
        
        self.modsbox = tK.Listbox(frame)
        self.modsbox.pack(fill=tK.BOTH, expand=1)
        
        self.button_dl = tK.Button(frame, text="Start download", command=self.start_download)
        self.button_dl.pack(fill=tK.X)
    
    def set_line(self, lineno, value):
        self.modsbox.delete(lineno)
        self.modsbox.insert(lineno, value)
    
    def start_download(self):

        if not os.path.exists(DLDIR):
            os.mkdir(DLDIR)
        
        def minihook(dl, totalsize, percent, modnum):
            self.set_line(modnum, "[%02d%%]  %s  (%s/%s)" % (percent, self.mods[modnum].mod.name, get_filesize_display(dl), get_filesize_display(totalsize)))
            #print "\r  %s%% - %s kb / %s kb" % (percent, dlkb, totalkb),

        def completehook(active, path, message):
            self.set_line(active, message % self.mods[active].mod.name)

        for i, m in enumerate(self.mods):
            path = os.path.join(DLDIR, m.mod.filename)
            d = [m, path, minihook, i, completehook, False]
            DLQUEUE.put(d)

class ModuleInfo:
    
    def __init__(self, master, mod):
        self.mod = mod
        self.setup_widgets(master)

    def show_webpage(self, e):
        if self.mod.mod.homepage:
            webbrowser.open(self.mod.mod.homepage)
    
    def setup_widgets(self, master):
        master.title("Module %s" % self.mod.mod.name)
        frame = tK.Frame(master)
        frame.pack(fill=tK.BOTH, expand=1)
        
        title = tK.Label(frame, text="%s v%s" % (self.mod.mod.name, self.mod.mod.version))
        title.pack()
        
        description = tK.Text(frame)
        description.insert(tK.END, self.mod.mod.description)
        description.pack(expand=1, fill=tK.BOTH)
        
        if self.mod.mod.homepage:
            description.tag_config("homepage", underline=1)
            description.tag_bind("homepage", "<Button-1>", self.show_webpage)
            description.insert(tK.END, "\n\nHomepage: ")
            description.insert(tK.END, self.mod.mod.homepage, "homepage")
        
        def click(mod):
            def inner(ev):
                show_mod_window(mod)
            return inner
        
        description.tag_config("a", underline=1)
        description.tag_bind("a", "<Button-1>", click)
        description.config(cursor="arrow")
        
        dependslist = self.mod.get_dependency_mods()
        wantslist = self.mod.get_dependency_mods(3)
        for modlist, maintext in ( (dependslist, "Requires"), (wantslist, "Recommends")):
            if modlist["mods"]:
                #d = "Requires: %s" % ", ".join(x.mod.name for x in dependslist)
                description.insert(tK.END, "\n\n%s: \n  " % maintext)
                for m in modlist["mods"]:
                    tag = "a" + str(m.mod.id)
                    description.tag_config(tag, underline=1)
                    description.tag_bind(tag, "<Button-1>", click(m))
                    description.insert(tK.END, m.mod.name, tag)
                    description.insert(tK.END, ", ")
            
            if modlist["unknown"]:
                #d = "Requires: %s" % ", ".join(x.mod.name for x in dependslist)
                tag = "unk"
                description.tag_config(tag)
                description.insert(tK.END, m.mod.name, tag)
                
                description.insert(tK.END, "\n\n%s (Unknown): \n  " % maintext)
                for m in modlist["unknown"]:
                    description.insert(tK.END, m, tag)
                    description.insert(tK.END, ", ")
            
        description.config(state=tK.DISABLED, wrap=tK.WORD)
        
        dlbutton = tK.Button(frame, text="Download mods", command=self.start_download)
        dlbutton.pack(fill=tK.X)
    
    def start_download(self):
        download_modules([self.mod] + self.mod.get_dependency_mods())
        
class Search:
    modmap = []
    
    def __init__(self, master):
        self.setup_widgets(master)
        master.after(20,self.set_default_services)

    def setup_widgets_search(self, master):
        master.minsize(width=300,  height=500)
        
        frame = tK.Frame(master)
        frame.pack(fill=tK.X)

        self.entry_search = tK.Entry(frame)
        self.entry_search.pack(side=tK.LEFT, fill=tK.X)

        self.entry_search.bind("<Return>", self.do_search)

        self.button_search = tK.Button(frame, text="Search", command=self.do_search)
        self.button_search.pack(side=tK.LEFT)
        
        frame2 = tK.Frame(master)
        frame2.pack(fill=tK.BOTH, expand=1)
        
        self.modsbox = tK.Listbox(frame2)
        self.modsbox.pack(fill=tK.BOTH, expand=1)
        
        self.modsbox.bind("<Double-Button-1>", self.show_module)

    def setup_widgets(self, master):

        master.title("YAMMy UI")
        
        self.setup_widgets_search(master)

        frame = tK.Frame(master)
        frame.pack()
        
        button_update = tK.Button(frame, text="Update database", command=mdb.update_services)
        button_update.pack()

        self.status = tK.StringVar()
        status = tK.Label(master, text="", bd=1, relief=tK.SUNKEN, anchor=tK.W, textvariable=self.status)
        status.pack(side=tK.BOTTOM, fill=tK.X)
        
    # -------------------------------------------------

    def update_data(self, fetch=True):
        mdb.update_services()
        
        self.status.set("%s modules in database" % mdb.get_module_count())
        self.list_modules(mdb.get_modules_not_in_category("framework"))

    def list_modules(self, modulelist):
        self.modmap = modulelist
        self.modsbox.delete(0, tK.END)
        
        for mod in self.modmap:
            #show_mod_window(mod)
            self.modsbox.insert(tK.END, "%s  [%s]" % (mod.mod.name, mod.mod.category or "no category"))

    def set_default_services(self):
        if not mdb.get_services().count():
            self.status.set("Doing initial setup..")
            mdb.add_service("http://terra.thelazy.net/yamm/mods.json")
            self.update_data()
        else:
            self.update_data(False)
        
    def show_module(self, e):
        for index in self.modsbox.curselection():
            show_mod_window(self.modmap[index])

    def do_search(self, e=None):
        q = self.entry_search.get()
        modmap = mdb.search(q)
        self.list_modules(modmap)
        self.status.set("%s result(s) found" % len(modmap))
        
def main():
    root = tK.Tk()
    app = Search(root)
    root.mainloop()
    root.destroy()

if __name__ == "__main__":
    main()
