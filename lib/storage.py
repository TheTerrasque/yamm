from utility.peewee import *
import random
import os

from utils import get_base_path, os

basepath = os.path.join(get_base_path(), "data")
try:
    os.mkdir(basepath)
except WindowsError:
    pass

dbpath = os.path.join(basepath, "modinfo.db")

db = SqliteDatabase(dbpath)

class BaseModel(Model):
    class Meta:
        database = db

class Settings(BaseModel):
    key = CharField()
    value = TextField()

class ModService(BaseModel):
    name = CharField()
    url = CharField(unique=True)
    mirrors = TextField()
    active_mirror = CharField(null=True)
    etag = CharField(null=True)
    updated = DateTimeField(null=True)
    
    def set_mirrors(self, mirrorlist):
        self.mirrors = "|".join(mirrorlist)
    
    def get_mirrors(self):
        return self.mirrors.split("|")
    
    def get_mirror(self):
        return self.active_mirror or random.choice(self.get_mirrors())

class ModEntry(BaseModel):
    name = CharField(index=True)
    description = TextField(null=True)
    version = CharField(null=True)
    service = ForeignKeyField(ModService)
    category = CharField(null=True)
    filename = CharField(null=True)
    filehash = CharField(null=True)
    filesize = IntegerField(null=True)
    homepage = CharField(null=True)
    author = CharField(null=True)
    updated = DateTimeField(null=True)
    magnet = CharField(null=True)
    torrent = CharField(null=True)

DEPENDENCY = [
    (0, "Requires"),
    (1, "Provides"),
    (2, "Conflicts"),
    (3, "Recommends"),
]

class ModDependency(BaseModel):
    mod = ForeignKeyField(ModEntry)
    dependency = CharField(index = True)
    relation = IntegerField(choices = DEPENDENCY)

def get_mod_by_name(name):
    try:
        return ModEntry.get(name=name)
    except DoesNotExist:
        return None

def create_tables():
    db.connect()
    db.create_tables([ModEntry, ModService, ModDependency],  safe=True)

create_tables()