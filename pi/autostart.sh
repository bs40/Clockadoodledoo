#!/bin/bash
# Start the clock full screen at every boot. Run once (install.sh runs it too):
#     bash ~/clock/pi/autostart.sh
# The clock runs as a systemd user service and draws straight to the screen, so no desktop is
# needed; it is restarted if it crashes, but not if it is quit with Esc or Q.
#     systemctl --user stop clock      stop it until the next boot
#     systemctl --user disable clock   stop it starting at boot
set -e
cd "$(dirname "$0")/.."
HERE="$(pwd)"

mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/clock.service <<UNIT
[Unit]
Description=Clockadoodledoo clock
StartLimitIntervalSec=0

[Service]
WorkingDirectory=$HERE
Environment=SDL_VIDEODRIVER=kmsdrm
ExecStart=$HERE/.venv/bin/python $HERE/run.py --fullscreen
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
UNIT

rm -f ~/.config/autostart/clock.desktop   # the desktop-session autostart this replaces
systemctl --user daemon-reload
systemctl --user enable clock.service
sudo loginctl enable-linger "$USER"       # start user services at boot, without anyone logging in
systemctl --user restart clock.service
sleep 4
systemctl --user --no-pager status clock.service | head -n 3
