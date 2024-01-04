# Simplistic script to refresh suggestions, launch the bot and clean up the
# queue a bit. Force a timeout after 48 hours as the multithreaded bot
# sometimes is slow or loops forever.

cd ~/www/python/src/
timeout 48h ~/www/python/venv/bin/python ~/www/python/src/prefill.py
find cache bot_cache -maxdepth 1 -type f -mtime +14 -name "*json" -delete
cd ~/www/python/src/cache/
mkdir ~/www/python/src/cache/ss/
grep -ErlZ --exclude-dir="*" '"proposed_change": "(hdl|pmc|arxiv|doi|url-access)' | xargs -0 -I§ mv "./§" ~/www/python/src/bot_cache/
grep -ErlZ --exclude-dir="*" '"proposed_link": "http://(citeseerx|pdfs.semanticscholar.org)' | xargs -0 -I§ mv "./§" ~/www/python/src/cache/ss/
cd ~/www/python/src/
~/www/python/venv/bin/python bot.py "(arxiv|pmc|pmid|doi|hdl)"
timeout 72h ~/www/python/venv/bin/python ~/www/python/src/prefill_cached.py
# Failure is not an option
exit 0
