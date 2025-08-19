#!/usr/bin/env sh
set -eu
PID_FILE="/var/run/api.pid"
LOG_FILE="/var/log/api.log"
APP_DIR="/app"

if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "[restart] Stop API pid=$(cat "$PID_FILE")"
  kill -TERM "$(cat "$PID_FILE")" || true
  # Option: attends jusqu’à 10s max
  for i in $(seq 1 10); do
    kill -0 "$(cat "$PID_FILE")" 2>/dev/null || break
    sleep 1
  done
fi

cd "$APP_DIR"
echo "[restart] Start API"
nohup python -u main.py >> "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"
echo "[restart] API redémarrée (pid=$(cat "$PID_FILE"))"

