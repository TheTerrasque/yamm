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

Running via GUI:

 1. Install Python (version 2) from python.org
 2. Then double click on the "yammy ui.pyw" file.
    - First start might be a bit slow as it has to
      set up the database and download metadata
 3. Double click the mod you want installed
 4. Click "Download mods"
 5. Click "Start download"
 6. All needed files will be downloaded to files/ subdir

Set up Mod Organizer plugin and URL handling:

 To set up and install these, you ususally need administrator access.

 The easy way to do this is to run the provided "setup.vbs" script,
 which will start the GUI in setup mode and with the correctaccess rights.

 You can also start the setup part manually by starting
 "yammy ui.pyw" with "--setup" option.

 You will need Mod Organizer v 1.3.5 or higher for the MO plugin to work.

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
     - Delete data/modinfo.db and re-add the services