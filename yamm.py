#! /usr/bin/python
# -*- mode: python; coding: utf-8 -*-
import logging

logging.basicConfig(level=logging.INFO)

from lib import moddb

import urllib
import os.path
import os

import argparse
def create_argparse():
    parser = argparse.ArgumentParser(description='Yet Another Mod Manager')
    parser.add_argument('module', metavar='MODULE', help='Submodule', choices=F)
    parser.add_argument('extra', metavar='DATA', help='Data for submodule', nargs="?")
    parser.add_argument("--dldir", metavar="DIR", help="Download directory", default="files")
    args = parser.parse_args()
    return args


def addservice(mdb, args):
    if args.extra:
        try:
            # "http://terra.thelazy.net/yamm/mods.json"
            s = mdb.add_service(args.extra)
            print "Added service provider %s" % s.name
        except:
            logging.info("Could not add service (already added?)")

def search(mdb, args):
    if args.extra:
        for x in mdb.search(args.extra):
            print "%s - %s" % (x.mod.name, x.mod.description)

def update(mdb, args):
    mdb.update_services()

def info(mdb, args):
    mod = mdb.get_module(args.extra)
    print mod.mod.name
    print mod.mod.description
    print "Version %s" % mod.mod.version
    print "Download URL : %s" % mod.get_url()
    depends = mod.get_dependency_mods()
    if depends:
        print "Requires:"
        print "  " + ", ".join(x.mod.name for x in depends)

def download(mdb, args):
    mod = mdb.get_module(args.extra)
    depends = mod.get_dependency_mods()
    downloadlist = [mod] + depends
    
    if depends:
        print "Mod '%s' depends on : %s"% (mod.mod.name, ', '.join(x.mod.name for x in depends) )
    
    def minihook(count, blocksize, totalsize):
        dl = count * blocksize
        dlkb = dl / 1024
        totalkb = totalsize / 1024
        percent = int(( float(dl) / totalsize) * 100)
        print "\r  %s%% - %s kb / %s kb" % (percent, dlkb, totalkb),
    
    if not os.path.exists(args.dldir):
        print "Creating download folder '%s'" % args.dldir
        os.mkdir(args.dldir)
    
    print "Starting downloads.."
    
    for i, m in enumerate(downloadlist):
        path = os.path.join(args.dldir, m.mod.filename)
        print " Downloading %s [%s/%s]" % (m.mod.name, i+1, len(downloadlist))
        if os.path.exists(path):
            print "  File already exists, skipping", 
        else:
            urllib.urlretrieve(m.get_url(), path, minihook)
        print ""
        if not m.check_file(path, True):
            print "  !WARNING! File for '%s' seem to be corrupted!" % m.mod.name
        
def show_filedata(mdb, args):
    print {
        "filehash": moddb.create_filehash(args.extra),
        "filesize": os.stat(args.extra).st_size,
    }

F = {
    "add" : addservice,
    "search": search,
    "update": update,
    "show": info,
    "download": download,
    "filedata": show_filedata,
}

def main():
    mdb = moddb.ModDb()
    args = create_argparse()
    F[args.module](mdb, args)

if __name__ == "__main__":
    main()