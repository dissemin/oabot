# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
from wikiciteparser.parser import parse_citation_template
from urllib import urlencode
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
from ranking import sort_links
from settings import *
from ondiskcache import OnDiskCache
from classifier import AcademicPaperFilter
import md5

urls_cache = OnDiskCache('urls_cache.pkl')
paper_filter = AcademicPaperFilter()

rg_re = re.compile('(https?://www\.researchgate\.net/)(.*)(publication/[0-9]*)_.*/links/[0-9a-f]*.pdf')


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

    def is_https(self):
        return self.proposed_link and self.proposed_link.startswith('https')

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

    def propose_change(self):
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

        dissemin_paper_object = get_dissemin_paper(reference)

        # Otherwise, try to get a free link
        link = get_oa_link(dissemin_paper_object)
        if not link:
            self.classification = 'not_found'
            return

        # We found an OA link!
        self.proposed_link = link

        self.proposed_link_policy = get_paper_values(dissemin_paper_object, 'policy')
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
                # don't change anything
                break

            # If the parameter is not present yet, add it
            self.classification = 'link_added'

            if argmap.is_id:
                self.proposed_change = 'id={{%s|%s}}' % (argmap.name,match)
            else:
                self.proposed_change = '%s=%s' % (argmap.name,match)
            break

    def update_template(self, change):
        """
        Given a change of the form "param=value", add it to the template
        """
        bits = change.split('=')
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
    title = reference.get('Title')
    authors = reference.get('Authors', [])
    date = reference.get('Date')

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

    req = requests.post('https://dissem.in/api/query',
                        json=args,
                        headers={'User-Agent':OABOT_USER_AGENT})

    resp = req.json()  
    paper_object = resp.get('paper', {})

    return paper_object

def get_paper_values(paper, attribute):

    for record in paper.get('records',[]):
        if record.get(attribute):
            return record.get(attribute)
    
    return None

def get_oa_link(paper):

    doi = paper.get('doi')
    if doi is not None:
        doi = "/".join(doi.split("/")[-2:])

    # Dissemin's full text detection is not always accurate, so
    # we manually go through each url for the paper and check
    # if it is free to read.

    # if we want more accurate (but slower) results
    # we can check availability manually:

    candidate_urls = sort_links([
        record.get('pdf_url') for record in
        paper.get('records',[])  if record.get('pdf_url')
    ])
    for url in sort_links(candidate_urls):
        if url:
            return url

    # then, try OAdoi
    # (OAdoi finds full texts that dissemin does not, so it's always good to have!)
    if doi:
        resp = None
        attempts = 0
        while resp is None:
            email = '{}@{}.in'.format('contact', 'dissem')
            try:
                req = requests.get('https://api.oadoi.org/v2/:{}'.format(doi), {'email':email})
                resp = req.json()
            except ValueError:
                from time import sleep
                sleep(10)
                attempts += 1
                if attempts >= 3:
                    return None
                else:
                    continue

        best_oa = (resp.get('best_oa_location') or {})
        if best_oa.get('host_type') == 'publisher':
            return None
        if best_oa.get('url'):
            # try to HEAD the url just to check it's still there
            try:
                url = best_oa['url']
                head = requests.head(url)
                head.raise_for_status()
                return url
            except requests.exceptions.RequestException:
                return None

def add_oa_links_in_references(text, page):
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
        edit.propose_change()
        yield edit

def get_page_over_api(page_name):
    r = requests.get('https://en.wikipedia.org/w/api.php', params={
        'action':'query',
        'titles':page_name,
        'prop':'revisions',
        'rvprop':'content',
        'format':'json',},
        headers={'User-Agent':OABOT_USER_AGENT})
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


