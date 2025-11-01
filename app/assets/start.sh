#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

# Function to log messages
log_info() {
  echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# --- Start Services in Background ---
log_info "Starting supervisor (FastAPI, Stunnel) in background..."
export STUNNEL_ENABLED=1

/usr/bin/supervisord -c /assets/supervisord.conf &
SUPERVISOR_PID=$! # Сохраняем PID фонового процесса

# --- Wait for Supervisor ---
wait $SUPERVISOR_PID
