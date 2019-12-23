#!/bin/sh
set -e
DESTBIN=/usr/local/bin
DESTSRV=/lib/systemd/system
SERVER=zero-hid-gateway.py
SERVICE=zero-hid-gateway.service
cp "$SERVER" "$DESTBIN/$SERVER"
chmod 755 "$DESTBIN/$SERVER"
cp "$SERVICE" "$DESTSRV/$SERVICE"
systemctl daemon-reload
systemctl enable "$SERVICE"
systemctl stop "$SERVICE" || true
systemctl start "$SERVICE"
