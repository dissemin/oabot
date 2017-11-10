# -*- encoding: utf-8 -*-

from __future__ import unicode_literals
import re


# This section defines a priority order on the links retrieved from APIs
domain_priority = {
	'doi.org': 50,		# Links to the publisher's version in most of the cases
	'dx.doi.org': 50,		# Links to the publisher's version in most of the cases
	'ncbi.nlm.nih.gov': 40, # PubMed Central: official version too
	'arxiv.org' : 30,	# Curated repository
	'hdl.handle.net': 20,	# Institutional repositories
	'citeseerx.ist.psu.edu': 10, # Preprints crawled on the web
}
# Academia.edu and ResearchGate are not ranked here, they are at an equal (lowest) priority

domain_re = re.compile(r'\s*(https?|ftp)://(([a-zA-Z0-9-_]+\.)+[a-zA-Z]+)/?')
def extract_domain(url):
    match = domain_re.match(url)
    if match:
	return match.group(2)

def link_rank(url):
    return (- domain_priority.get(extract_domain(url), 0))

def sort_links(urls):
    return sorted(urls, key=link_rank)

