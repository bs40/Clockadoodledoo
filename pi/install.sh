#!/bin/bash
# One-time setup on the Raspberry Pi. Run from the project folder:
#     bash ~/clock/pi/install.sh
# Installs Python dependencies into ~/clock/.venv, starts the clock full screen
# at every boot, and turns off screen blanking.
set -e
cd "$(dirname "$0")/.."
HERE="$(pwd)"

sudo apt-get update
sudo apt-get install -y python3-venv ddcutil sense-hat   # sense-hat: optional Sense HAT sensors
sudo usermod -aG i2c "$USER"        # lets ddcutil set the screen brightness later

python3 -m venv --system-site-packages .venv   # so the venv can see the Sense HAT library
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

mkdir -p ~/.config/autostart
cat > ~/.config/autostart/clock.desktop <<DESKTOP
[Desktop Entry]
Type=Application
Name=Clockadoodledoo
Exec=$HERE/.venv/bin/python $HERE/run.py --fullscreen
Path=$HERE
X-GNOME-Autostart-enabled=true
DESKTOP

sudo raspi-config nonint do_blanking 1   # 1 = never blank the screen
bash pi/icons.sh

echo
echo "Done. Reboot to start the clock:  sudo reboot"
echo "To try it now without rebooting:  $HERE/.venv/bin/python run.py --fullscreen"
