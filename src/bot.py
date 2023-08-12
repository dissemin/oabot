from app import *
from time import sleep
import pywikibot
from pywikibot.exceptions import *
from requests.exceptions import *

def run_bot(template_param, access_token=None, site=None, max_edits=100000):
    cached_pages = list_cache_contents('bot_cache/')
    edits_made = 0
    for page_name in cached_pages:
        print(page_name)
        cache_fname = 'bot_cache/'+to_cache_name(page_name)
        with open(cache_fname, 'r') as f:
            page_json = json.load(f)
        if run_bot_on_page(page_json, template_param, access_token=access_token, site=site):
            edits_made += 1
            sleep(10)
        if edits_made >= max_edits:
            return

def run_bot_on_page(proposed_edits, template_param, access_token=None, site=None):
    page_name = proposed_edits['page_name']
    proposed_additions = {}
    ids_touched = []

    for edit in proposed_edits['proposed_edits']:
        template_hash = edit['orig_hash']
        change = edit['proposed_change']
        match = re.findall(r'^' + template_param, change)
        if match:
            proposed_additions[template_hash] = change
            ids_touched += match

    if len(proposed_additions) < 1:
        return False

    try:
        app.logger.info('Attempting change on {}: {}'.format(page_name, change))
        change_made = perform_bot_edit(page_name, '[[Wikipedia:OABOT|Open access bot]]: {} added to citation with #oabot.'.format(', '.join(set(ids_touched))), proposed_additions, access_token=access_token, site=site)
        if change_made:
            return True
    except ValueError:
        app.logger.exception('perform_bot_edit failed on {}'.format(page_name))
    except (LockedPageError, OtherPageSaveError, ReadTimeout):
        app.logger.exception('perform_bot_edit was rejected or timed out on {}'.format(page_name))
    return False

def perform_bot_edit(page_name, summary, proposed_additions, access_token=None, site=None):
     # Get the page
    new_text = main.get_page_over_api(page_name)

    # Perform each edit
    for template_hash in proposed_additions:
        new_text, change_made = make_new_wikicode_for_bot(new_text, template_hash, proposed_additions[template_hash], page_name)

    # Save the page
    if change_made:
        if site:
            page = pywikibot.Page(site, page_name)
            page.text = new_text
            page.save(summary)
        else:
            edit_wiki_page(page_name, new_text, access_token, summary, bot='yes')


        # Remove the cache
        cache_fname = "bot_cache/"+to_cache_name(page_name)
        if os.path.isfile(cache_fname):
            os.remove(cache_fname)

    return change_made

def make_new_wikicode_for_bot(text, template_hash, proposed_addition, page_name):
    wikicode = mwparserfromhell.parse(text)
    change_made = False
    for template in wikicode.filter_templates():
        edit = main.TemplateEdit(template, page_name)
        if edit.orig_hash == template_hash:
            try:
                for proposed_parameter in proposed_addition.split("|"):
                    edit.update_template(proposed_parameter)
                change_made = True
            except ValueError:
                app.logger.exception('update_template failed on {}'.format(page_name))
                pass # TODO report to the user
    return str(wikicode), change_made


if __name__ == '__main__':
    import sys
    template_param = sys.argv[1]
    app.logger.info("Starting additions for parameter: {}".format(template_param))
    site = pywikibot.Site()
    site.login()
    run_bot(template_param, site=site)
