#!/usr/bin/env bash
# 一键推送到 GitHub
cd "$(dirname "$0")"
git remote add origin https://github.com/qypvip/stock-auto-analyst.git 2>/dev/null
git branch -M main
git push -u origin main --force
echo "推送完成!"
