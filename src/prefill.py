#!/usr/bin/python2
# -*- coding: utf-8  -*-
""" Script to get OAbot suggestions for all English Wikipedia pages """
#
# (C) CAPSH, 2020
#
# Distributed under the terms of the MIT license.
#

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
        sortedpages.append(p.title().encode('utf-8'))
    random.shuffle(sortedpages)

    print(("INFO: Will start working on {} pages".format(len(sortedpages))))
    pool = multiprocessing.Pool(5)
    for p in sortedpages:
        worker(p)

if __name__ == '__main__':
    if len(sys.argv) >= 2:
        prefill_cache(5000000, sys.argv[1])
    else:
        prefill_cache(5000000)
