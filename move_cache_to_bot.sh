#!/bin/sh

cd ~/www/python/src/cache/
template_param=$1
for fname in `ack --no-recurse -l "\"proposed_change\": \"$template_param"`; do
    mv $fname ~/www/python/src/bot_cache/
done

