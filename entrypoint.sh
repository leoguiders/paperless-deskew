#!/bin/sh
set -e

# Provide the pre-consume hook in a directory shared with the paperless
# container; refreshed on every start, so image updates apply
if [ -n "$HOOK_DIR" ]; then
  mkdir -p "$HOOK_DIR"
  cp /app/deskew.py /app/deskew_hook.py "$HOOK_DIR/"
  chmod 644 "$HOOK_DIR/deskew.py"
  chmod 755 "$HOOK_DIR/deskew_hook.py"
  echo "Hook installed in $HOOK_DIR"
fi

# Tag service for documents already in paperless (optional)
if [ -n "$PAPERLESS_URL" ] && [ -n "$PAPERLESS_TOKEN" ]; then
  exec python3 -u /app/service.py
fi

echo "PAPERLESS_URL/PAPERLESS_TOKEN not set - tag service disabled, only providing the hook"
exec sleep infinity
