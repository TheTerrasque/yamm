import urllib
import os
from threading import Thread, Lock
from Queue import Queue

import mo_rpc

STATUS = {
    0: (" I ", "Initializing"),
    1: (" Q ", "Queued"),
    2: (" D ", "Downloading"),
    3: (" C ", "Complete"),
    "Merr": ("-MO", "Could not connect to MO"),
    "Mwait": ("MO>", "Waiting for Mod Organizer"),
    "Mexist": ("MO!", "Mod already installed"),
    "Mcomplete": ("MO!", "Mod installed"),
    "Mfail": ("MO?", "Mod install failed"),
    "Mmiss": ("---", "No mod file to install"),
}

def requests_download_file(url, outfile, callback_func=None, byterange=None, chunksize=256*1024):
    r = requests.get(url, stream=True)
    with open(outfile, 'wb') as f:
        for count, chunk in enumerate(r.iter_content(chunk_size=chunksize)):
            f.write(chunk)
            if callback_func:
                callback_func(count, chunksize, r.content)
            
def queue_thread_handler(queue, workClass):
    worker = workClass()
    while True:
        entry = queue.get()
        worker.process(entry)

class BaseWorker(object):
    pass

class HttpDownload(BaseWorker):
    def process(self, entry):
        def hook(count, blocksize, totalsize):
            if count % 15 != 0: # Limit how often updates are run
                return
            dl = count * blocksize
            percent = int(( float(dl) / totalsize) * 100)
            entry._progress(percent, totalsize)
            
        urllib.urlretrieve(entry.mod.get_url(), entry.file_path(), hook)
        entry._update(3)
 
class ModOrganizer(BaseWorker):
    def __init__(self):
        self.rpc = mo_rpc.RpcCaller()

    def process(self, entry):
        if not self.rpc.ping():
            return entry._update("Merr")
        
        if self.rpc.get_mod(entry.mod.mod.name):
            return entry._update("Mexist")
        
        modname = self.rpc.install_mod(entry.file_path(), entry.mod.mod.name)
        if modname:
            return entry._update("Mcomplete")
        else:
            return entry._update("Mfail")

class ModWorkorder(object):
    def __init__(self, mod, task, callback=None):
        self.mod = mod
        self.callback = callback
        self.status = 1
        self.task = task

    def init(self, parent):
        self.parent = parent
        
    def get_status(self):
        return STATUS[self.status][1]
    
    def get_mini_status(self):
        if self.status == 2:
            return "%s%%" % self.percent
        return STATUS[self.status][0]
    
    def _progress(self, percent, totalsize):
        self.percent = percent
        self.totalsize = totalsize
        self._update(2)

    def file_path(self):
        return os.path.join(self.parent.folder, self.mod.mod.filename)
        
    def _update(self, status):
        self.status = status
        if self.callback:
            with self.parent.UIlock:
                self.callback(self)

WORKERS = [
    #(queuename, workerclass, num_threads)
    ("dlhttp", HttpDownload, 2),
    ("mo-rpc", ModOrganizer, 1)
]

class WorkHandler(object):
    def __init__(self, folder):
        self.urls = []
        self.folder = folder
        if not os.path.exists(folder):
            os.mkdir(folder)
        
        self._threads = []
        self.create_threads()
        
    def create_threads(self):
        self.queue = {}
        self.UIlock = Lock()
        
        for queuename, work_class, num_threads in WORKERS:
            self.queue[queuename] = Queue()
            for threadnum in range(num_threads):
                thread = Thread(target=queue_thread_handler, args = (self.queue[queuename], work_class))
                thread.daemon = True
                thread.start()
                self._threads.append(thread)

    def add_work(self, entry):
        entry.init(self)
        self.queue[entry.task].put(entry)