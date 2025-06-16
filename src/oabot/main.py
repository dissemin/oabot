# -*- encoding: utf-8 -*-

from wikiciteparser.parser import parse_citation_template
from urllib.parse import urlencode
from urllib.parse import urlparse
import mwparserfromhell
import requests
import json
import codecs
import sys
import urllib.request, urllib.parse, urllib.error
from unidecode import unidecode
import re
from datetime import datetime
from copy import deepcopy
import os
from .arguments import template_arg_mappings, get_value
from .ranking import sort_links, is_blacklisted, is_no_subscription
from .settings import *
from .ondiskcache import OnDiskCache
from .classifier import AcademicPaperFilter
import hashlib
from time import sleep

urls_cache = OnDiskCache('urls_cache.pkl')
paper_filter = AcademicPaperFilter()

SESSION = requests.Session()
SESSION.headers.update({'User-Agent': OABOT_USER_AGENT})

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
        self.orig_string = str(self.template)
        r = hashlib.md5()
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

    def propose_change(self, only_doi=True):
        """
        Fetches open urls for that template and proposes a change
        """
        reference = parse_citation_template(self.template)
        tpl_name = str(self.template.name).lower().strip()
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
            if already_oa_param in ['doi']:
                # We'll need to double check the publisher URL.
                pass
            elif already_oa_param in ['hdl']:
                # We still want to add PMC if available, as hdl-access does not autolink.
                pass
            else:
                # The status quo is good enough.
                return

        # If the template is marked with |registration= or |subscription=,
        # maybe an editor tried to find a better version or maybe not.
        if ((get_value(self.template, 'subscription')
            or get_value(self.template, 'registration')) in
            ['yes','y','true']):
            self.classification = 'registration_subscription'

        # Set paper_object to be empty; we no longer have a source for it
        # since Dissemin closed.
        paper_object = {}
        # Try to get a free link
        doi = reference.get('ID_list', {}).get('DOI')
        try:
            link, oa_status = get_oa_link(paper=paper_object, doi=doi, only_unpaywall=only_doi)
        except requests.exceptions.RequestException:
            sleep(60)
            return

        # TODO: Reconsider adding bronze OA if it ever becomes possible to remove doi-access=free
        if oa_status in ['gold', 'hybrid']:
            self.classification = 'already_open'
            if doi and not already_oa_param:
                self.proposed_change = "doi-access=free|"
                self.proposed_link = "https://doi.org/{}".format(doi)

        # Continue either way as we may want to add hdl, pmc

        if not link:
            self.classification = 'not_found'
            if oa_status == "closed":
                self.proposed_change = ""
                if get_value(self.template, 'doi-access') in ['free']:
                    # There is no OA link but the DOI was previously considered OA.
                    # This was probably en ephemeral bronze OA paper.
                    # Remove the previous doi-access statement.
                    self.proposed_change += "doi-access=|"
            old_url = get_value(self.template, 'url')
            if old_url and "http" in old_url and not get_value(self.template, 'url-access'):
                if oa_status == "closed":
                    if is_no_subscription(old_url):
                        self.classification = 'subscription_ignored'
                    else:
                        # Probably the existing link is closed.
                        if is_blacklisted(old_url):
                            # Catch DOIs which redirect to a redirect, like linkinghub.elsevier.com
                            self.classification = 'registration_subscription'
                            self.proposed_change += "url-access=subscription|"
                        else:
                            # Ignore links which are not publisher links
                            try:
                                head = SESSION.head('https://doi.org/{}'.format(doi), timeout=1)
                            except requests.exceptions.RequestException:
                                print("WARNING: Request to doi.org failed")
                                head = None
                            if head and head.headers.get('Location', None) and urlparse(head.headers.get('Location', None)).hostname not in old_url:
                                # The old URL may be a repository link which Unpaywall forgot.
                                self.classification = 'subscription_ignored'
                                self.keep_existing_url(old_url)
                            else:
                                self.classification = 'registration_subscription'
                                self.proposed_change += "url-access=subscription|"
                        
                elif oa_status == "unknown":
                    # We queried Dissemin on top of Unpaywall and no result
                    # TODO: We should never get here since Dissemin was removed.
                    self.classification = 'subscription_ignored'
            else:
                # Nothing to see? Publisher URLs may need correction.
                pass
            return

        # We found an OA link!
        self.proposed_link = link
        # If the parameter is not present yet, add it
        self.classification = 'link_added'

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
                # TODO: Unused variable?
                change['new_'+argmap.name] = (match,link)

                self.classification = 'already_present'
                if argmap.name == 'hdl' and not self.template.has('hdl-access'):
                    self.proposed_change += "hdl-access=free|"
                    # don't change anything else
                    # TODO: Consider still adding PMC if available
                    return
                if argmap.name == 'url':
                    # We may want to change the URL. Propose it after cleanup.
                    for param in ['url-access', 'url-status', 'archive-url', 'archive-date', 'archiveurl', 'archivedate', 'accessdate']:
                        # Override existing URL archival parameters only if present.
                        if self.template.has(param):
                            self.proposed_change += f"{param}=|"
                else:
                    # Do not override existing parameters.
                    return

            if argmap.is_id:
                self.proposed_change += 'id={{%s|%s}}|' % (argmap.name,match)
            else:
                self.proposed_change += '%s=%s|' % (argmap.name,match)
                if argmap.name == 'hdl':
                    self.proposed_change += "hdl-access=free|"
            break

        # If we are going to add an URL, check it's not probably redundant
        if self.proposed_change.startswith('url'):
            hdl = get_value(self.template, 'hdl')
            old_url = get_value(self.template, 'url')
            if old_url:
                old_url = old_url.strip()
                self.keep_existing_url(old_url)
                # Nothing left to check. The new link seems good to use.
                self.classification = 'link_replaced'
            if hdl and hdl in self.proposed_change:
                # Don't actually add the URL but mark the hdl as seemingly OA
                # and hope that the templates will later linkify it
                self.classification = "already_open"
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

    def keep_existing_url(self, url):
        """
        Check existing URL and discard changes if the current URL is good enough.
        """
        if not url:
            return

        # Avoid proposing e.g. a direct PDF URL from the same domain we already link
        if urlparse(url).hostname in self.proposed_change:
            self.proposed_change = ""
            self.classification = "already_open"
            return True

        try:
            r = SESSION.head(url, timeout=5, allow_redirects=True)
        except requests.exceptions.RequestException:
            r = None
        # Avoid changing an URL which already clearly points to an open PDF
        if r and int(r.headers.get('Content-Length', 0)) > 10000 and 'pdf' in r.headers.get('Content-Type', ''):
            self.proposed_change = ""
            self.classification = "already_open"
            return True

        return False

