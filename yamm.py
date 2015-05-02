#! /usr/bin/python
# -*- mode: python; coding: utf-8 -*-
import logging

logging.basicConfig(level=logging.INFO)

from lib import moddb

import argparse
def create_argparse():
    parser = argparse.ArgumentParser(description='Yet Another Mod Manager')
    parser.add_argument('module', metavar='MODULE', help='Submodule', choices=F)
    parser.add_argument('extra', metavar='submodule', help='Data for submodule', nargs="?")
    args = parser.parse_args()
    return args


def addservice(mdb, service):
    if service:
        try:
            # "http://terra.thelazy.net/yamm/mods.json"
            mdb.add_service(service)
        except:
            logging.info("Could not add service (already added?)")

def search(mdb, text):
    if text:
        for x in mdb.search(text):
            print "%s - %s" % (x.mod.name, x.mod.description)

def update(mdb, throwaway):
    mdb.update_services()

def info(mdb, modname):
    mod = mdb.get_module(modname)
    print mod.mod.name
    print mod.mod.description
    print "Version %s" % mod.mod.version
    print "Download URL : %s" % mod.get_url()
    depends = mod.get_dependency_mods()
    if depends:
        print "Depends on:"
        for x in depends:
            print " %s | %s" % (x.mod.name, x.get_url())
    
F = {
    "add" : addservice,
    "search": search,
    "update": update,
    "show": info,
}

def main():
    mdb = moddb.ModDb()
    args = create_argparse()
    F[args.module](mdb, args.extra)
    

if __name__ == "__main__":
    main()