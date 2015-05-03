YAMM - Yet Another Mod Manager
------------------------------

A first-pass barebone prototype for a mod download/management system

Goal is to work as a plugin for Mod Organizer

This works by subscribing to various mod services, and then use
published data from those to resolve dependencies and download mods
in a distributed way.

A lot is missing, but especially metadata like filesize and hash of files is missing.
With a secure hash included, mod sites can let volunteers help with file hosting
without having to trust them completely.

The JSON itself can be generated from existing databases,
either dynamically on request or static on updates.

------------------------

Example use:

    # Build index and initialize DB
    python yamm.py add "http://terra.thelazy.net/yamm/mods.json"
    python yamm.py update
    
    python yamm.py search ui
    python yamm.py search defeat
    python yamm.py show SkyUI
    python yamm.py show Defeat
    
    python yamm.py download Defeat

-----------------------

Actual mod installataion / management not included,
since goal is to have MO do that.

-----------------------

Troubleshooting:

    If something doesn't work:
     - Ensure you have the latest code
     - Delete mods.db and rebuild index