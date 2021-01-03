#!/bin/bash
cd /data/project/oabot/www/python/src
echo "activating virtualenv"
source ../venv/bin/activate
echo "starting python"
python <<EOF
print "importing main"
from main import *
print "launching test_run()"
dry_run_for_wikitable(90, u'Bronze Age')
EOF
