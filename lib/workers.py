import os
from threading import Thread, Lock
from Queue import Queue, Empty

import logging

import time

import mo_rpc
import requests

from requests.exceptions import ConnectionError

from .torrent import qBittorrentRPC, TransmissionRPC
from .utils import get_json

L = logging.getLogger("YAMM.worker")

STATUS = {
    0: (" I ", "Initializing"),
    1: (" Q ", "Queued"),
    2: (" D ", "Downloading"),
    3: (" C ", "Complete"),
    "CHECKSUM_ERR": ("!!!", "Checksum failed"),
    "Merr": ("-MO", "Could not connect to MO"),
    "Mwait": ("MO>", "Waiting for Mod Organizer"),
    "Mexist": ("MO!", "Mod already installed"),
    "Mcomplete": ("MO!", "Mod installed"),
    "Mfail": ("MO?", "Mod install failed"),
    "Mmiss": ("---", "No mod file to install"),
    "Tadd": (".T.", "Adding torrent"),
    "Tfail": ("!T!", "Couldn't add torrent!"),
    "Tadded": (" T ", "Torrent added"),
}

def requests_download_file(url, outfile, callback_func=None, try_resume=True, chunksize=64*1024):
    """
    Download file via Requests, support continuing a partial download
    """
    headers = {}
    filemode = "wb"
    existing = 0
    chunk_offset = 0
    
    if try_resume and os.path.exists(outfile):
        existing = os.path.getsize(outfile)
        headers["Range"] = "bytes=%s-" % existing
    
    r = requests.get(url, stream=True, headers = headers)
    filesize = int(r.headers['content-length'])
    
    #If server responds correctly to a range request, append to existing file
    if r.status_code == 206:
        filemode = "ab"
        filesize = filesize + existing
        chunk_offset = existing / chunksize
        
    else:
        if not r.status_code == requests.codes.ok:
            #print "Got error status code", r.status_code
            L.warning("Downloader got status code %s for url %s", r.status_code, url)
            return
    
    with open(outfile, filemode) as f:
        for count, chunk in enumerate(r.iter_content(chunk_size=chunksize)):
            f.write(chunk)
            if callback_func:
                callback_func(count + chunk_offset, chunksize, filesize)
            
def queue_thread_handler(queue, workClass):
    worker = workClass(queue)
    while True:
        try:
            worker.next()
        except Exception:
            L.exception("Worker %s failed", workClass.name)

class BaseWorker(object):
    threads = 1
    name = None
    
    def __init__(self, queue):
        self.queue = queue
        self.init()
    
    def init(self):
        pass    
    
    def next(self):
        self.process(self.queue.get())

    @classmethod
    def get_name(cls):
        return cls.name or "q-" + cls.__name__
    
    def process(self, entry):
        raise Exception("Process not implemented")


