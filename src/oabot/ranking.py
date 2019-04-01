# -*- encoding: utf-8 -*-

from __future__ import unicode_literals
import re

rg_re = re.compile('(https?://www\.researchgate\.net/)(.*)(publication/[0-9]*)_.*/links/[0-9a-f]*.pdf')

# This section defines a priority order on the links retrieved from APIs
domain_priority = {
        'doi.org': 50,                # Links to the publisher's version in most of the cases
        'dx.doi.org': 50,                # Links to the publisher's version in most of the cases
        'ncbi.nlm.nih.gov': 40, # PubMed Central: official version too
        'arxiv.org' : 30,        # Curated repository
        'hdl.handle.net': 20,        # Institutional repositories
        'citeseerx.ist.psu.edu': 10, # Preprints crawled on the web
}
# Academia.edu and ResearchGate are not ranked here, they are at an equal (lowest) priority
domain_blacklist = [
    'www.researchgate.net',
    # Publisher links are redundant with DOI links and often become inaccessible.
    'ams.org',
    'annals.org',
    'asm.org',
    'babel.hathitrust.org',
    'bioone.org',
    'bloodjournal.org',
    'cell.com',
    'doaj.org',
    'doi.org',
    'erudit.org',
    'iop.org',
    'jbc.org',
    'nature.com',
    'oup.com',
    'rsc.org'
    'sciencemag.org',
    'sciencedirect.com',
    'scitation.org',
    'link.springer.com',
    'tandfonline.com',
    'thelancet.com',
    'thieme-connect.de',
    'journals.uchicago.edu',
    'onlinelibrary.wiley.com',
]

domain_re = re.compile(r'\s*(https?|ftp)://(([a-zA-Z0-9-_]+\.)+[a-zA-Z]+)(:[0-9]+)?/?')
def extract_domain(url):
    match = domain_re.match(url)
    if match:
        return match.group(2)

def link_rank(url):
    return (- domain_priority.get(extract_domain(url), 0))

def sort_links(urls):
    return sorted(urls, key=link_rank)

def is_blacklisted(url):
    subdomain = extract_domain(url)
    for domain in domain_blacklist:
        if domain in subdomain:
            return True
    return False
