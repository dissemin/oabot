# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
from wikiciteparser.parser import parse_citation_template
from urllib import urlencode
try:
    import urlparse
except ImportError:
    from urllib.parse import urlparse
import mwparserfromhell
import requests
import json
import codecs
import sys
import urllib
from unidecode import unidecode
import re
from datetime import datetime
from copy import deepcopy
import os
from arguments import template_arg_mappings, get_value
from ranking import sort_links, is_blacklisted
from settings import *
from ondiskcache import OnDiskCache
from classifier import AcademicPaperFilter
import md5
from time import sleep
from Levenshtein import ratio

urls_cache = OnDiskCache('urls_cache.pkl')
paper_filter = AcademicPaperFilter()

class TemplateEdit(object):
    """
    This represents a proposed change (possibly empty)
    on a citation template
    """
    def __init__(self, tpl, page):
        """
        :param tpl: a mwparserfromhell template: the original template
                that we want to change
        """
        self.template = tpl
        self.orig_string = unicode(self.template)
        r = md5.md5()
        r.update(self.orig_string.encode('utf-8'))
        self.orig_hash = r.hexdigest()
        self.classification = None
        self.conflicting_value = ''
        self.proposed_change = ''
        self.proposed_link = None
        self.index = None
        self.page = page
        self.proposed_link_policy = None
        self.issn = None

    def json(self):
        return {
            'orig_string': self.orig_string,
            'orig_hash': self.orig_hash,
            'classification': self.classification,
            'conflicting_value': self.conflicting_value,
            'proposed_change': self.proposed_change,
            'proposed_link': self.proposed_link,
            'index': self.index,
            'policy': self.proposed_link_policy,
            'issn': self.issn,
        }

    def propose_change(self, only_doi=False):
        """
        Fetches open urls for that template and proposes a change
        """
        reference = parse_citation_template(self.template)
        tpl_name = unicode(self.template.name).lower().strip()
        if not reference or tpl_name in excluded_templates:
            self.classification = 'ignored'
            return

        sys.stdout.write('.')
        sys.stdout.flush()

        # First check if there is already a link to a full text
        # in the citation.
        already_oa_param = None
        already_oa_value = None
        for argmap in template_arg_mappings:
            if argmap.present_and_free(self.template):
                already_oa_param = argmap.name
                already_oa_value = argmap.get(self.template)

        change = {}

        # If so, we just skip it - no need for more free links
        if already_oa_param:
            self.classification = 'already_open'
            self.conflicting_value = already_oa_value
            return

        # --- Disabled for now ----
        # If the template is marked with |registration= or
        # |subscription= , let's assume that the editor tried to find
        # a better version themselves so it's not worth trying.
        if ((get_value(self.template, 'subscription')
            or get_value(self.template, 'registration')) in
            ['yes','y','true']):
            self.classification = 'registration_subscription'
            # return

        if only_doi:
            dissemin_paper_object = {}
        else:
            dissemin_paper_object = get_dissemin_paper(reference)

        # Otherwise, try to get a free link
        doi = reference.get('ID_list', {}).get('DOI')
        link = get_oa_link(paper=dissemin_paper_object, doi=doi, only_unpaywall=only_doi)
        if link is False:
            self.classification = 'already_open'
            if doi:
                self.proposed_change = "doi-access=free"
                self.proposed_link = "https://doi.org/{}".format(doi)
                return
            # TODO add the DOI suggested by Dissemin if missing. Needs some checks.
            # elif dissemin_paper_object.get('pdf_url') and 'doi.org' in dissemin_paper_object.get('pdf_url'):
            #    self.proposed_change = dissemin_paper_object.get('pdf_url')
            #    return
            else:
                return
        if not link:
            self.classification = 'not_found'
            return

        # We found an OA link!
        self.proposed_link = link

        if dissemin_paper_object:
            self.proposed_link_policy = get_paper_values(dissemin_paper_object, 'policy')
            # TODO: fetch from Unpaywall?
            self.issn = get_paper_values(dissemin_paper_object, 'issn')

        # Try to match it with an argument
        argument_found = False
        for argmap in template_arg_mappings:
            # Did the link we have got match that argument place?
            match = argmap.extract(link)
            if not match:
                continue

            argument_found = True

            # If this parameter is already present in the template:
            current_value = argmap.get(self.template)
            if current_value:
                change['new_'+argmap.name] = (match,link)

                #if argmap.custom_access:
                #    stats['changed'] += 1
                #    template.add(argmap.custom_access, 'free')
                #else:

                self.classification = 'already_present'
                if argmap.name == 'hdl':
                    self.proposed_change = "hdl-access=free"
                # don't change anything else
                break

            # If the parameter is not present yet, add it
            self.classification = 'link_added'

            if argmap.is_id:
                self.proposed_change = 'id={{%s|%s}}' % (argmap.name,match)
            else:
                self.proposed_change = '%s=%s' % (argmap.name,match)
                if argmap.name == 'hdl':
                    self.proposed_change += "|hdl-access=free"
            break

        # If we are going to add an URL, check it's not probably redundant
        if self.proposed_change.startswith('url='):
            hdl = get_value(self.template, 'hdl')
            if hdl and hdl in self.proposed_change:
                # Don't actually add the URL but mark the hdl as seemingly OA
                # and hope that the templates will later linkify it
                self.proposed_change = "hdl-access=free"

    def update_template(self, change):
        """
        Given a change of the form "param=value", add it to the template
        """
        bits = re.split('=', change, maxsplit=1)
        if len(bits) != 2:
            raise ValueError('invalid change')
        param = bits[0].lower().strip()
        value = bits[1].strip()
        
        # Escape various characters in Wikicode
        value = value.replace(' ', '%20')
        value = value.replace('|', '{{!}}')
        self.template.add(param, value)

