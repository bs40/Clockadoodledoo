#!/bin/bash
# Restart the clock inside the Pi's desktop session. deploy.cmd runs this after copying.
cd "$(dirname "$0")/.."
pkill -f "run.py --fullscreen"
sleep 1
export XDG_RUNTIME_DIR=/run/user/$(id -u)
export WAYLAND_DISPLAY=wayland-0 DISPLAY=:0
setsid nohup .venv/bin/python run.py --fullscreen >/tmp/clock.log 2>&1 </dev/null &
sleep 4
if pgrep -f "run.py --fullscreen" >/dev/null; then
    echo "clock restarted"
else
    echo "clock failed to start:"; tail -n 20 /tmp/clock.log
fi