def remove_diacritics(s):
    return unidecode(s) if type(s) == str else s

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

    # We no longer call Dissemin
    candidate_urls = []

    # Try OAdoi/Unpaywall, if we have a DOI
    # (It finds full texts that Dissemin does not, so it's always good to have!)
    oa_status = None
    if doi:
        resp = None
        attempts = 0
        while resp is None:
            email = '{}@{}.in'.format('contact', 'dissem')
            try:
                req = requests.get('https://api.unpaywall.org/v2/:{}'.format(doi), params={'email':email}, timeout=10)
                resp = req.json()
                sleep(0.15)
            except ValueError:
                sleep(10)
                attempts += 1
                if attempts >= 3:
                    break
                else:
                    continue

        # Default to Unpaywall's OA status
        if resp:
            oa_status = resp.get('oa_status', None)
        if oa_status and oa_status == "closed" and only_unpaywall:
            # Just give up when Unpaywall doesn't know an OA location.
            return None, "closed"

        # If we have Unpaywall data, use it and prefer identifiers.
        boa = resp.get('best_oa_location', None)
        if boa and boa['host_type'] == 'publisher':
            # If we're coming from the DOI rather add doi-access=free
            # Avoid getting publisher URLs from Unpaywall or elsewhere
            if len(resp.get('oa_locations', [])) <= 1:
                return False, oa_status

        for oa_location in resp.get('oa_locations') or []:
            landing_page = oa_location.get('url_for_landing_page', '')
        # In case there's a handle, prefer the landing page URL over the PDF link
        # as the hdl URL will be converted to the hdl parameter.
            if 'hdl.handle.net' in landing_page:
                candidate_urls.append(landing_page)
        # T354471: If the URL comes from CiteSeerX, use the landing page URL
        # so that other arxiv/identifier matches have a chance to rank higher
        # and override any incorrect matches by title on the CiteSeerX side.
            if 'citeseerx.ist.psu.edu' in landing_page:
                candidate_urls.append(landing_page.replace("/summary", "/download"))
        # T354472: Reduce chances of incorrect title matches on PMC
        # FIXME: Unpaywall removed the evidence field in 2025
            if (landing_page.startswith("https://europepmc.org") or landing_page.startswith("https://www.ncbi.nlm.nih.gov/pmc/")) and oa_location.get("evidence") == "oa repository (via OAI-PMH title and first author match)" and int(resp.get("year", 2000)) < 2000:
                continue

            if oa_location.get('url') and oa_location.get('host_type') != 'publisher':
                candidate_urls.append(oa_location['url'])

    # Full text detection is not always accurate, so we try to pick
    # the URL which is most useful for citation templates and we
    # double check that it's still up.
    for url in sort_links(candidate_urls):
        if url:
            try:
                head = SESSION.head(url, timeout=10)
                head.raise_for_status()
                if head.status_code < 400 and 'Location' in head.headers and urllib.parse.urlparse(head.headers['Location']).path == '/':
                    # Redirects to main page: fake status code, should be not found
                    continue
                if not is_blacklisted(url):
                    try:
                        return url, "open"
                    except NameError:
                        # Probably we had no DOI to check Unpaywall for
                        return url, None
            except requests.exceptions.RequestException:
                continue

    if oa_status:
        return None, oa_status

    # TODO: We should never get here with Unpaywall.
    return None, "unknown"

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
    page = list(js.get('query',{}).get('pages',{}).values())[0]
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


