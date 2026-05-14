#!/usr/bin/env bash
# ─── 数据同步工具 ─────────────────────────────
# 将 .learnings/股票/ 的最新数据同步到 repo 的 data/ 目录
# 用法: bash scripts/sync_data.sh
# =============================================

REPO="$(cd "$(dirname "$0")/.." && pwd)"
LEARNINGS="$HOME/.learnings/股票"

echo "🔄 同步数据到仓库..."
echo "  源: $LEARNINGS"
echo "  目标: $REPO/data"

# 1. 组合数据
if [ -f "$LEARNINGS/simulated_portfolio.json" ]; then
    cp "$LEARNINGS/simulated_portfolio.json" "$REPO/data/portfolio/"
    echo "  ✅ portfolio/simulated_portfolio.json"
fi
if [ -f "$LEARNINGS/prediction_log.json" ]; then
    cp "$LEARNINGS/prediction_log.json" "$REPO/data/portfolio/"
    echo "  ✅ portfolio/prediction_log.json"
fi

# 2. 学习记录
if [ -f "$LEARNINGS/LEARNINGS.md" ]; then
    cp "$LEARNINGS/LEARNINGS.md" "$REPO/data/learnings/"
    echo "  ✅ learnings/LEARNINGS.md"
fi

# 3. 历史报告
if [ -d "$LEARNINGS/reports" ]; then
    cp "$LEARNINGS/reports/"*.md "$REPO/output/reports/" 2>/dev/null
    echo "  ✅ reports/ (历史报告)"
fi

echo ""
echo "📊 数据同步完成！"
echo "运行分析: python scripts/analyze.py"
