#!/bin/bash
cd /data/project/oabot/www/python/src
echo "activating virtualenv"
source ../venv/bin/activate
echo "starting python"
python <<EOF
print "importing main"
from main import *
print "launching test_run()"
test_run(27, u'Antidepressant')
EOF
