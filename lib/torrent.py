import urllib2
import json

# https://trac.transmissionbt.com/browser/trunk/extras/rpc-spec.txt

class TransmissionRPC(object):
    sessionid = ""
    
    def __init__(self, host="localhost", port=9091):
        self.host = host
        self.port = port
        self.url = "http://" + host + ":" + str(port) + "/transmission/rpc"

    def _request(self, method, arguments={}):
        req = urllib2.Request(self.url)
        req.add_header("X-Transmission-Session-Id", self.sessionid)
        req.add_header('Content-Type', 'application/json')
        
        data = {
            "method": method,
            "arguments": arguments
        }
        jdata = json.dumps(data)
        resp = None
        try:
            resp = urllib2.urlopen(req, jdata)
            
        except urllib2.HTTPError as e:
            if e.code == 409:
                self.sessionid = e.headers["X-Transmission-Session-Id"]
                #print "Updated session ID to %s" % self.sessionid
                return self._request(method, arguments)
            else:
                print "HTTP error:", e.code
        if resp:
            return json.loads(resp.read())
    
    def get_torrents(self, fields = ["id", "name", "percentDone", "totalSize"]):
        return self._request("torrent-get", {"fields":fields})

    def add_torrent(self, download_path, torrent_link):
        r = self._request("torrent-add", {"filename":torrent_link, "download-dir": download_path})
        return r["arguments"]["id"]
    
    def version(self):
        return self._request("session-get")["arguments"]["version"]
    
if __name__ == "__main__":
    tr = TransmissionRPC()
    print tr.version()
    print tr._request("torrent-get", {"fields": ["id"]})
    