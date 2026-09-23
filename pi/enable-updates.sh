mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
#!/bin/bash
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
# One-time: turn ~/clock into a git checkout of the GitHub repository and start the update timer.
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
#     bash ~/clock/pi/enable-updates.sh https://github.com/USER/Clockadoodledoo.git
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
# For a private repository use the SSH form (git@github.com:USER/Clockadoodledoo.git) and first
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
# add this Pi's public key (~/.ssh/id_ed25519.pub, made with ssh-keygen) as a deploy key on GitHub.
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
set -e
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
REPO="$1"
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
[ -n "$REPO" ] || { echo "usage: $0 REPO_URL"; exit 1; }
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
cd "$(dirname "$0")/.."
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
HERE="$(pwd)"
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts

mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
if [ ! -d .git ]; then
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
    git init -q
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
fi
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
git remote remove origin 2>/dev/null || true
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
git remote add origin "$REPO"
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
git fetch -q origin
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
git checkout -q -B main origin/main
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
cp requirements.txt .venv/requirements.installed 2>/dev/null || true
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
echo "checked out $(git log -1 --format='%h %s')"
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts

mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
mkdir -p ~/.config/systemd/user
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
cat > ~/.config/systemd/user/clock-update.service <<UNIT
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
[Unit]
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
Description=Fetch Clockadoodledoo updates
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts

mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
[Service]
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
Type=oneshot
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
ExecStart=/bin/bash $HERE/pi/update.sh
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
UNIT
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
cat > ~/.config/systemd/user/clock-update.timer <<UNIT
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
[Unit]
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
Description=Check for Clockadoodledoo updates every 5 minutes
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts

mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
[Timer]
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
OnBootSec=2min
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
OnUnitActiveSec=5min
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts

mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
[Install]
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
WantedBy=timers.target
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
UNIT
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
systemctl --user daemon-reload
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
systemctl --user enable --now clock-update.timer
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
sudo loginctl enable-linger "$USER"
mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com 2>/dev/null >> ~/.ssh/known_hosts
echo "update timer running:"; systemctl --user list-timers clock-update.timer --no-pager | head -3
