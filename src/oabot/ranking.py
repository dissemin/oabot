# -*- encoding: utf-8 -*-

from __future__ import unicode_literals
import re

rg_re = re.compile('(https?://www\.researchgate\.net/)(.*)(publication/[0-9]*)_.*/links/[0-9a-f]*.pdf')

# This section defines a priority order on the links retrieved from APIs
domain_priority = {
        'doi.org': 50,                # Links to the publisher's version in most of the cases
        'dx.doi.org': 50,                # Links to the publisher's version in most of the cases
        'ncbi.nlm.nih.gov': 40, # PubMed or PubMed Central: official version too
        'arxiv.org' : 30,        # Curated repository
        'hdl.handle.net': 20,        # Institutional repositories
        'citeseerx.ist.psu.edu': 10, # Preprints crawled on the web
}
# Academia.edu and ResearchGate are not ranked here, they are at an equal (lowest) priority
domain_blacklist = [
    'www.researchgate.net',
    # Publisher links are redundant with DOI links and often become inaccessible.
    'aaccjnls.org',
    'aacrjournals.org',
    'aanda.org',
    'aappublications.org',
    'ahajournals.org',
    'ajol.info',
    'ajronline.org',
    'americanarchivist.org',
    'amjbot.org',
    'ams.org',
    'annals.org',
    'annualreviews.org',
    'asm.org',
    'aspetjournals.org',
    'babel.hathitrust.org',
    'biochemsoctrans.org',
    'biologists.org',
    'bioone.org',
    'bloodjournal.org',
    'cambridge.org',
    'cell.com',
    'cshlp.org',
    'degruyter.com',
    'diabetesjournals.org',
    'dl.acm.org',
    'doaj.org',
    'doi.org',
    'ersjournals.com',
    'erudit.org',
    'euppublishing.com',
    'fasebj.com',
    'futuremedicine.com',
    'healio.com',
    'healthaffairs.org',
    'informs.org',
    'int-res.com',
    'intlpress.com',
    'iop.org',
    'jamanetwork.com',
    'jbc.org',
    'jimmunol.org',
    'jlr.org',
    'jneurosci.org',
    'journal.csj.jp',
    'journals.ametsoc.org',
    'journals.iucr.org',
    'journals.lww.com',
    'journals.sagepub.com',
    'journals.uchicago.edu',
    'jwildlifedis.org',
    'karger.com',
    'link.aps.org',
    'link.springer.com',
    'microbiologyresearch.org',
    'movementsciencemedia.org',
    'mscand.dk',
    'msp.org',
    'mdpi.com',
    'nature.com',
    'nejm.org',
    'neurology.org',
    'nrcresearchpress.com',
    'oceanrep.geomar.de',
    'onlinelibrary.wiley.com',
    'oup.com',
    'parasite-journal.org',
    'physiology.org',
    'plos.org',
    'plosone.org',
    'pubs.acs.org',
    'pubs.aeaweb.org',
    'rcpsych.org',
    'reproduction-online.org',
    'royalsocietypublishing.org',
    'rsc.org',
    'sciencedirect.com',
    'sciencemag.org',
    'scitation.org',
    'spandidos-publications.com',
    'springer.com',
    'tandfonline.com',
    'thelancet.com',
    'thieme-connect.de',
    'ucpress.edu',
    # Repositories with too many false positives
    'library.tue.nl',
    'orbit.dtu.dk',
    'pangaea.de',
    'scielo.br',
]

domain_re = re.compile(r'\s*(https?|ftp)://(([a-zA-Z0-9-_]+\.)+[a-zA-Z]+)(:[0-9]+)?/?')
def extract_domain(url):
    match = domain_re.match(url)
    if match:
        return match.group(2)

def link_rank(url):
    if 'www.ncbi.nlm.nih.gov/pubmed/' in url or 'europepmc.org/abstract/med/' in url:
        return 20
    return (- domain_priority.get(extract_domain(url), 0))

def sort_links(urls):
    return sorted(urls, key=link_rank)

def is_blacklisted(url):
    if 'estringido.pdf' in url:
        return True
    subdomain = extract_domain(url)
    for domain in domain_blacklist:
        if domain in subdomain:
            return True
    return False
