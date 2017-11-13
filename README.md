Wikipedia OAbot
===============

This tool looks for [open access](https://en.wikipedia.org/wiki/Open_access) versions
of [references in Wikipedia articles](https://en.wikipedia.org/wiki/Wikipedia:Citing_sources).

It relies on the [Dissemin](http://dissem.in) [API](http://dev.dissem.in/api.html) and [oaDOI](https://oadoi.org).

[Start editing citations](https://tools.wmflabs.org/oabot/)
-----------------------------------------------------

[Report any issues on Phabricator](https://phabricator.wikimedia.org/tag/oabot/)
------------------------------------------------------------

Local installation and usage instructions:
* Clone the repository on your computer and enter the project directory
* Install dependencies with `pip install -r requirements.txt`
* Create a database config with `cp dbconfig.py.in dbconfig.py` (this database is used to store edit counts)
* Serve the application with a [WSGI](http://enwp.org/WSGI)-enabled server, using `app.py`, or run the application locally with `python app.py`, which serves the tool on `http://localhost:5000/`.
