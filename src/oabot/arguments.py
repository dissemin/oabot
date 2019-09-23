# -*- encoding: utf-8 -*-

from __future__ import unicode_literals
import re

# helper
def get_value(template, param):
    if template.has(param, ignore_empty=True):
        return unicode(template.get(param).value).strip()

##############
# Edit logic #
##############

# This section defines the behaviour of the bot.

# See template_arg_mappings below for a list of examples of this class
class ArgumentMapping(object):
    def __init__(self, name, regex, is_id=False, alternate_names=[],
                    group_id=1, always_free=False, custom_access=False):
        """
        :param name: the parameter slot in which the identifier is stored (e.g. arxiv)
        :para is_id: if this parameter is true, we will actually store the identifier in |id={{name| … }} instead of |name.
        :par  regex: the regular expression extract on the URLs that trigger this mapping. The first parenthesis-enclosed group in these regular expressions should contain the id.
        :para alternate_names: alternate parameter slots to look out for - we will not add any identifier if one of them is non-empty.
        :para group_id: position of the identifier in the regex
        :para always_free: the parameter denotes links which are always free
        """
        self.name = name
        self.regex = re.compile(regex)
        self.is_id = is_id
        self.alternate_names = alternate_names
        self.group_id = group_id
        self.always_free = always_free
        self.custom_access = custom_access

    def get(self, template):
        """
        Get the argument value in a particular template.
        If the parameter should be input as |id=, we return the full
        value of |id=. # TODO refine this
        """
        val = None
        if self.is_id:
            val = get_value(template, 'id')
        else:
            val = get_value(template, self.name)
        for aid in self.alternate_names:
            val = val or get_value(template, aid)
        return val

    def present(self, template):
        return self.get(template) != None

    def present_and_free(self, template):
        """
        When the argument is in the template, and it links to a full text
        according to the access icons
        """
        def strip(s):
            return s.strip() if s else None
        return (
                self.present(template) and
                   ( self.always_free
                    or
                   ( self.custom_access and
                    get_value(template, self.name+'-access') == 'free')
                    )
                )

    def normalise(self, url):
        """
        Convert the URL into an equivalent which is more suitable for comparison and ranks.
        """
        if 'babel.hathitrust.org' in url:
            return re.sub(r"https://babel\.hathitrust\.org/cgi/imgsrv/download/pdf\?id=([a-z]+\.[0-9]+).*",
                          r"https://hdl.handle.net/2027/\1",
                          url)
        return url

    def extract(self, url):
        """
        Extract the parameter value from the URL, or None if it does not match
        """
        url = self.normalise(url)
        match = self.regex.match(url)
        if not match:
            return None
        return match.group(self.group_id)

url_pdf_extension_re = re.compile(r'.*\.pdf([\?#].*)?$', re.IGNORECASE)
class UrlArgumentMapping(ArgumentMapping):
    def present_and_free(self, template):
        val = self.get(template)
        if val:
            match = url_pdf_extension_re.match(val.strip())
            if match:
                return True
        return False

doi_argument = ArgumentMapping(
        'doi',
        r'https?://(dx\.)?doi\.org/([^ ]*)',
        group_id=2,
        alternate_names=['DOI'],
        custom_access=True)

hdl_argument = ArgumentMapping(
        'hdl',
        r'https?://hdl\.handle\.net/([^ ]*)',
        alternate_names=['HDL'],
        custom_access=True)

arxiv_argument = ArgumentMapping(
        'arxiv',
        r'https?://arxiv\.org/(abs|pdf)/(\d+\.[\d]+|[a-z-]+/\d+)(v\d+)?(\.pdf)?',
        group_id=2,
        alternate_names=['eprint','ARXIV','arXiv'],
        always_free=True)

pmc_argument = ArgumentMapping(
        'pmc',
        r'https?://www\.ncbi\.nlm\.nih\.gov/pmc/articles/PMC([^/]*)/?',
        alternate_names=['PMC'],
        always_free=True)
eupmc_argument = ArgumentMapping(
        'pmc',
        r'https?://europepmc.org/articles/pmc([0-9]+)[^0-9]*',
        alternate_names=['PMC'],
        always_free=True)
pmid_argument = ArgumentMapping(
        'pmid',
        r'https?://www\.ncbi\.nlm\.nih\.gov/pubmed/([^/]*)[^0-9]*',
        alternate_names=['PMID'],
        custom_access=True)
eupmid_argument = ArgumentMapping(
        'pmid',
        r'https?://europepmc.org/abstract/med/([0-9]+)[^0-9]*',
        alternate_names=['PMID'],
        custom_access=True)
citeseerx_argument = ArgumentMapping(
        'citeseerx',
        r'https?://citeseerx\.ist\.psu\.edu/viewdoc/(summary|download)\?doi=([0-9.]*)(&.*)?',
        alternate_names=['CITESEERX'],
        group_id=2,
        always_free=True)
url_argument =  UrlArgumentMapping(
        'url',
        r'(.*)',
        alternate_names=['URL'])

template_arg_mappings = [
    doi_argument,
    hdl_argument,
    arxiv_argument,
    pmc_argument,
    eupmc_argument,
    pmid_argument,
    eupmid_argument,
    citeseerx_argument,
    url_argument,
]

