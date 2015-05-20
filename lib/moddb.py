from storage import ModEntry, ModDependency, ModService, db, get_mod_by_name

import logging
from collections import defaultdict

import datetime

from utils import create_filehash, get_json

L = logging.getLogger("YAMM.moddb")

MOD_CACHE = {}
def get_modentry(mod_id, db_instance = None):
    if not mod_id in MOD_CACHE:
        MOD_CACHE[mod_id] = ModInstance(mod_id, db_instance)
    return MOD_CACHE[mod_id]

class ModDependencies(object):
    def __init__(self, mod):
        self.mod = mod
        self.scan_mod()

    def get_mods_providing(self, tag):
        return [get_modentry(x.mod.id, x.mod) for x in ModDependency.select().where(ModDependency.relation == 1, ModDependency.dependency == tag)]
        
    def scan_mod(self):
        class ModDepEntry(object):
            def __init__(self):
                self.required_by = set()
                self.provided_by = set()
                self.conflicts_with = set()
                self.recommended_by = set()
        
            def get_provider(self):
                """
                Return a provider for this entry, or None if none are fund
                """
                if self.provided_by:
                    return list(self.provided_by)[0]
        
            def add_relation(self, mod, relation):
                entrylist = [self.required_by, self.provided_by, self.conflicts_with, self.recommended_by][relation]
                entrylist.add(mod)
        
            def add_providers(self, providerlist):
                self.provided_by.update(providerlist)
                
            def update(self, dep_entry):
                self.required_by.update(dep_entry.required_by)
                self.provided_by.update(dep_entry.provided_by)
                self.conflicts_with.update(dep_entry.conflicts_with)
                self.recommended_by.update(dep_entry.recommended_by)
                
            def display(self):
                return "Required by %s, provided by %s, recommended by %s" % (self.required_by, self.provided_by, self.recommended_by)
            
        depmap = defaultdict(ModDepEntry)
        
        for i, name in enumerate(["Requires", "Provides", "Conflicts", "Recommends"]):
            dep_tags = self.mod.get_dependency_tags(i)
            for tag in dep_tags:
                providers = self.get_mods_providing(tag)
                
                depmap[tag].add_providers(providers)
                depmap[tag].add_relation(self.mod, i)
                
                for provider in providers:
                    if provider.VISITED:
                        continue
                    provider.VISITED = True
                    if i == 0: #Only follow if required
                        d = provider.get_dependencies(False)
                        for key in d.dependencies:
                            depmap[key].update(d.dependencies[key])
        self.dependencies = depmap

    def get_required_mods(self):
        """
        Return dict where "mods" key is list of mods that are required for this mod and
        "unknown" is list of unresolved tags
        """
        mods = []
        unknowntags = []
        for key, value in self.dependencies.items():
            if value.required_by:
                if value.provided_by:
                    mods.append(list(value.provided_by)[0]) #Pick random'ish if more than one.
                else:
                    unknowntags.append((key, value))
        return {"mods":sorted(mods, key= lambda x: x.mod.name), "unknown": unknowntags}

class ModInstance(object):
    DEPS = None
    VISITED = False
    
    def __repr__(self):
        return u"<Mod:%s>" % self.mod.name
    
    def __init__(self, mod_id, instance=None):
        if instance:
            self.mod = instance
        else:
            self.mod = ModEntry.get(id=mod_id)

    def __unicode__(self):
        return self.mod.name
    
    def check_file(self, path, approve_if_no_dbhash=False):
        """
        Check file against hash in DB, return True or False
        If hash fails it will return False unless approve_if_no_dbhash is set to True
        """
        if self.mod.filehash:
            h = create_filehash(path)
            return h == self.mod.filehash
        return approve_if_no_dbhash
    
    def get_urls(self):
        """
        Return download urls for mod archive
        """
        if self.mod.filename:
            return [x + self.mod.filename for x in self.mod.service.get_mirrors()]
    
    def get_url(self):
        """
        Return random download url for mod archive
        """
        if self.mod.filename:
            return self.mod.service.get_mirror() + self.mod.filename
    
    def get_dependency_tags(self, relation=0):
        """
        Return list of dependency keywords
        """
        return [x.dependency for x in ModDependency.select().where(ModDependency.mod==self.mod, ModDependency.relation == relation)]
    
    def get_dependencies(self, reset=True):
        if reset:
            for k in MOD_CACHE:
                MOD_CACHE[k].VISITED = False
        
        if not self.DEPS:
            self.DEPS = ModDependencies(self)
        
        return self.DEPS
    
