#!/bin/bash
# Restart the clock (the clock systemd user service set up by autostart.sh). deploy.cmd runs this
# after copying.
systemctl --user restart clock.service
sleep 4
if systemctl --user is-active --quiet clock.service; then
    echo "clock restarted"
else
    echo "clock failed to start:"; systemctl --user --no-pager status clock.service | tail -n 20
fi
