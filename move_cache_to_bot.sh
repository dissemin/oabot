#!/bin/sh

template_param=$1
for fname in `grep -Rl $template_param cache`; do
    mv $fname bot_cache/
done

