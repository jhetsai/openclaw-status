#!/bin/bash
# upload_status_r2.sh — generate + upload status_esp32.json to R2
WORKSPACE="/home/jhe/.openclaw/workspace"
cd "$WORKSPACE"
python3 scripts/gen_status_json.py
python3 scripts/upload_status_r2.py
