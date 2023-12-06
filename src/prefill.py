#!/usr/bin/python2
# -*- coding: utf-8  -*-
""" Script to get OAbot suggestions for all English Wikipedia pages """
#
# (C) CAPSH, 2020
#
# Distributed under the terms of the MIT license.
#

from multiprocessing import Pool, TimeoutError
import pywikibot
import sys
import random
import requests
from app import get_proposed_edits, app
from time import sleep


def worker(title=None):
    print(title)
    try:
        get_proposed_edits(page_name=title,
                           force=False,
                           follow_redirects=True,
                           only_doi=True)
    except:
        sleep(60)
    sleep(0.1)


def prefill_cache(max_pages=5000):
    print("INFO: Getting the list of pages to work on")
    site = pywikibot.Site()
    # pages = pywikibot.Page(site, 'Module:Citation/CS1'
    #                        ).embeddedin(namespaces=[0])
    pages = pywikibot.Page(site, 'Doi (identifier)'
                           ).backlinks(namespaces=[0])
    count = 0
    sortedpages = []
    # TODO: Use timestamp to allow working only on recently updated pages
    for p in pages:
        sortedpages.append(p.title())
    random.shuffle(sortedpages)

    print(("INFO: Will start working on {} pages".format(len(sortedpages))))
    # Takes almost 1 GB of RAM. With 20 processes, more than 1 CPU is needed.
    with Pool(processes=10) as pool:
        result = pool.map_async(worker, sortedpages, 100)
        while True:
            # FIXME: Doesn't respect max_pages
            sleep(1)
            try:
                print(result.get(12000))
            except TimeoutError:
                print("WARNING: One chunk timed out")
            except StopIteration:
                print("INFO: We run out of results to print")

if __name__ == '__main__':
    if len(sys.argv) >= 2:
        prefill_cache(5000000, sys.argv[1])
    else:
        prefill_cache(5000000)
