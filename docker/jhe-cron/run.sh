#!/bin/bash
# Wrapper script for cron jobs in Docker
# Sets correct WORKSPACE before calling VM scripts

WORKSPACE="${WORKSPACE:-/app}"
export WORKSPACE

SCRIPT="$1"
shift 2>/dev/null || true

if [ -z "$SCRIPT" ]; then
    echo "Usage: run.sh <script-name> [args...]"
    exit 1
fi

SCRIPT_PATH="/app/scripts/$SCRIPT"

if [ ! -f "$SCRIPT_PATH" ]; then
    echo "ERROR: Script not found: $SCRIPT_PATH"
    exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running $SCRIPT (WORKSPACE=$WORKSPACE)"

bash "$SCRIPT_PATH" "$@"
exit $?
