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

Running via GUI:

 1. Install Python (version 2) from python.org
 2. Then double click on the "yammy ui.pyw" file.
    - First start might be a bit slow as it has to
      set up the database and download metadata
 3. Double click the mod you want installed
 4. Click "Download mods"
 5. Click "Start download"
 6. All needed files will be downloaded to files/ subdir

Mod Organizer plugin:

 /!\ This is very much work in progress, and generally doesn't work very well
 
 If you have copied the utils/plugin_MO.py to Mod Organizer's plugin directory,
 and checked "Install in Mod Organizer after download" it will try to install
 the mod to Mod Organizer, where Mod Organizer will pop up a dialoge asking for name
 and doing the usual install procedure. 
------------------------

CLI Example use:

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