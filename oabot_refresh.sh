# Simplistic script to refresh suggestions, launch the bot and clean up the queue a bit.
# Try not to override the suggestions which were already rejected, to
# avoid presenting the same suggestions all the time to users of the tool.
cd ~/www/python/src/
~/www/python/venv/bin/python ~/www/python/src/prefill.py
cd ~/www/python/src/cache/
grep -ErlZ --exclude-dir="*" '"proposed_change": "(hdl|pmc|arxiv|doi)' | xargs -0 -I§ mv "§" ~/www/python/src/bot_cache/
grep -ErlZ --exclude-dir="*" '"proposed_link": "http://(citeseerx|pdfs.semanticscholar.org)' | xargs -0 -I§ mv "§" ~/www/python/src/cache/ss/
cd ~/www/python/
for title in $( find ~/www/python/src/cache -maxdepth 1 -type f -mtime -14 -name "*json" -printf "%f\n" | sed 's,#,/,g' | sed 's,.json,,g' | sort | shuf ); do bash oabot_prefill_single.sh "$title" ; done
cd ~/www/python/src/
~/www/python/venv/bin/python bot.py "(arxiv|pmc|pmid|doi|hdl)"
# Failure is not an option
exit 0
