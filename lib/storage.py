from utility.peewee import *

db = SqliteDatabase('mods.db')

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
    
    def set_mirrors(self, mirrorlist):
        self.mirrors = "|".join(mirrorlist)
    
    def get_mirrors(self):
        return self.mirrors.split("|")
    
    def get_mirror(self):
        return self.active_mirror or self.get_mirrors()[0]

class ModEntry(BaseModel):
    name = CharField(index=True)
    description = TextField(null=True)
    version = CharField(null=True)
    service = ForeignKeyField(ModService)
    filename = CharField(null=True)

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
    
def create_tables():
    db.connect()
    db.create_tables([Settings, ModEntry, ModService, ModDependency],  safe=True)

create_tables()