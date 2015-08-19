import json
import mmap
import time
import tempfile
import os.path

filename = "yamm_mo_rpc"
filename = os.path.join(tempfile.gettempdir(), filename)
size=16384

class TimeoutException(Exception):
    pass

PLUGIN_VERSION = 2
MO_VERSION = [1, 3, 5]

class RpcCaller(object):
    data = None
    
    def __init__(self):
        self._setup_link()
    
    def _setup_link(self):
        if not os.path.exists(filename):
            with open(filename, "wb") as f:
                f.write("Hello Python!\n")
        fn = open(filename, "r+")
        fn.seek(size - 1)
        fn.write("\0")
        fn.flush()
        self.data = mmap.mmap(fn.fileno(), size)
        
    def __getattr__(self, value):
        def caller(*args, **kwargs):
            return self._send_request(value, args, kwargs)
        return caller
        
    
    def _check_version(self):
        return True
    
    def _send_request(self, function, args=[], kwargs={}, timeout = 0):
        if not self.data:
            return None
        
        d = {
            "function": function,
            "args": args,
            "kwargs": kwargs
        }
        WAIT = 0.01
        
        def write(data):
            self.data.seek(0)
            tval  = data + (" " * size)
            tval = tval[:size]
            self.data.write(tval)
        
        def read():
            self.data.seek(0)
            dd = self.data.read(size).strip()
            d = json.loads(dd)
            return d
        
        
        jdata = json.dumps(d)
        
        write(jdata)
        C = 0
        while not "result" in d:
            time.sleep(WAIT)
            C += WAIT
            if timeout and C > timeout:
                raise TimeoutException("Timed out waiting for answer")
            d = read()
            
        if "error" in d:
            print " ", d["error"]
            print " ", d["details"]
            print " ", d["data"]
            for x in d["trace"]:
                print "  ", x
            return None
        return d["result"]
        

    def ping(self):
        try:
            return self._send_request("version", timeout=0.2)
        except TimeoutException:
            return False
        

if __name__ == "__main__":
    
    rpc = RpcCaller()
    if rpc.ping():
        print rpc.version()
        print rpc.get_mo_version()
        print rpc.get_debug()
        print rpc.get_mod("Testing 123")
        print rpc.get_mod("SkyUI")
        print rpc.get_gamename()
        print rpc.get_active_profile()
        print rpc.get_mods()
    else:
        print "Timeout, ModOrganizer is not running?"
