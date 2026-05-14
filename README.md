# 📊 A股智能分析系统 v1.5 + ⚽ 足球预测 v6.5

> 全自动 A-share stock analysis + football prediction system — 免费数据源、本地运行、多因子评分、模拟交易、自我学习

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

---

## 🇨🇳 中文

### 概述

这是一个免费的多功能智能分析系统，包含 **A股分析** 和 **足球预测** 两大模块。

全部使用免费公开 API，零成本运行，支持本地自动化推送。

---

### 📈 A股智能分析

#### 核心功能

| 功能 | 说明 |
|------|------|
| 🎯 **四维评分** | 技术面(35%) + 基本面(35%) + 估值(15%) + 动量(15%) |
| 🔍 **全市场选股** | 东方财富API 动态获取，过滤单价 ≤¥20 |
| 📊 **K线形态识别** | 十字星、锤子线、吞没形态、晨星/黄昏星等10+种 |
| ⚡ **量价背离检测** | 顶背离/底背离自动识别 |
| 💰 **资金流向分析** | 主力净流入/流出、大单追踪 |
| 🧩 **板块轮动** | 行业板块热度排序、资金聚集度 |
| 💵 **模拟交易** | ¥100,000模拟资金，凯利公式仓位管理，限5只 |
| 🧠 **自我学习** | 根据胜率自动调整四维评分权重 |
| 📧 **报告推送** | 每周一 08:00 QQ邮箱推送 |

#### 评分模型

| 维度 | 权重 | 关键指标 |
|------|------|----------|
| 📈 技术面 | 35% | MA趋势、MACD金叉/死叉、KDJ、RSI、布林带、量比、CCI |
| 📋 基本面 | 35% | PE(25%)、PB(20%)、ROE(25%)、营收增速(15%)、利润增速(15%) |
| 💰 估值 | 15% | 动态PE分位、PB分位、PS分位、股息率溢价 |
| 🚀 动量 | 15% | 5日涨幅、20日涨幅、成交量变化率、RSI动量 |

#### 买卖区间

| 项目 | 规则 |
|------|------|
| 买入区间 | 当前价 × 支撑系数以内 |
| 止损 | -8% |
| 止盈1档 | +8% 减仓30% |
| 止盈2档 | +15% 减仓50% |
| 止盈3档 | +25% 清仓 |
| 仓位管理 | 凯利公式 f* = (bp - q) / b |

---

### ⚽ 足球预测 v6.5

#### 14因子深度分析

| # | 因子 | 说明 |
|---|------|------|
| 1 | Elo评级 | 动态调整，反映真实实力 |
| 2 | 动机因子 | 保级/冲欧冠/争冠驱动 |
| 3 | 主客场 | 主场优势量化 |
| 4 | 近期趋势 | 6场加权表现 |
| 5 | 防守稳定性 | 场均失球率 |
| 6 | H2H历史交锋 | 对战心理优势 |
| 7 | 伤病影响 | 关键球员缺阵 |
| 8 | 休息时间 | 疲劳累积度 |
| 9 | 天气影响 | wttr.in免费获取 |
| 10 | 裁判风格 | 出牌率/点球倾向 |
| 11 | 球队球风 | 攻势/防反/控场 |
| 12 | 赛程密集度 | 周中杯赛消耗 |
| 13 | 指数隐含概率 | 市场热度校正 |
| 14 | 媒体热度 | 异常舆情感知 |

#### 推送时间

| 时间 | 内容 | 数据源 |
|------|------|--------|
| ⚽ **08:00** | 未来3天Top10预测+天气+动机 | Football-Data.org + wttr.in |
| ⚽ **17:00** | 已赛复盘+准确率统计+未赛调整 | Football-Data.org |

覆盖联赛: 英超 🏴󠁧󠁢󠁥󠁮󠁧󠁿 | 西甲 🇪🇸 | 德甲 🇩🇪 | 意甲 🇮🇹 | 法甲 🇫🇷 | 欧冠 🌍

---

### 🚀 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/qypvip/stock-auto-analyst.git
cd stock-auto-analyst

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行 A股分析
python stock_auto_analyst.py

# 4. 运行足球预测
python football_predict.py
```

### 📦 依赖

```
requests>=2.25.0
pandas>=1.2.0
numpy>=1.19.0
```

---

### 📄 文档

| 文档 | 说明 |
|------|------|
| [评分模型](docs/scoring-model.md) | 详细评分算法说明 |
| [自定义配置](docs/customization.md) | 参数调优指南 |
| [数据源](docs/api-sources.md) | API端点清单 |
| [SKILL.md](SKILL.md) | Hermes Agent 系统集成 |

---

### 🤝 贡献

PRs welcome! 详见 [CONTRIBUTING.md](CONTRIBUTING.md)

### 📄 License

MIT License — 可自由 fork、修改、商用

### ⚠️ 免责声明

本系统仅供 **教育研究用途**，不构成投资建议。股市有风险，投资需谨慎。

**足球预测仅供参考，不构成投注建议。**

---

## 🇬🇧 English

### Overview

A free, multi-functional intelligent analysis system combining **A-share stock analysis** and **football match prediction**. All data from free public APIs, zero cost, with automated scheduled delivery.

### Key Features

- **A-Share:** 4-dimension scoring (Technical 35% + Fundamental 35% + Valuation 15% + Momentum 15%)
- **Candlestick Patterns:** 10+ pattern recognition (Doji, Hammer, Engulfing, Morning/Evening Star)
- **Paper Trading:** ¥100,000 simulated capital, Kelly formula position sizing
- **Self-Learning:** Auto-adjusted weights based on prediction win rate
- **Football Prediction:** 14-factor deep analysis, dual daily push (morning/review)
- **Free Data:** No paid APIs required

### Data Sources

- **East Money (东方财富)** — Stock screening & K-line data
- **Football-Data.org** — Match schedules & scores (Free Tier)
- **wttr.in** — Weather data (free, no key)
- **Sina Finance / Tencent Finance** — Fallback stock data
