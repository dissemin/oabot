# -*- encocding: utf-8 -*-

import os

# App mount point, if the environment variable 'OABOT_DEV' is defined then
# mount the application on '/', otherwise mount it under '/oabot'
OABOT_APP_MOUNT_POINT = '/oabot'
if os.environ.get('OABOT_DEV', None) is not None:
    # Mount point is '/'
    OABOT_APP_MOUNT_POINT = ''

OABOT_USER_AGENT = 'OAbot/1.0 (+http://enwp.org/WP:OABOT)'

# the bot will not make any changes to these templates
excluded_templates = ['cite arxiv', 'cite web', 'cite news', 'cite book']

