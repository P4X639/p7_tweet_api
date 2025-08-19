#!/usr/bin/env sh
PID_FILE="/var/run/api.pid"
if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "API RUNNING (pid=$(cat "$PID_FILE"))"
  exit 0
else
  echo "API NOT RUNNING"
  exit 1
fi