def remove_diacritics(s):
    return unidecode(s) if type(s) == unicode else s

def get_dissemin_paper(reference):
    """
    Given a citation template (as parsed by wikiciteparser and a proposed link)
    get dissemin API information for that link
    """
    doi = reference.get('ID_list', {}).get('DOI')
    title = reference.get('Title', '')
    authors = reference.get('Authors', [])
    date = reference.get('Date', '')

    # CS1 represents unparsed authors as {'last':'First Last'}
    for i in range(len(authors)):
        if 'first' not in authors[i]:
            authors[i] = {'plain':authors[i].get('last','')}

    args = {
        'title':title,
        'authors':authors,
        'date':date,
        'doi':doi,
        }

    for retry in range(5):
        try:
            req = requests.post('https://dissem.in/api/query/',
                                json=args,
                                headers={'User-Agent':OABOT_USER_AGENT},
                                timeout=10)

            resp = req.json()
            paper_object = resp.get('paper', {})
            if not paper_object:
                return {}

            paper_year = paper_object.get("date", "")[:4]
            paper_authorlast = paper_object.get("authors")[0].get("name", {}).get("last", "")
            if date[:4] == paper_year and ratio(authors[0].get("last", ""), paper_authorlast) > 0.75:
                return paper_object
            else:
                # Fails a basic author/date check, ignore Dissemin record
                return {}
        except (ValueError, requests.exceptions.RequestException) as e:
            sleep(5)
            continue
        except IndexError:
            # The author names are not what expected, give up on a record match
            # TODO: could probably try harder
            return {}
    return {}

def get_paper_values(paper, attribute):

    for record in paper.get('records',[]):
        if record.get(attribute):
            return record.get(attribute)
    
    return None

