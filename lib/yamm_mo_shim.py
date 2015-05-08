import json
import mmap
import time

filename = r"C:\\Users\\Mikael\\yamm_mo_rpc"
size=16384

class RpcCaller(object):
    def __init__(self):
        fn = open(filename, "r+")
        self.data = mmap.mmap(fn.fileno(), size)
    
    def _send_request(self, function, args=[], kwargs={}):
        d = {
            "function": function,
            "args": args,
            "kwargs": kwargs
        }
        jdata = json.dumps(d)
        self.data.seek(0)
        tval = jdata + (" " * size)
        tval = tval[:size]
        self.data.write(tval)
        while not "result" in d:
            time.sleep(0.1)
            self.data.seek(0)
            dd = self.data.read(size).strip()
            d = json.loads(dd)
        return d["result"]
        
if __name__ == "__main__":
    rpc = RpcCaller()
    print rpc._send_request("echo", [], {})
    print rpc._send_request("get_gamename")