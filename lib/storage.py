from utility.peewee import *
import random
import os
from urlparse import urljoin
from utils import get_config_path
from datetime import datetime

basepath = os.path.join(get_config_path(), "data")
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
    torrent = CharField(null=True)
    
    def set_mirrors(self, mirrorlist):
        self.mirrors = "|".join(mirrorlist)
    
    def get_mirrors(self):
        return [urljoin(self.url, x) for x in self.mirrors.split("|")]
    
    def clear_mods(self):
        with db.transaction():
            for mod in ModEntry.select().filter(ModEntry.service == self):
                mod.delete_instance(recursive=True, delete_nullable=True)
    
    def get_torrent_path(self):
        if self.torrent:
            return urljoin(self.url, self.torrent)
    
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

    def is_watched(self):
        return ModWatch.select().where(ModWatch.mod == self).count()

    def remove_watch(self):
        if self.is_watched():
            ModWatch.select().where(ModWatch.mod == self).get().delete_instance()

    def set_watch(self):
        if not self.is_watched():
            watch = ModWatch(mod=self)
            watch.save()
            watch.update_versiondata()
            watch.save()
            return watch

class ModWatch(BaseModel):
    mod = ForeignKeyField(ModEntry)
    version = CharField(null=True)
    updated = DateTimeField(null=True)
    
    def update_versiondata(self):
        self.version = self.mod.version
        self.updated = datetime.now()
    
    def is_updated(self):
        return self.version != self.mod.version

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
    db.create_tables([ModEntry, ModService, ModDependency, ModWatch],  safe=True)

create_tables()