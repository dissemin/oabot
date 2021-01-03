#!/usr/bin/python2
# -*- coding: utf-8  -*-
""" Script to run the OAbot suggestion creation on all relevant English Wikipedia pages """
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
    print(p.title().encode('utf-8'))
    try:
        get_proposed_edits(page_name=p.title(), force=False, follow_redirects=True, only_doi=True)
    except:
        sleep(60)

def prefill_cache(max_pages=5000):
    site = pywikibot.Site()
    # pages = pywikibot.Page(site, 'Module:Citation/CS1').embeddedin(namespaces=[0])
    pages = pywikibot.Page(site, 'Digital object identifier').backlinks(namespaces=[0])
    count = 0
    sortedpages = []
    for p in pages:
        sortedpages.append(p)
    random.shuffle(sortedpages)
    for p in sortedpages:
        if count >= max_pages:
            break
        count += 1
        sleep(1.5)

if __name__ == '__main__':
    if len(sys.argv) >= 2:
        prefill_cache(5000000, sys.argv[1])
    else:
        prefill_cache(5000000)
