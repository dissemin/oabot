import pywikibot
import sys
import requests
from app import get_proposed_edits, app
import threading
from time import sleep

def worker(title=None):
    try:
        get_proposed_edits(title, False, True)
    except:
        pass

def prefill_cache(max_pages=5000, starting_page=None):
    site = pywikibot.Site()
    cs1 = pywikibot.Page(site, 'Module:Citation/CS1')
    count = 0
    starting_page_seen = starting_page is None
    for p in cs1.embeddedin(namespaces=[0]):
        print(p.title().encode('utf-8'))
        if p.title() == starting_page:
           starting_page_seen = True
           continue
        if count >= max_pages:
            break
        if not starting_page_seen:
            continue
        try:
            threading.Thread(target=worker, args=[p.title()]).start()
        except:
            sleep(60)
        count += 1
        sleep(0.2)

if __name__ == '__main__':
    if len(sys.argv) >= 2:
        prefill_cache(5000000, sys.argv[1])
    else:
        prefill_cache(5000000)
