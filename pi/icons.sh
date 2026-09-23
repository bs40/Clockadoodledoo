#!/bin/bash
# Put a Clockadoodledoo launcher on the desktop and in the applications menu. Run by install.sh.
cd "$(dirname "$0")/.."
HERE="$(pwd)"
mkdir -p ~/.local/share/applications ~/.local/share/icons ~/Desktop
cp assets/icon.png ~/.local/share/icons/clockadoodledoo.png
cat > ~/.local/share/applications/clockadoodledoo.desktop <<DESKTOP
[Desktop Entry]
Type=Application
Name=Clockadoodledoo
Comment=Animated chiming clock
Exec=/bin/bash $HERE/pi/restart.sh
Icon=clockadoodledoo
Terminal=false
Categories=Utility;Clock;
DESKTOP
cp ~/.local/share/applications/clockadoodledoo.desktop ~/Desktop/
chmod +x ~/Desktop/clockadoodledoo.desktop
# PIXEL/labwc mark desktop launchers trusted via this metadata flag
gio set ~/Desktop/clockadoodledoo.desktop metadata::trusted true 2>/dev/null || true
update-desktop-database ~/.local/share/applications 2>/dev/null || true
echo "launcher installed"