class ModDb(object):
    def add_service(self, json_url):
        if ModService.select().where(ModService.url==json_url).count():
            return None
        data, etag = get_json(json_url)
        service = ModService(url=json_url)
        service.name = data["service"]["name"]
        service.set_mirrors(data["service"]["filelocations"])
        service.save()
        L.info("Service %s added", service.name)
        return service
    
    def get_module(self, modulename):
        e = get_mod_by_name(modulename)
        if e:
            return get_modentry(e.id, e)
    
    def get_services(self):
        return ModService.select()
    
    def update_services(self):
        with db.transaction():
            for service in self.get_services():
                updater = ServiceUpdater(service)
                updater.update()
    
    def get_module_count(self):
        return ModEntry.select().count()
    
    def get_modules_not_in_category(self, category="framework"):
        """
        Return all modules *not* in the given category
        """
        d = ModEntry.select().where((ModEntry.category.is_null(True)) | (ModEntry.category != category))
        L.debug("There a re %s modules not in category %s", d.count(),  category)
        return [get_modentry(x.id, x) for x in d]
    
    def search(self, text):
        d = ModEntry.select().where(
             (ModEntry.description.contains(text)) |
             (ModEntry.name.contains(text))
            )
        return [get_modentry(x.id, x) for x in d]
    
class ServiceUpdater(object):
    
    # PeeWee related class functions

    def update_service_data(self, data, etag):
        """Update the service info from JSON data"""
        self.service.name = data["service"]["name"]
        self.service.etag = etag
        self.service.set_mirrors(data["service"]["filelocations"])
        self.service.save()

    def set_dependency_relation(self, modentry, dependencies, relation):
        """Remove old dependency data and set new for given relation
        
        Relations:
            (0, "Requires"),
            (1, "Provides"),
            (2, "Conflicts"),
            (3, "Recommends"),
        """
        ModDependency.delete().where(ModDependency.mod == modentry, ModDependency.relation == relation).execute()
        for dep in dependencies:
            ModDependency.create(mod = modentry, relation = relation, dependency = dep)

    def save_mod_instance(self, mod):
        """Create or update a mod instance in DB"""
        modentry, created = ModEntry.get_or_create(name=mod["name"], service=self.service)
        
        modentry.version = mod["version"]
        modentry.service = self.service
        
        # Optional entries
        for field in ["description", "filehash", "filesize", "homepage", "author", "category", "filename"]:
            if mod.get(field):
                setattr(modentry, field, mod[field])
        
        modentry.save()
        
        return modentry, created

    # Normal class functions
    
    def __init__(self, service):
        self.service = service

    def update(self):
        data, etag = get_json(self.service.url, self.service.etag)
        if data:
            self.update_service_data(data, etag)
            self.update_mods(data["mods"])
        
    def update_mods(self, modlist):
        ModEntry.delete().where(ModEntry.service == self.service).execute()
        
        for mod in modlist:
            modentry, new_entry = self.save_mod_instance(mod)
            
            self.set_dependency_relation(modentry, mod.get("depends", []), 0)                       # Requires
            self.set_dependency_relation(modentry, [modentry.name] + mod.get("provides", []), 1)    # Provides
            self.set_dependency_relation(modentry, mod.get("conflict", []), 2)                      # In conflict with
            self.set_dependency_relation(modentry, mod.get("recommends", []), 3)                     # Recommends
        MOD_CACHE.clear()