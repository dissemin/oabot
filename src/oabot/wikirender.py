
import requests
import json

from jinja2 import evalcontextfilter, Markup

@evalcontextfilter
def wikirender(eval_ctx, wikicode):
    """
    Converts wikicode to the resulting HTML
    """
    r = requests.get('https://en.wikipedia.org/w/api.php',
        {'action':'parse',
         'text':wikicode,
         'format':'json',
        })
    result = r.json().get('parse',{}).get('text', {}).get('*','')

    result = result.replace('href="/wiki/',
            'href="https://en.wikipedia.org/wiki/')
    result = result.replace('<a ','<a target="_blank" ')

    if eval_ctx.autoescape:
        result = Markup(result) or wikicode
    return result or wikicode


