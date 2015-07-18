import json
import requests
import time
# https://trac.transmissionbt.com/browser/trunk/extras/rpc-spec.txt

class qBittorrentRPC(object):
    def __init__(self, login = None,url="http://127.0.0.1:8080"):
        self.s = requests.Session()
        self.url = url
        self.sid = None
        if login:
            self.authorize(*login)
        
    def authorize(self, username, password):
        r = self.post("/login", {"username": username, "password": password})
        print r.content
    
    def post(self, url, data={}):
        return self._req(url, data)
    
    def get(self, url, data={}):
        return self._req(url, data, use_get=True)
    
    def _req(self, url, data=None, use_get=False):
        c = {
            
        }
        if self.sid:
            c["SID"] = self.sid
            
        if use_get:
            response = self.s.get(self.url+url, cookies=c)
        else:
            response = self.s.post(self.url+url, data, cookies=c)
        if not response.ok:
            response.raise_for_status()
        if response.cookies.get("SID"):
            self.sid = response.cookies.get("SID")
            print "SID set %s" % self.sid
        return response

    def set_preference(self, preferences):
        preference_data = {"json": json.dumps(preferences)}
        print preference_data["json"]
        self.post("/command/setPreferences", preference_data)

    def add_torrent_path(self, url, filename, folder):
        folder = folder.replace("/", "\\")
        
        old_path = self.get_preferences()["save_path"]
        
        print "Folder: %s" % folder
        self.set_preference({"save_path": folder})

        r = self.add_torrent(url, filename)
        
        self.set_preference({"save_path": old_path})
        return r
        
    def get_preferences(self):
        return self.get("/query/preferences").json()

    def get_torrents(self):
        torrents = self.get("/query/torrents").json()
        return torrents

    def get_torrent_with_name(self, name):
        for x in self.get_torrents():
            if x["name"] == name:
                return x

    def add_torrent(self, url, filename):
        x = self.get_torrent_with_name(filename) 
        if x:
            return x["hash"]
        
        self.post("/command/download", {"urls": url})
        
        while not x:
            time.sleep(0.01)
            x = self.get_torrent_with_name(filename)
        return x["hash"]

class TransmissionRPC(object):
    sessionid = ""
    
    def __init__(self, host="localhost", port=9091):
        self.host = host
        self.port = port
        self.url = "http://" + host + ":" + str(port) + "/transmission/rpc"

    def _request(self, method, arguments={}):
        headers = {
            "X-Transmission-Session-Id": self.sessionid,
            'Content-Type': 'application/json'
        }
        data = {
            "method": method,
            "arguments": arguments
        }
        
        r = requests.post(self.url, headers = headers, data = json.dumps(data))
        
        if r.status_code == 409:
            self.sessionid = r.headers["X-Transmission-Session-Id"]
            return self._request(method, arguments)
        
        return r.json()
    
    def get_torrents(self, fields = ["id", "name", "percentDone", "totalSize"]):
        return self._request("torrent-get", {"fields":fields})

    def add_torrent(self, download_path, torrent_link):
        r = self._request("torrent-add", {"filename":torrent_link, "download-dir": download_path})

        if r["arguments"]:
            a = r["arguments"]
            if "torrent-added" in a:
                return a["torrent-added"]["id"]
            if "torrent-duplicate" in a:
                return a["torrent-duplicate"]["id"]
        
    
    def version(self):
        return self._request("session-get")["arguments"]["version"]
    
if __name__ == "__main__":
    #tr = TransmissionRPC()
    #print tr.version()
    #print tr._request("torrent-get", {"fields": ["id"]})
    
    qb = qBittorrentRPC()
    
    print qb.add_torrent("http://yamm.thelazy.net/media/torrents/UnofficialSkyrimPatch_2.1.1.torrent", "Unofficial_Skyrim_Patch-19-2-1-1.7z")
    print qb.get_torrents()
    print qb.get_preferences()["save_path"]