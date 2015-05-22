import Tkinter as tK
import tkMessageBox
import tkSimpleDialog
from .utils import get_filesize_display
import os
from .thread_workers import start_threads
import webbrowser

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
MOQUEUE = None

def initialize_uimodules():
    global DLQUEUE
    global MOQUEUE
    DLQUEUE, MOQUEUE = start_threads()
    

class CreateToolTip(object):
    '''
    create a tooltip for a given widget
    '''
    #Source : https://www.daniweb.com/software-development/python/code/484591/a-tooltip-class-for-tkinter
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.close)
    def enter(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = tK.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tK.Label(self.tw, text=self.text, justify='left',
                       background='yellow', relief='solid', borderwidth=1,
                       font=("times", "8", "normal"))
        label.pack(ipadx=1)
    def close(self, event=None):
        if self.tw:
            self.tw.destroy()


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


class ModDlEntry:
    """
    An UI object representing the mod and related info
    For downloading mod
    """
    overwrite = False
    
    def __init__(self, parent, mod, downloaddir):
        self.parent = parent
        self.mod = mod
        self.downloaddir = downloaddir
        self.path =  mod.mod.filename and os.path.join(self.downloaddir, mod.mod.filename) or None
        self.required_by = ["Some modules here"]
        self.recommended_by = []
        self.create_widgets()
        self.set_data()
                       
    def create_widgets(self):
        frame = tK.Frame(self.parent)
        self.frame = frame
        frame.config(relief=tK.SUNKEN, bd=1)
        frame.pack(fill=tK.BOTH)
        
        # [X] | [95%] | BlaMod | Downloading | Required | 200MB | [x] Torrent | [Install in MO] | [Redownload]
        pack = {
            "side": tK.LEFT,
            "padx": 5,
            "pady": 3
        }
        
        self.dlvar = tK.IntVar()
        self.dlcheck = tK.Checkbutton(frame, var=self.dlvar)
        self.dlcheck.pack(**pack)
        
        self.ministatus = tK.Label(frame, text="[-o-]")
        self.ministatus.pack(**pack)
        
        self.name = tK.Label(frame, text="%s" % self.mod.mod.name, anchor=tK.W)
        self.name.pack(expand=1, fill=tK.X, **pack)
        self.name.bind("<Button-1>", self.show_mod)
    
        self.status = tK.Label(frame, text="State")
        self.status.pack(**pack)
        
        #self.relation = tK.Label(frame, text="Relation")
        #self.relation.pack(**pack)
        
        self.size = tK.Label(frame, text="??? kb")
        self.size.pack(**pack)
        
        self.torrvar = tK.IntVar()
        self.useTorrent = tK.Checkbutton(frame, var=self.torrvar, text="Torrent")
        self.useTorrent.pack(**pack)

        self.button_mo = tK.Button(frame, text="To MO", command=self.install_in_mo)
        self.button_mo.pack(fill=tK.X)
        CreateToolTip(self.button_mo, "Install the mod in Mod Organizer")

        self.set_row_color("#fff")

    def set_row_color(self, hexcolor):
        for e in [self.frame, self.dlcheck, self.ministatus,
                  self.name, self.status, self.size, self.useTorrent]:
            e.config(background=hexcolor)

    def is_download_checked(self):
        return self.dlvar.get()

    def install_in_mo(self):
        MOQUEUE.put(self)
        
    def set_data(self):
        self.dlcheck.select()
        
        self.set_status("-*-", "Listed")
        
        self.useTorrent.config(state=tK.DISABLED) # tK.NORMAL
        
        if self.mod.mod.filesize:
            self.size.config(text=get_filesize_display(self.mod.mod.filesize))
        
        if not self.path:
            self.dlcheck.deselect()
            self.dlcheck.config(state=tK.DISABLED)
            self.set_status("-v-", "No download info")
            
    def set_status(self, mini, text):
        self.ministatus.config(text="[" + mini + "]")
        self.status.config(text=text)

    def update_download(self, downloaded, totalsize, percent):
        self.set_status("%02d%%" % percent, "Downloading %s of %s" % (get_filesize_display(downloaded), get_filesize_display(totalsize)))
    
    def show_mod(self, event):
        CALLBACK["showmod"](self.mod)

    
class DownloadModules:
   
    def __init__(self, master, modlist, downloaddir="files/"):
        self.downloaddir = downloaddir
        self.mods = modlist
        self.setup_widgets(master)
        self.master = master

    def setup_widgets(self, master):
        master.title("Modules Download Window")
        master.minsize(width=400,  height=500)
        
        frame = tK.Frame(master)
        frame.pack(fill=tK.BOTH, expand=1)
        
        title = tK.Label(frame, text="Mod download list")
        title.pack(fill=tK.X)
        
        self.modwidgets = []
        frameMod = tK.Frame(frame)
        frameMod.pack(fill=tK.BOTH, expand=1)
        
        for mod in self.mods:
            m = ModDlEntry(frameMod, mod, self.downloaddir)
            self.modwidgets.append(m)
            
        self.button_dl = tK.Button(frame, text="Download checked mods", command=self.start_download)
        self.button_dl.pack(fill=tK.X, anchor=tK.S)
        
        self.button_mo = tK.Button(frame, text="Send checked mods to Mod Organizer", command=self.send_to_mo)
        self.button_mo.pack(fill=tK.X, anchor=tK.S)
    
    def send_to_mo(self):
        for x in self.modwidgets:
            if x.is_download_checked():
                x.set_status("+MO", "In Queue for MO")
                MOQUEUE.put(x)
    
    
    def start_download(self):
        if not DLQUEUE:
            L.critical("ERROR! QUEUE NOT CREATED!")
            
        if not os.path.exists(self.downloaddir):
            os.mkdir(self.downloaddir)

        for m in self.modwidgets:
            if m.is_download_checked():
                DLQUEUE.put(m)


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
        def getkey(obj):
            if obj[1]:
                return obj[1].mod.name
            return None
        return [sorted(deps, key=getkey), sorted(recommends, key=getkey)]
    
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