cd ~/www/python/src
echo $1
~/www/python/venv/bin/python -c 'from app import get_proposed_edits, app; get_proposed_edits("'$1'", True, True, False)'
