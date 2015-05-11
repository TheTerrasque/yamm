import urllib
from threading import Thread, Lock
from Queue import Queue
import os.path

def downloader_thread(queue, updatelock):
    def handle_next_entry():
        widget =  queue.get()
        
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
            urllib.urlretrieve(widget.mod.get_url(), widget.path, mahook)
        
        with updatelock:
            set_widget_state("\o/", "Completed")
    
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