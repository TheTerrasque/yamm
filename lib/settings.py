from .utils import get_config_path
import os.path
import json

CPATH = get_config_path()

class Entry(object):
    def __init__(self, name, default_value=None, description="", values=[]):
        self.name = name
        self.values = values
        self.default_value = default_value
        self.description = description
        self.value = self.default_value

    def get_value(self):
        return self.value
    
    def get_value_display(self):
        if self.values:
            for x, v in self.values:
                if x == self.value:
                    return v
        return self.value
        
    def write(self):
        return self.get_value()
    
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
        
SETTINGS = Setting(configfile)
    
SETTINGS.adds([
    Section("directory").adds([
        Entry("download", os.path.join(CPATH, "downloads"), "Directory to store downloaded files"),
    ]),
    Section("torrent").adds([
        Entry("client", values = (
                (None, "No client"),
                ("transmission", "Transmission-QT"),
                ("qbittorent", "qBitTorrent")
            )
        )
    ])
])

SETTINGS.load()