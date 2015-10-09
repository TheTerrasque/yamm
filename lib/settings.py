from .utils import get_config_path
import os.path
import json

CPATH = get_config_path()

class Entry(object):
    def __init__(self, name, default_value="", title="", values=[], valuetype="text", helptext=""):
        self.name = name
        self.values = values
        if values and valuetype=="text":
            valuetype = "choice"
        self.default_value = default_value
        self.description = title or name
        self.value = self.default_value
        self.valuetype = valuetype
        self.helptext = helptext
    
    def get_value_display(self):
        if self.values:
            for x, v in self.values:
                if x == self.value:
                    return v
        return self.value
        
    def write(self):
        return self.value
    
    def read(self, value):
        self.value = value

    def should_save(self):
        return self.default_value != self.value
        
class Section(object):
    
    def __init__(self, name, description="", title=None):
        self.name = name
        self.title = title or name.capitalize()
        self.description = description
        self.entries = {}
    
    def add(self, entry):
        self.entries[entry.name] = entry
        return self
    
    def adds(self, entries):
        for x in entries:
            self.add(x)
        return self
    
    def write(self):
        r = {}
        for key, value in self.entries.items():
            if value.should_save():
                r[key] = value.write()
        return r
    
    def read(self, value):
        for k, v in value.items():
            self.entries[k].read(v)

    def should_save(self):
        return self.write()
    
    def __getattr__(self, key):
        return self.entries[key]
    
class Setting(Section):
    def __init__(self, configfile):
        self.configfile = configfile
        self.entries = {}
    
    def load(self):
        if os.path.exists(self.configfile):
            with open(self.configfile) as f:
                v = json.load(f)
                self.read(v)
    
    def save(self):
        with open(self.configfile, "w") as f:
                v = self.write()
                json.dump(v, f, indent=4)

    def __getitem__(self, key):
        path = self
        for p in key.split("."):
            path = path.entries[p]
        return path.value

configfile = os.path.join(CPATH, "settings.json")
        
def create_settings(conffile=configfile):        
    settings = Setting(configfile)
        
    settings.adds([
        Section("directory", title="Directory setup").adds([
            Entry("download", os.path.join(CPATH, "downloads"), "Download directory", valuetype="folder"),
        ]),
        Section("torrent", title="BitTorrent").adds([
            Entry("client", "none", values = (
                    ("none", "No client", "HTTP Download"),
                    ("transmission", "Transmission-QT [BETA]", "Needs Remote Access enabled at port 9091 and authentication turned off"),
                    #("qbittorent", "qBittorrent [ALPHA]", "Needs Web UI enabled at port 8080 with 'Bypass authentication for localhost' enabled")
                ),
                title="Torrent client"
            )
        ]),
        Section("mo", title="Mod Organizer").adds([
            Entry("modir", "", "Mod Organizer folder", valuetype="folder"),
            Entry("modtag", False, "Tag YAMM mods in Mod Organizer", valuetype="checkbox", helptext="This will add [YAMM] in front of each mod installed with YAMM"),
            Entry("modenable", True, "Enable mods after installing", valuetype="checkbox", helptext="This will automatically enable a mod after installing it"),
        ])
    ])
    
    settings.load()
    return settings

SETTINGS = create_settings()