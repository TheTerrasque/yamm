YAMM - Yet Another Mod Manager
------------------------------

This is a mod organizing tool that focuses on downloading and
getting mods *and* requirements to Mod Organizer, and is meant to
work in tandem with the Mod Organizer tool.

This works by subscribing to various mod services, and then use
published data from those to resolve dependencies and download mods
in a distributed way.

The JSON itself can be generated from existing databases,
either dynamically on request or static on updates.

------------------------

Actual mod installataion / management not included,
since goal is to have MO do that.

-----------------------

JSON Service Format:

Root entry consist of two keys:

1. "mods" - Holding a list of mods this service provides
2. "service" - Holding metadata of the service

"mods" key:
    Required field:
     - "name" : This will be the referential name of the mod. Used internally for resolving dependencies.
    
    Optional fields:
     - "version" : The version of the mod. Not actively used at the moment, but there are some plans for it.
     - "category": What category it's put under. Category "framework" won't show in normal mod listing in the program.
     - "filehash": sha256 hash for file, base64 encoded with trailing "=" removed.
     - "homepage": URL to homepage or page for more information about the mod.
     - "description": Short description of the mod.
     - "filesize": Size in bytes for mod.
     - "filename": Name of the mod's file on the server.
     - "torrent": Name of torrent file for mod.
     - "author": Author of said mod.
     - "magnet": Torrent infohash, for use in magnet link. Will only be tried if torrent file is not provided.
     
     These optional entries consist of list of strings referencing name field on other mods, and defines relations to other mods
        - "depends": What other mods this one requires.
        - "recommends": Other mods recommended to run with this mod, but not required.
        - "provides": Mod names this mod provides drop-in replacement of.
        - "conflicts": Mods this one is in direct conflict with.

"service" key:
    Required field:
     - "name": Name of the service
    
    Optional fields:
     - "filelocations":
            List of base urls that are combined with filename for mod. If not given, the final url will be in relation to the json url.
            If more than one entry in list, one will be chosen at random.
            
     - "recommends": List of urls to other services that this service recommends / relies on. User will be asked if s/he want to add these too
     - "torrents": Base URL to torrent files. Works similar to "filelocations", but is only one entry.

-----------------------

URL scheme:

    YAMM urls start with "yamm:" and contains one or more of the following (separated by | ):
        "service:<url>" - URL is url to json service file. If user doesn't have that service s/he will be asked if it shall be added
        "mod:<modname>" - Will open the window for "modname" if it's found in the database.
        
    These can be chained, so you can for example add the relevant service before opening the mod.
     
-----------------------

Troubleshooting:

    If something doesn't work:
     - Ensure you have the latest code
     - Delete %userprofile%/YAMM/data/modinfo.db and re-add the services