def get_oa_link(paper, doi=None, only_unpaywall=True):

    if paper and not doi:
        doi = paper.get('doi')
        if doi is not None:
            doi = "/".join(doi.split("/")[-2:])

    dissemin_dois = set([ record.get('doi') for record in
                         paper.get('records',[]) if record.get('doi')  ])
    if len(dissemin_dois) > 2:
        # Do not use Dissemin suggestions: many DOIs suggest a risk of overmerged
        # records. https://github.com/dissemin/dissemin/issues/512
        candidate_urls = []
    else:
        # Get all the URLs which Dissemin considers to be full-text links
        candidate_urls = ([
            record.get('pdf_url') for record in
            paper.get('records',[])  if record.get('pdf_url')
        ])

    # Then, try OAdoi/Unpaywall
    # (It finds full texts that Dissemin does not, so it's always good to have!)
    if doi:
        resp = None
        attempts = 0
        while resp is None:
            email = '{}@{}.in'.format('contact', 'dissem')
            try:
                req = requests.get('http://api.unpaywall.org/v2/:{}'.format(doi), params={'email':email}, timeout=10)
                resp = req.json()
                sleep(0.15)
            except ValueError:
                sleep(10)
                attempts += 1
                if attempts >= 3:
                    break
                else:
                    continue

        if only_unpaywall:
            # Just rely on whichever URL Unpaywall considers the best location.
            if not resp['is_oa']:
                return None
            boa = resp['best_oa_location']
            if boa['host_type'] == 'publisher':
                # We're coming from the DOI so if anything add doi-access=free
                return False
            elif 'citeseerx.ist.psu.edu' in resp['best_oa_location']['url_for_landing_page']:
                # Use the CiteSeerX URL which gets converted to the parameter
                return resp['best_oa_location']['url_for_landing_page']
            else:
                if 'hdl.handle.net' in boa['url_for_landing_page']:
                    url = boa['url_for_landing_page']
                else:
                    url = boa['url']
                if not is_blacklisted(url):
                    return url

        for oa_location in resp.get('oa_locations') or []:
            if oa_location.get('url') and oa_location.get('host_type') != 'publisher':
                candidate_urls.append(oa_location['url'])

    # TODO If Dissemin considers this gold OA, it only needs a doi-access=free
    #if paper.get('classification', 'UNK') == 'OA':
    #    return False

    # Full text detection is not always accurate, so we try to pick
    # the URL which is most useful for citation templates and we
    # doule check that it's still up.
    for url in sort_links(candidate_urls):
        if url:
            try:
                head = requests.head(url, timeout=10)
                head.raise_for_status()
                if head.status_code < 400 and 'Location' in head.headers and urlparse.urlparse(head.headers['Location']).path == '/':
                    # Redirects to main page: fake status code, should be not found
                    continue
                if not is_blacklisted(url):
                    return url
            except requests.exceptions.RequestException:
                continue

def add_oa_links_in_references(text, page, only_doi=False):
    """
    Main function of the bot.

    :param text: the wikicode of the page to edit
    :returns: a tuple: the new wikicode, the list of changed templates,
            and edit statistics
    """
    wikicode = mwparserfromhell.parse(text)

    for index, template in enumerate(wikicode.filter_templates()):
        edit = TemplateEdit(template, page)
        edit.index = index
        edit.propose_change(only_doi)
        yield edit

def get_page_over_api(page_name):
    r = requests.get('https://en.wikipedia.org/w/api.php', params={
        'action':'query',
        'titles':page_name,
        'prop':'revisions',
        'rvprop':'content',
        'format':'json',},
        headers={'User-Agent':OABOT_USER_AGENT},
        timeout=10)
    r.raise_for_status()
    js = r.json()
    page = js.get('query',{}).get('pages',{}).values()[0]
    pagid = page.get('pageid', -1)
    if pagid == -1:
        raise ValueError("Invalid page.")
    text = page.get('revisions',[{}])[0]['*']
    return text

def bot_is_allowed(text, user):
    """
    Taken from https://en.wikipedia.org/wiki/Template:Bots
    For bot exclusion compliance.
    """
    user = user.lower().strip()
    text = mwparserfromhell.parse(text)
    for tl in text.filter_templates():
        if tl.name in ('bots', 'nobots'):
            break
    else:
        return True
    for param in tl.params:
        bots = [x.lower().strip() for x in param.value.split(",")]
        if param.name == 'allow':
            if ''.join(bots) == 'none': return False
            for bot in bots:
                if bot in (user, 'all'):
                    return True
        elif param.name == 'deny':
            if ''.join(bots) == 'none': return True
            for bot in bots:
                if bot in (user, 'all'):
                    return False
    return True


