#!/bin/bash
# One-time: turn ~/clock into a git checkout of the GitHub repository and start the update timer.
#     bash ~/clock/pi/enable-updates.sh https://github.com/USER/Clockadoodledoo.git
# For a private repository use the SSH form (git@github.com:USER/Clockadoodledoo.git) and first
# add this Pi's public key (~/.ssh/id_ed25519.pub, made with ssh-keygen) as a deploy key on GitHub.
set -e
REPO="$1"
[ -n "$REPO" ] || { echo "usage: $0 REPO_URL"; exit 1; }
cd "$(dirname "$0")/.."
HERE="$(pwd)"

if [ ! -d .git ]; then
    git init -q
fi
git remote remove origin 2>/dev/null || true
git remote add origin "$REPO"
git fetch -q origin
git checkout -q -B main origin/main
cp requirements.txt .venv/requirements.installed 2>/dev/null || true
echo "checked out $(git log -1 --format='%h %s')"

mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/clock-update.service <<UNIT
[Unit]
Description=Fetch Clockadoodledoo updates

[Service]
Type=oneshot
ExecStart=/bin/bash $HERE/pi/update.sh
UNIT
cat > ~/.config/systemd/user/clock-update.timer <<UNIT
[Unit]
Description=Check for Clockadoodledoo updates every 5 minutes

[Timer]
OnBootSec=2min
OnUnitActiveSec=5min

[Install]
WantedBy=timers.target
UNIT
systemctl --user daemon-reload
systemctl --user enable --now clock-update.timer
sudo loginctl enable-linger "$USER"
echo "update timer running:"; systemctl --user list-timers clock-update.timer --no-pager | head -3
