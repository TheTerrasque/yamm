from .utils import get_config_path
import os.path
import json

CPATH = get_config_path()

class Entry(object):
    def __init__(self, name, default_value="", description="", values=[], valuetype="text"):
        self.name = name
        self.values = values
        if values and valuetype=="text":
            valuetype = "choice"
        self.default_value = default_value
        self.description = description or name
        self.value = self.default_value
        self.valuetype = valuetype
    
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
    
    def __init__(self, name, description=""):
        self.name = name
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

configfile = os.path.join(CPATH, "settings.json")
        
def create_settings(conffile=configfile):        
    settings = Setting(configfile)
        
    settings.adds([
        Section("directory").adds([
            Entry("download", os.path.join(CPATH, "downloads"), "Download directory", valuetype="folder"),
            Entry("modir", "", "Mod Organizer folder", valuetype="folder"),
        ]),
        Section("torrent").adds([
            Entry("client", "none", values = (
                    ("none", "No client", "HTTP Download"),
                    ("transmission", "Transmission-QT [BETA]", "Needs Remote Access enabled at port 9091 and authentication turned off"),
                    ("qbittorent", "qBittorrent [ALPHA]", "Needs Web UI enabled at port 8080 with 'Bypass authentication for localhost' enabled")
                ),
                description="Torrent client"
            )
        ])
    ])
    
    settings.load()
    return settings

SETTINGS = create_settings()