#!/bin/bash
# Repackage Tizen WGT to fix signature/certificate mismatch (Error 118012)
set -e

APP_DIR="$1"
PROFILE="${2:-samsung_tv}"
TARGET_TV="${3:-100.113.48.14:26101}"

if [ -z "$APP_DIR" ]; then
    echo "Usage: $0 <app_directory> [profile_name] [tv_ip:port]"
    exit 1
fi

echo "==> Cleaning stale signatures..."
rm -f "$APP_DIR"/*signature*.xml "$APP_DIR"/.manifest.tmp "$APP_DIR"/*.wgt

echo "==> Packaging with profile: $PROFILE..."
tizen package -t wgt -s "$PROFILE" -- "$APP_DIR"

WGT_FILE=$(ls -t "$APP_DIR"/*.wgt | head -n 1)
echo "==> Package generated: $WGT_FILE"

if [ -n "$TARGET_TV" ]; then
    echo "==> Installing to $TARGET_TV..."
    tizen install -n "$WGT_FILE" -s "$TARGET_TV"
fi
