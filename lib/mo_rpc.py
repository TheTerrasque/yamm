import json
import mmap
import time
import tempfile
import os.path
import logging

filename = "yamm_mo_rpc"
filename = os.path.join(tempfile.gettempdir(), filename)
size=16384

L = logging.getLogger("YAMM.rpc_mo")

class TimeoutException(Exception):
    pass

class RpcCaller(object):
    data = None
    
    def __init__(self):
        if os.path.exists(filename):
            fn = open(filename, "r+")
            self.data = mmap.mmap(fn.fileno(), size)
    
    def __getattr__(self, value):
        def caller(*args, **kwargs):
            return self._send_request(value, args, kwargs)
        return caller
        
    
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
            L.warn("Call error for %s: %s", function, d["details"])
            return None
        return d["result"]
        
        
rpc = RpcCaller()

def ping():
    try:
        return rpc._send_request("version", timeout=0.2)
    except TimeoutException:
        return False
        

if __name__ == "__main__":
    if ping():
        print (rpc.get_mods())
        print (rpc.version())
        print (rpc.get_debug())
        print (rpc.get_gamename())
        print (rpc.get_active_profile())
        print (rpc.install_mod(r"D:\\JContainers-49743-3-2-3.zip"))
        print (rpc.install_mod2("JCTEST", r"D:\\JContainers-49743-3-2-3.zip"))
    else:
        print ("Timeout, ModOrganizer is not running?")