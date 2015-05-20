import urllib
from threading import Thread, Lock
from Queue import Queue
import os.path

import mo_rpc

def mod_organizer_thread(queue, updatelock):
    rpc = mo_rpc.RpcCaller()
    
    def set_widget_state(mini, maxi):
            with updatelock:
                widget.set_status(mini, maxi)
    while True:
        widget = queue.get()
        
        if not rpc.ping():
            set_widget_state("-MO", "Could not connect to MO")
            continue
        
        if widget.path:
            if rpc.get_mod(widget.mod.mod.name):
                set_widget_state("MO!", "Mod already installed")
            else:
                set_widget_state("MO>", "Waiting for Mod Organizer")
                modname = rpc.install_mod(widget.path, widget.mod.mod.name)
                if modname:
                    set_widget_state("MO!", "Mod installed")
                else:
                    set_widget_state("MO?", "Mod install failed")
        else:
            set_widget_state("---", "No mod file to install")
            
def downloader_thread(queue, updatelock):
    def handle_next_entry():
        widget = queue.get()
        
        def set_widget_state(mini, maxi):
            with updatelock:
                widget.set_status(mini, maxi)
        
        def mahook(count, blocksize, totalsize):
            if count % 15 != 0:
                return
            dl = count * blocksize
            percent = int(( float(dl) / totalsize) * 100)
            
            with updatelock:
                widget.update_download(dl, totalsize, percent)
        
        if not widget.overwrite and os.path.exists(widget.path):
            set_widget_state("---", "Checking file")
            
            if not widget.mod.check_file(widget.path, True):
                set_widget_state("/o\\", "File damaged")
            else:
                set_widget_state("-o-", "Completed")
        else:
            urllib.urlretrieve(widget.mod.get_url(), widget.path, mahook)
            set_widget_state("\o/", "Completed")
            if not widget.mod.check_file(widget.path, True):
                set_widget_state("/o\\", "File damaged")
        
    
    while True:
        handle_next_entry()

THREADS = []

def start_threads(dlnum=2):
    """
    Start up threads for file downloading
    
    Queue arguments:
        module UI widget class
    """
    dlqueue = Queue()
    modqueue = Queue()
    updatelock = Lock()
    for x in range(dlnum):
        DLTHREAD = Thread(target=downloader_thread, args = (dlqueue, updatelock))
        DLTHREAD.daemon = True
        DLTHREAD.start()
        THREADS.append(DLTHREAD)
    MODTHREAD = Thread(target=mod_organizer_thread, args = (modqueue, updatelock))
    MODTHREAD.daemon = True
    MODTHREAD.start()
    THREADS.append(MODTHREAD)
    return dlqueue, modqueue