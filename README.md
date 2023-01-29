Wikipedia OAbot [![Build Status](https://travis-ci.org/dissemin/oabot.svg?branch=master)](https://travis-ci.org/dissemin/oabot)
===============

This tool looks for [open access](https://en.wikipedia.org/wiki/Open_access) versions
of [references in Wikipedia articles](https://en.wikipedia.org/wiki/Wikipedia:Citing_sources). (For now only the English Wikipedia.)

It relies on the [Dissemin](http://dissem.in) [API](http://dev.dissem.in/api.html) and [Unpaywall](https://unpaywall.org).

[Start editing citations](https://tools.wmflabs.org/oabot/)
-----------------------------------------------------

[Report any issues on Phabricator](https://phabricator.wikimedia.org/tag/oabot/)
------------------------------------------------------------

OAbot requires Python 3 for bot.py due to the pywikibot dependency (which can be ignored if you don't run bot.py). The latest version tested with Python 2 is tagged as `python2`.

Local installation and usage instructions:
* Clone the repository on your computer and enter the project directory.
* Install dependencies with `pip install -r requirements.txt`.
* Create a database config with `cp dbconfig.py.in dbconfig.py` (this database is used to store edit counts)
* Serve the application with a [WSGI](http://enwp.org/WSGI)-enabled server, using `app.py`, or run the application locally with `python app.py`, which serves the tool on `http://localhost:5000/`.
* To run the tool in production, set up the `config.yaml` with the tool's secrets.
* To run the bot, follow the [pywikibot instructions](https://wikitech.wikimedia.org/wiki/Help:Toolforge/Pywikibot) and make sure the `user-config.py` file with credentials is in [one of the relevant directories](https://www.mediawiki.org/wiki/Manual:Pywikibot/user-config.py), for example the working directory of bot.py.
