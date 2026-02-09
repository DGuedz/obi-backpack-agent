#!/bin/bash
set -e

# OBI WORK - Secure Agent Launcher
# Usage: ./start_agent_secure.sh [mode]

MODE=${1:-safe}

echo "[OBI-SECURE] Initializing Environment..."

# 1. Export AWS Safety Flags
export AWS_MAX_ATTEMPTS=3
export AWS_RETRY_MODE=adaptive
export AWS_EC2_METADATA_DISABLED=true
export PYTHONUNBUFFERED=1

# 2. Resource Ulimits (Redundant check)
ulimit -n 4096
ulimit -u 512

echo "[OBI-SECURE] Limits Applied. Launching Watchdog in Mode: $MODE"

# 3. Launch Watchdog
# Assumes we are in the backend_core/obi_work_core directory or adjusts path
cd "$(dirname "$0")/../../obi_work_core"

exec python3 agent_guard.py \
    --mode "$MODE" \
    --max-workers 2 \
    --timeout 30 \
    --memory-limit 512 \
    --cpu-limit 1 \
    --log-level INFO
