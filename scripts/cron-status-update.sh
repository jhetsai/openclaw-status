#!/bin/bash
# 狀態頁自動更新 Cron 脚本
# 每小時執行一次

cd /home/jhe/.openclaw/workspace
bash scripts/bake-status-page.sh >> logs/cron-status.log 2>&1