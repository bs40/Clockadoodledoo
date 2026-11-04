#!/bin/bash
# One-time setup on the Raspberry Pi. Run from the project folder:
#     bash ~/clock/pi/install.sh
# Installs Python dependencies into ~/clock/.venv, starts the clock full screen
# at every boot (pi/autostart.sh; no desktop needed), and turns off screen blanking.
set -e
cd "$(dirname "$0")/.."
HERE="$(pwd)"

sudo apt-get update
sudo apt-get install -y python3-venv ddcutil sense-hat   # sense-hat: optional Sense HAT sensors
sudo usermod -aG i2c "$USER"        # lets ddcutil set the screen brightness later

python3 -m venv --system-site-packages .venv   # so the venv can see the Sense HAT library
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

sudo raspi-config nonint do_blanking 1   # 1 = never blank the screen
bash pi/autostart.sh                     # starts it now, and at every boot

echo
echo "Done: the clock is running and will start at every boot."
