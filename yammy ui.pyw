import Tkinter as tK

from lib import moddb
import webbrowser
import os
import urllib
from threading import Thread
from Queue import Queue

mdb = moddb.ModDb()
DLDIR = "files/"

def show_mod_window(mod):
    top = tK.Toplevel()
    ModuleInfo(top, mod)

def download_modules(modulelist):
    top = tK.Toplevel()
    DownloadModules(top, modulelist)
    
class DownloadModules:
   
    
    def __init__(self, master, modlist):
        self.mods = modlist
        self.setup_widgets(master)
        
        self.DLQUEUE = Queue()
        
        self.DLTHREAD = Thread(target=dlfile, args = (self.DLQUEUE, ))
        self.DLTHREAD.daemon = True
        self.DLTHREAD.start()
        
        for mod in modlist:
            self.modsbox.insert(tK.END, "[00%%]   %-30s  (%s)" % (mod.mod.name, mod.mod.filesize or "N/A"))
        
    def setup_widgets(self, master):
        master.title("Module Download")
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
        
        def minihook(dl, totalsize, percent, modnum):
            dlkb = dl / 1024
            totalkb = totalsize / 1024
            self.set_line(modnum, "[%02d%%]  %s  (%skb/%skb)" % (percent, self.mods[modnum].mod.name, dlkb, totalkb))
            #print "\r  %s%% - %s kb / %s kb" % (percent, dlkb, totalkb),

        def completehook(active):
            self.set_line(active, "[\o/]  %s - Completed" % (self.mods[active].mod.name))
            if not self.mods[active].check_file(path, True):
                self.set_line(active, "[/o\]  %s - %s" % (m.mod.name, "File is damaged"))

        if not os.path.exists(DLDIR):
            print "Creating download folder '%s'" % DLDIR
            os.mkdir(DLDIR)
            
        for i, m in enumerate(self.mods):
            
            path = os.path.join(DLDIR, m.mod.filename)
            #print " Downloading %s [%s/%s]" % (m.mod.name, i+1, len(self.mods))
            
            if os.path.exists(path):
                self.set_line(i, "[-o-]  %s - %s" % (m.mod.name, "Already downloaded"))
                if not m.check_file(path, True):
                    self.set_line(i, "[/o\]  %s - %s" % (m.mod.name, "File is damaged"))
            else:
                d = [m.get_url(), path, minihook, i, completehook]
                self.DLQUEUE.put(d)

def dlfile(queue):
    while True:
        url, path, hook, active, endhook =  queue.get()
        
        def mahook(count, blocksize, totalsize):
            if count % 5 != 0:
                return
            dl = count * blocksize
            percent = int(( float(dl) / totalsize) * 100)
            hook(dl, totalsize, percent, active)
            
        urllib.urlretrieve(url, path, mahook)
        endhook(active)

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
        frame.pack(fill=tK.BOTH)
        
        title = tK.Label(frame, text="%s v%s" % (self.mod.mod.name, self.mod.mod.version))
        title.pack()
        
        description = tK.Text(frame)
        description.insert(tK.END, self.mod.mod.description)
        description.pack()
        
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
    
        if dependslist:
            #d = "Requires: %s" % ", ".join(x.mod.name for x in dependslist)
            description.insert(tK.END, "\n\nRequires: " )
            for m in dependslist:
                tag = "a" + str(m.mod.id)
                description.tag_config(tag, underline=1)
                description.tag_bind(tag, "<Button-1>", click(m))
                description.insert(tK.END, m.mod.name, tag)
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
