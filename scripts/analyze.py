#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 A股仓库分析系统 v1.0
从 repo 文件夹读取数据 → 实时分析 → 写回结果

数据流:
  data/portfolio/simulated_portfolio.json ─┐
  data/learnings/LEARNINGS.md ─────────────┤
  (父目录) stock_auto_analyst.py ──────────┼─→ output/analysis/results.json
  (实时) 腾讯/东方财富 API ────────────────┘   output/reports/analysis_*.md

用法:
  python scripts/analyze.py              # 完整分析
  python scripts/analyze.py --quick       # 快速分析(仅API数据)
  python scripts/analyze.py --report      # 只生成报告
"""

import os, sys, json, math
from datetime import datetime

# ─── Repo 路径 ─────────────────────────────────────────
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR   = os.path.join(REPO_ROOT, "data")
OUTPUT_DIR = os.path.join(REPO_ROOT, "output")

PORTFOLIO_FILE = os.path.join(DATA_DIR, "portfolio", "simulated_portfolio.json")
PREDICT_LOG    = os.path.join(DATA_DIR, "portfolio", "prediction_log.json")
LEARNINGS_FILE = os.path.join(DATA_DIR, "learnings", "LEARNINGS.md")
ANALYSIS_OUT   = os.path.join(OUTPUT_DIR, "analysis", "results.json")
REPORT_OUT     = os.path.join(OUTPUT_DIR, "reports")

os.makedirs(os.path.dirname(ANALYSIS_OUT), exist_ok=True)
os.makedirs(REPORT_OUT, exist_ok=True)

# ─── 加载主引擎 ──────────────────────────────────────
sys.path.insert(0, REPO_ROOT)
from stock_auto_analyst import (
    fetch_market_indices, fetch_candidates_sina,
    fetch_stocks_batch, fetch_kline, screen_and_score,
    compute_technical_score, score_single_stock,
    LearningModule, SimulatedPortfolio,
    generate_weekly_report, LD, PF
)


# ─── 数据层: 读 repo 数据 ──────────────────────────────
def load_portfolio():
    """从 data/portfolio/ 读取组合数据"""
    if not os.path.exists(PORTFOLIO_FILE):
        print("  ⚠️  data/portfolio/simulated_portfolio.json 不存在, 使用空组合")
        return {"ic": 100000, "cash": 100000, "pos": {}, "trades": [], "tp": 0}
    with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_learnings():
    """从 data/learnings/ 读取学习记录"""
    if not os.path.exists(LEARNINGS_FILE):
        return "暂无学习记录"
    with open(LEARNINGS_FILE, "r", encoding="utf-8") as f:
        return f.read()[:800]  # 截取前 800 字

def load_prediction_log():
    """从 data/portfolio/ 读取预测日志"""
    if not os.path.exists(PREDICT_LOG):
        return []
    with open(PREDICT_LOG, "r", encoding="utf-8") as f:
        return json.load(f)


# ─── 分析层 ──────────────────────────────────────────
def run_analysis(quick=False):
    """主分析流程"""
    print(f"{'='*50}")
    print(f"  📊 仓库分析系统 — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}\n")

    # Step 1: 大盘数据
    print("📈 一、获取大盘数据...")
    indices = fetch_market_indices()
    if indices:
        for name, d in indices.items():
            arrow = "🟢" if d.get("change_pct", 0) >= 0 else "🔴"
            print(f"  {arrow} {name}: {d['price']:.2f} ({d.get('change_pct',0):+.2f}%)")
    else:
        print("  ⚠️ 大盘数据获取失败")

    # Step 2: 读取持仓
    print("\n💼 二、读取模拟持仓...")
    portfolio = load_portfolio()
    print(f"  现金: ¥{portfolio['cash']:,.0f}")
    
    if portfolio.get("pos"):
        for code, pos in portfolio["pos"].items():
            if pos["shares"] > 0:
                print(f"  📦 {pos['name']}({code}): {pos['shares']}股 @ ¥{pos['avg_cost']:.2f}")
    else:
        print("  暂无持仓")

    if quick:
        print("\n⚡ 快速模式: 跳过全市场扫描和评分")
        results = {"quick": True, "indices": indices}
        return results

    # Step 3: 全市场扫描
    print("\n🔍 三、全市场扫描评分...")
    top = screen_and_score(max_price=20.0, limit=10)
    if top:
        print(f"\n  ⭐ TOP 10 精选:")
        for i, s in enumerate(top, 1):
            print(f"  {i}. {s['name']}({s['code']}) 评分:{s['cs']}/100  ¥{s['price']:.2f}  {s.get('sig',[])}")
    else:
        print("  ⚠️ 扫描无结果")

    # Step 4: 自我学习分析
    print("\n🧠 四、自我学习分析...")
    lm = LearningModule()
    learn_summary = lm.insights()
    print(f"  当前权重: 技术{lm.weights.get('tech_w',0.55)*100:.0f}% 基本面{lm.weights.get('fund_w',0.30)*100:.0f}% 价格{lm.weights.get('price_w',0.15)*100:.0f}%")

    # Step 5: 整合结果
    print("\n📝 五、保存分析结果...")
    analysis_result = {
        "time": datetime.now().isoformat(),
        "indices": indices if indices else {},
        "portfolio_summary": {
            "cash": portfolio["cash"],
            "cash_formatted": f"¥{portfolio['cash']:,.0f}",
            "positions": len([c for c in portfolio.get("pos",{}) if portfolio["pos"][c]["shares"] > 0]),
            "total_pnl": portfolio.get("tp", 0)
        },
        "top_picks": [{
            "name": s["name"], "code": s["code"],
            "score": s["cs"], "price": s["price"],
            "change_pct": s.get("chg", 0),
            "signals": s.get("sig", []),
            "target": s.get("target", 0),
            "stop_loss": s.get("sl", 0)
        } for s in (top or [])],
        "weights": lm.weights,
        "learn_summary": learn_summary
    }

    with open(ANALYSIS_OUT, "w", encoding="utf-8") as f:
        json.dump(analysis_result, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 分析结果已保存: {ANALYSIS_OUT}")

    # Step 6: 生成报告
    print("📄 六、生成分析报告...")
    market_info = {
        "trend": "震荡上行" if indices else "未知",
        "risk": "较低",
        "score": 60,
        "indices": indices if indices else {}
    }
    # 构建 portfolio 包含 generate_weekly_report 需要的所有字段
    port_total = portfolio["cash"]
    for c, p in portfolio.get("pos", {}).items():
        if p.get("shares", 0) > 0:
            mv = p["shares"] * p.get("avg_cost", 0)
            p["market_val"] = mv
            port_total += mv
    report_positions = {}
    for c, p in portfolio.get("pos", {}).items():
        if p.get("shares", 0) > 0:
            report_positions[c] = {
                "name": p.get("name", "未知"),
                "shares": p["shares"],
                "avg_cost": p.get("avg_cost", 0),
                "pnl": p.get("pnl", 0),
                "pnl_pct": p.get("pnl_pct", 0),
                "market_val": p.get("market_val", p["shares"] * p.get("avg_cost", 0))
            }
    report_portfolio = {
        "cash": portfolio["cash"],
        "total": port_total,
        "cnt": len(report_positions),
        "ic": portfolio.get("ic", 100000),
        "tp": portfolio.get("tp", 0),
        "tp_pct": portfolio.get("tp", 0) / max(portfolio.get("ic", 100000), 1) * 100,
        "pos": report_positions,
        "trades": portfolio.get("trades", [])
    }

    report = generate_weekly_report(
        top or [], market_info, report_portfolio, learn_summary, []
    )

    report_file = os.path.join(REPORT_OUT, f"分析报告_{datetime.now().strftime('%Y%m%d_%H%M')}.md")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  ✅ 报告已生成: {report_file}")

    print(f"\n{'='*50}")
    print(f"  ✅ 分析完成！")
    print(f"{'='*50}")
    return analysis_result


# ─── 入口 ──────────────────────────────────────────
if __name__ == "__main__":
    quick_mode = "--quick" in sys.argv
    report_only = "--report" in sys.argv
    
    if report_only:
        # 只从已有结果生成报告
        if os.path.exists(ANALYSIS_OUT):
            with open(ANALYSIS_OUT, "r") as f:
                result = json.load(f)
            print(f"📄 从已有结果生成报告: {ANALYSIS_OUT}")
        else:
            print("⚠️ 无已有结果, 先运行分析")
            result = run_analysis(quick=True)
    else:
        result = run_analysis(quick=quick_mode)
    
    # 输出报告文件路径
    report_files = sorted(os.listdir(REPORT_OUT), reverse=True)
    if report_files:
        latest = report_files[0]
        print(f"\n📁 最新报告: output/reports/{latest}")
