#!/bin/bash
#set -x 
#set -e # Exit immediately if a command exits with a non-zero status.

# Function to log messages
log_info() {
  echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

TOP=$(pwd)

# --- Install Root Certificates ---
cd /assets/scripts

log_info "Install Root Certificates"

# --- Сертификаты рабочего контура ---
cat /certs/prod/guc2022.crt | ./root.sh || log_info "Warning: Could not install $(basename "$cert"). Continuing..."
cat /certs/prod/tlscaroot.p7b | ./root.sh || log_info "Warning: Could not install $(basename "$cert"). Continuing..."
cat /certs/prod/tlsca.p7b | ./rootca.sh || log_info "Warning: Could not install $(basename "$cert"). Continuing..."

# --- Сертификаты тестового контура ---
cat /certs/test/root2023-4.crt | ./root.sh || log_info "Warning: Could not install $(basename "$cert"). Continuing..."
cat /certs/test/rootca.cer | ./root.sh || log_info "Warning: Could not install $(basename "$cert"). Continuing..."
cat /certs/test/subca.cer | ./rootca.sh || log_info "Warning: Could not install $(basename "$cert"). Continuing..."

log_info "Root certificate installation finished."

# --- Install Personal Certificate ---
MY_CERT_BUNDLE="/certs/bundle.zip"
log_info "Install Personal Certificate"
cat "$MY_CERT_BUNDLE" | ./my.sh
log_info "Personal certificate installation finished."

cd "$TOP"
