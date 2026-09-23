#!/bin/bash
# Fetch the latest code from GitHub and, if anything changed, install it and ask the clock to
# restart at the next quiet moment. Run by the clock-update systemd timer every 5 minutes.
set -e
cd "$(dirname "$0")/.."
git fetch -q origin
local_rev=$(git rev-parse HEAD)
remote_rev=$(git rev-parse origin/main)
[ "$local_rev" = "$remote_rev" ] && exit 0

echo "update: $local_rev -> $remote_rev"
git reset -q --hard origin/main          # config.json is untracked, so it is left alone
if ! cmp -s requirements.txt .venv/requirements.installed 2>/dev/null; then
    .venv/bin/pip install -q -r requirements.txt && cp requirements.txt .venv/requirements.installed
fi
git log -1 --format='%h %s' > .update-pending   # the clock restarts itself when it sees this
