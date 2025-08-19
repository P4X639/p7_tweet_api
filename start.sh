#!/usr/bin/env sh
set -eu

APP_DIR="/app"
LOG_DIR="/var/log"
RUN_DIR="/var/run"
PID_FILE="$RUN_DIR/api.pid"
LOG_FILE="$LOG_DIR/api.log"

mkdir -p "$LOG_DIR" "$RUN_DIR"
cd "$APP_DIR"

# Démarre l’API (backgound + PID stockée + gestion des logs)
nohup python -u main.py >> "$LOG_FILE" 2>&1 &
API_PID=$!
echo $API_PID > "$PID_FILE"
echo "[start] API démarrée (pid=$API_PID). Logs: $LOG_FILE"

# Arrêt propre si le conteneur reçoit SIGTERM/SIGINT
term() {
  echo "[start] Signal reçu, arrêt de l’API..."
  if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    kill -TERM "$(cat "$PID_FILE")" || true
    wait "$(cat "$PID_FILE")" 2>/dev/null || true
  fi
  exit 0
}
trap term TERM INT

# Garde le conteneur vivant + stream les logs de l'API
touch "$LOG_FILE"
exec tail -F "$LOG_FILE"
