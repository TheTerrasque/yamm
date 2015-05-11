import re
import logging

import hashlib

try:
    import urllib2
    from StringIO import StringIO
except ImportError:
    #Python 3
    from urllib import request as urllib2
    from io import StringIO

import gzip

import json

import os.path

L = logging.getLogger("YAMM.utils")

hasher = hashlib.sha256
BLOCKSIZE = 65536


def get_base_path():
    return os.path.dirname(os.path.dirname(__file__))


# Credits: http://stackoverflow.com/questions/1714027/version-number-comparison
def compare_version(version1, version2):
    def normalize(v):
        v.replace("-", ".")
        return [int(x) for x in re.sub(r'(\.0+)*$','', v).split(".")]
    return cmp(normalize(version1), normalize(version2))

SIZES = ['KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']
BYTES = 1024

def get_filesize_display(size):
    """
    Return filesize displayed in a userfriendly manner
    """
    for suffix in SIZES:
        size /= BYTES
        if size < BYTES:
            return '{0:.1f} {1}'.format(size, suffix)
        

def create_filehash(path):
    """
    Return Base64 hash of file at path
    """
    h = hasher()
    with open(path, "rb") as f:
        buf = f.read(BLOCKSIZE)
        while len(buf) > 0:
            h.update(buf)
            buf = f.read(BLOCKSIZE)
    return h.digest().encode("base64").strip().strip("=")

def get_json(url, etag=None):
    """
    Fetch url and return as JSON decoded dict
    
    Support etag and gzip encoding
    """    
    class NotModifiedHandler(urllib2.BaseHandler):
  
        def http_error_304(self, req, fp, code, message, headers):
            addinfourl = urllib2.addinfourl(fp, headers, req.get_full_url())
            addinfourl.code = code
            return addinfourl

    opener = urllib2.build_opener(NotModifiedHandler())

    req = urllib2.Request(url)
    
    if etag:
        req.add_header("If-None-Match", etag)

    req.add_header('Accept-encoding', 'gzip')

    url_handle = opener.open(req)

    headers = url_handle.info()
    
    if headers.get("Content-Encoding") == "gzip":
        buf = StringIO( url_handle.read() )
        L.debug("GZIP response")
        f = gzip.GzipFile(fileobj=buf)
        jdata = f
    else:
        L.debug("Uncompressed response")
        jdata = url_handle

    etag = headers.getheader("ETag")

    if hasattr(url_handle, 'code') and url_handle.code == 304:
        return None, None
        
    # FIXME: Gzip?
    data = json.load(jdata)
    
    return data, etag