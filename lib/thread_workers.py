import urllib
from threading import Thread, Lock
try:
    from Queue import Queue
except ImportError:
    from queue import Queue
import os.path

def downloader_thread(queue, updatelock):
    def handle_next_entry():
        mod, path, hook, active, completehook, overwrite =  queue.get()
        msg = ""
        def mahook(count, blocksize, totalsize):
          
            if count % 15 != 0:
                return
            dl = count * blocksize
            percent = int(( float(dl) / totalsize) * 100)
            
            with updatelock:
                hook(dl, totalsize, percent, active)
        
        if not overwrite and os.path.exists(path):
                msg = "[-o-]  %s - Already downloaded"
                if not mod.check_file(path, True):
                    msg = "[/o\]  %s - File is damaged"
        else:
            urllib.urlretrieve(mod.get_url(), path, mahook)
            msg = "[\o/]  %s - Completed"
        with updatelock:
            completehook(active, path, msg)
    
    while True:
        handle_next_entry()

THREADS = []

def start_download_threads(num=2):
    """
    Start up threads for file downloading
    
    Queue arguments:
        [module, basepath, progresshook, modnumber, download_complete_hook, overwrite_boolean]
    """
    queue = Queue()
    updatelock = Lock()
    for x in range(num):
        DLTHREAD = Thread(target=downloader_thread, args = (queue, updatelock))
        DLTHREAD.daemon = True
        DLTHREAD.start()
        THREADS.append(DLTHREAD)
    return queue