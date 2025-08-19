#!/usr/bin/env sh
PID_FILE="/var/run/api.pid"
if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  kill -TERM "$(cat "$PID_FILE")" || true
  echo "API stopped"
else
  echo "API already stopped"
fi

