import Tkinter as tK
import tkMessageBox
import tkSimpleDialog
from .utils import get_filesize_display
import os
from .thread_workers import start_download_threads
import webbrowser

import mo_rpc

import logging
L = logging.getLogger("YAMM.YammiUI.TK")


def open_window(module, data):
    top = tK.Toplevel()
    module(top, *data)
    return module

CALLBACK = {
    "showmod": lambda mod: open_window(ModuleInfo, [mod]),
    "downloadmod": lambda modlist: open_window(DownloadModules, [modlist]),
    "services": lambda mdb: open_window(ServiceList, [mdb]),
    "download_complete": lambda mod: mod,
}

DLQUEUE = None

def initialize_uimodules():
    global DLQUEUE
    DLQUEUE = start_download_threads()


class ServiceList:
    def __init__(self, master, mdb):
        self.mdb = mdb
        self.master = master
        self.setup_widgets(master)
        self.show_services()

    def setup_widgets(self, master):
        master.title("YAMM Services")
        master.minsize(width=300,  height=500)

        frame = tK.Frame(master)
        frame.pack(fill=tK.BOTH, expand=1)
        
        title = tK.Label(frame, text="Active services")
        title.pack(fill=tK.X)
        
        self.servicebox = tK.Listbox(frame)
        self.servicebox.pack(fill=tK.BOTH, expand=1)
        
        tK.Button(frame, text="Add service", command=self.add_service).pack(side=tK.LEFT)
        tK.Button(frame, text="Remove service", command=self.remove_service).pack(side=tK.LEFT)
        

    def add_service(self):
        service = tkSimpleDialog.askstring("Add service", "Service URL", parent=self.master)
        if service:
            try:
                self.mdb.add_service(service)
            except Exception as e:
                tkMessageBox.showerror("Problem adding service", u"Could not add service! \n\nError: %s" % unicode(e))
            self.show_services()
        #tkMessageBox.showinfo("Not implemented", "Not implemented yet. \nPlease use command line client yamm.py to add a service")
    
    def remove_service(self):
        for index in self.servicebox.curselection():
            service = self.services[index]
            if tkMessageBox.askyesno("Remove service", "Are you sure you want to remove the service '%s'?" % service.name):
                service.delete()
                break
        self.show_services()

    def show_services(self):
        self.servicebox.delete(0, tK.END)
        self.services = self.mdb.get_services()
        
        for service in self.services:
            #show_mod_window(mod)
            self.servicebox.insert(tK.END, service.name)

    