class Workers:
    class TransmissionDownload(BaseWorker):
        def init(self):
            self.rpc = TransmissionRPC()
            self.downloads = []

        def next(self):
            try:
                r = self.queue.get(True, 1)
                self.process(r)
            except Empty:
                self.update_entries()
                
        def update_entries(self):
            tmap = {}
            r = self.rpc.get_torrents()
            for t in r["arguments"]["torrents"]:
                tmap[t["id"]] = t
            
            to_remove = []
            
            for order in self.downloads:
                if order.torrentid in tmap:
                    data = tmap[order.torrentid]
                    done = int(data["percentDone"]*100)
                    order._progress(done, data["totalSize"])
                    if done > 99:
                        order._update(3, verify=True)
                        to_remove.append(order)
            for x in to_remove:
                self.downloads.remove(x)
            
        def process(self, order):
            torrent = order.entry.get_torrent_link()
            order._update("Tadd")
            try:
                r = self.rpc.add_torrent(order.get_download_folder(), torrent)
            except ConnectionError:
                order.torrentid = None
                order._update("Tfail")
                return
            
            order.torrentid = r
            self.downloads.append(order)
            order._update("Tadd")
    
    class qTorrentDownload(BaseWorker):
        def init(self):
            self.rpc = qBittorrentRPC()
            self.downloads = []

        def next(self):
            try:
                r = self.queue.get(True, 1)
                self.process(r)
            except Empty:
                self.update_entries()
                
        def update_entries(self):
            tmap = {}
            for t in self.rpc.get_torrents():
                tmap[t["hash"]] = t
            
            for order in self.downloads:
                if order.filehash in tmap:
                    data = tmap[order.filehash]
                    order._progress(int(data["progress"]*100), data["size"])
            
        def process(self, order):
            filename = order.entry.mod.filename
            torrent = order.entry.get_torrent_link()
            order._update("Tadd")
            r = self.rpc.add_torrent_path(torrent, filename, order.get_download_folder())
            order.filehash = r
            self.downloads.append(order)
            order._update("Tadd")
            
    class HttpDownload(BaseWorker):
        threads = 2
        
        def process(self, order):
            def hook(count, blocksize, totalsize):
                dl = count * blocksize
                percent = int(( float(dl) / totalsize) * 100)
                order._progress(percent, totalsize)
                
            requests_download_file(order.entry.get_url(), order.file_path(), hook)
            order._update(3, verify=True)

    class ServiceUpdate(BaseWorker):
        threads = 4
        
        def process(self, order):
            entry = order.entry
            data, etag = get_json(entry.service.url, entry.service.etag)
            with order.parent.get_lock("DB"):
                entry.update(data, etag)
            order._update()
     
    class ModOrganizer(BaseWorker):
        
        def init(self):
            self.rpc = mo_rpc.RpcCaller()
    
        def process(self, order):
            
            mod_name = order.entry.mod.name
            
            if order.parent.SETTINGS["mo.modtag"]:
                mod_name = "[YAMM] %s" % mod_name
            
            if order.parent.SETTINGS["mo.modtagversion"]:
                mod_name = "%s v%s" % (mod_name, order.entry.mod.version)
            
            if not self.rpc.ping():
                return order._update("Merr")
            
            if self.rpc.get_mod(mod_name):
                if order.parent.SETTINGS["mo.modenable"]:
                    self.rpc.set_active(mod_name)
                return order._update("Mexist")
            
            modname = self.rpc.install_mod(order.file_path(), mod_name, category="YAMM Installed")
            
            if modname:
                if order.parent.SETTINGS["mo.modenable"]:
                    time.sleep(0.5) # To let MO do it's thing before enabling the mod
                    self.rpc.set_active(mod_name)
                return order._update("Mcomplete")
            else:
                return order._update("Mfail")

class WorkOrder(object):
    def __init__(self, workclass, entry, callback=None):
        self.entry = entry
        self.callback = callback
        self.status = 1
        self.worker = workclass

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

    def get_download_folder(self):
        r = self.parent.SETTINGS["directory.download"]
        if not os.path.exists(r):
            os.mkdir(r)
        return r

    def file_path(self):
        return os.path.join(self.get_download_folder(), self.entry.mod.filename)
        
    def _update(self, status=None, verify=False):
        self.status = status
        
        if verify:
            if not self.entry.check_file(self.file_path()):
                self.status = "CHECKSUM_ERR"
        
        if self.callback:
            with self.parent.get_lock("UI"):
                self.callback(self)

class WorkHandler(object):
    def __init__(self, settings):
        self.urls = []
        
        self.SETTINGS = settings
                
        self._threads = []
        self.locks = {}
        self.queue = {}
    
    def get_lock(self, lockname):
        if not lockname in self.locks:
            self.locks[lockname] = Lock()
        return self.locks[lockname]
    
    def get_queue_for(self, workerclass):
        queuename = workerclass.get_name()
        
        if not queuename in self.queue:
            self.queue[queuename] = Queue()
            
            for threadnum in range(workerclass.threads):
                thread = Thread(target=queue_thread_handler, args = (self.queue[queuename], workerclass))
                thread.daemon = True
                thread.start()
                self._threads.append(thread)
                
        return self.queue[queuename]

    def add_order(self, *args, **kwargs):
        entry = WorkOrder(*args, **kwargs)
        self.add_work(entry)
    
    def add_work(self, entry):
        queue = self.get_queue_for(entry.worker)
        entry.init(self)
        queue.put(entry)