class DownloadModules:
   
    def __init__(self, master, modlist, downloaddir="files/"):
        self.downloaddir = downloaddir
        self.mods = modlist
        self.setup_widgets(master)
        self.master = master

        for mod in self.mods:
            self.modsbox.insert(tK.END, "[00%%]   %-30s ( %s )" % (mod.mod.name, mod.mod.filesize and get_filesize_display(mod.mod.filesize) or "N/A"))
        
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
    
        v = tK.IntVar()
        self.mo_checkbox = tK.Checkbutton(frame, text="Install in Mod Organizer after download", var=v, command=self.check_mo)
        self.mo_checkbox.var = v
        self.mo_checkbox.pack(fill=tK.X)
    
    def check_mo(self):
        if self.mo_checkbox.var.get() and not mo_rpc.ping():
            tkMessageBox.showerror("Connection error","Could not connect to Mod Organizer\n\nMake sure it's running and that the YAMM plugin is installed")
            self.mo_checkbox.deselect()
    
    def set_line(self, lineno, value):
        self.modsbox.delete(lineno)
        self.modsbox.insert(lineno, value)
    
    def ui_create_dl_entry(self, parent, mod):
        class ModDlEntry:
            def __init__(self, parent, mod):
                self.parent = parent
                self.mod = mod
                
            def create_widgets(self):
                frame = tK.Frame(self.parent)
                frame.pack(fill=tK.X)
                
                # Add checkbox
                # Add relation
                # Add torrent toggle
                # Add MO button
                
                # [X] | [95%] | BlaMod | Downloading | Required | 200MB | [x] Torrent | [Install in MO]
                
                self.ministatus = tK.Label(frame, text="[-o-]")
                self.ministatus.pack(side=tK.LEFT)
                
                self.name = tK.Label(frame, text="%s" % self.mod.mod.name)
                self.name.pack(side=tK.LEFT)
            
                self.status = tK.Label(frame, text="%s" % self.mod.mod.name)
                self.status.pack(side=tK.LEFT)
    
        r = ModDlEntry(parent, mod)
        return r
    
    def start_download(self):
        if not DLQUEUE:
            print "ERROR! QUEUE NOT CREATED!"
            
        if not os.path.exists(self.downloaddir):
            os.mkdir(self.downloaddir)
        
        def minihook(dl, totalsize, percent, modnum):
            self.set_line(modnum, "[%02d%%]  %-30s ( %s / %s )" % (percent, self.mods[modnum].mod.name, get_filesize_display(dl), get_filesize_display(totalsize)))
            #print "\r  %s%% - %s kb / %s kb" % (percent, dlkb, totalkb),

        def completehook(active, path, message):
            self.set_line(active, message % self.mods[active].mod.name)
            
            if self.mo_checkbox.var.get() and mo_rpc.ping():
                mo_rpc.rpc.install_mod(path)

        for i, m in enumerate(self.mods):
            path = os.path.join(self.downloaddir, m.mod.filename)
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
                CALLBACK["showmod"](mod)
            return inner
        
        description.tag_config("a", underline=1)
        description.tag_bind("a", "<Button-1>", click)
        description.config(cursor="arrow")
        
        deps, recommends = self.get_modlist()
        
        for modlist, maintext in ( (deps, "Requires"), (recommends, "Recommends")):
            if modlist:
                #d = "Requires: %s" % ", ".join(x.mod.name for x in dependslist)
                description.insert(tK.END, "\n\n%s: \n  " % maintext)
                
                unknown = "unk"
                description.tag_config(unknown)
                
                for tag, m in modlist:
                    if m:
                        tag = "a" + str(m.mod.id)
                        description.tag_config(tag, underline=1)
                        description.tag_bind(tag, "<Button-1>", click(m))
                        description.insert(tK.END, m.mod.name, tag)
                        description.insert(tK.END, ", ")
                    else:          
                        description.insert(tK.END, tag+"?", unknown)
                        description.insert(tK.END, ", ")
            
        description.config(state=tK.DISABLED, wrap=tK.WORD)
        
        dlbutton = tK.Button(frame, text="Download mods", command=self.start_download)
        dlbutton.pack(fill=tK.X)
    
    def get_modlist(self):
        depslist = self.mod.get_dependencies().dependencies
        deps = [(k, x.get_provider()) for k, x in depslist.items() if x.required_by]
        recommends = [(k, x.get_provider()) for k, x in depslist.items() if x.recommended_by]
        return [deps, recommends]
    
    def start_download(self):
        modlist = self.get_modlist()[0]
        dlmods = [self.mod] + [x[1] for x in modlist if x[1]]
        CALLBACK["downloadmod"](dlmods)

         
class Search:
    modmap = []
    
    def __init__(self, master, mod_db):
        self.mod_db = mod_db
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
        
        self.button_search = tK.Button(frame, text="Services", command=self.show_services)
        self.button_search.pack(side=tK.LEFT)
        
        frame2 = tK.Frame(master)
        frame2.pack(fill=tK.BOTH, expand=1)
        
        self.modsbox = tK.Listbox(frame2)
        self.modsbox.pack(fill=tK.BOTH, expand=1)
        
        self.modsbox.bind("<Double-Button-1>", self.show_module)

    def show_services(self):
        CALLBACK["services"](self.mod_db)
    
    def setup_widgets(self, master):

        master.title("YAMMy UI")
        
        self.setup_widgets_search(master)

        frame = tK.Frame(master)
        frame.pack()
        
        button_update = tK.Button(frame, text="Update database", command=self.mod_db.update_services)
        button_update.pack()

        self.status = tK.StringVar()
        status = tK.Label(master, text="", bd=1, relief=tK.SUNKEN, anchor=tK.W, textvariable=self.status)
        status.pack(side=tK.BOTTOM, fill=tK.X)
        
    # -------------------------------------------------

    def update_data(self, fetch=True):
        self.mod_db.update_services()
        self.status.set("%s modules in database" % self.mod_db.get_module_count())
        self.list_modules(self.mod_db.get_modules_not_in_category("framework"))

    def list_modules(self, modulelist):
        self.modmap = modulelist
        self.modsbox.delete(0, tK.END)
        
        for mod in self.modmap:
            #show_mod_window(mod)
            self.modsbox.insert(tK.END, "%s  [%s]" % (mod.mod.name, mod.mod.category or "no category"))

    def set_default_services(self):
        if not self.mod_db.get_services().count():
            self.status.set("Doing initial setup..")
            self.mod_db.add_service("http://terra.thelazy.net/yamm/mods.json")
            self.update_data()
        else:
            self.update_data(False)
        
    def show_module(self, e):
        for index in self.modsbox.curselection():
            CALLBACK["showmod"](self.modmap[index])

    def do_search(self, e=None):
        q = self.entry_search.get()
        modmap = self.mod_db.search(q)
        self.list_modules(modmap)
        self.status.set("%s result(s) found" % len(modmap))