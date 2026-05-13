# 📈 A股自主智能分析系统 (Stock Auto Analyst)

> 全自动 A-share stock analysis system — 免费数据源、本地运行、技术+基本面多维评分、模拟交易、自我学习

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

---

## 🇨🇳 中文

### 概述

这是一个完全免费的 A 股智能分析系统，使用**新浪财经 + 腾讯财经**公开 API（无需任何 API Key），在本地运行。

### 核心功能

| 功能 | 说明 |
|------|------|
| 📊 **大盘模拟** | 实时跟踪上证/深证/创业板指数，评估市场风险 |
| 🔍 **动态选股** | 筛选全市场 SH+SZ 股票，自动过滤单价 <20元(可配) |
| 📈 **技术分析** | MA/MACD/KDJ/RSI/布林带/量比 七维评分 |
| 📋 **基本面分析** | PE/PB/ROE/营收增速/利润增速 五维评分 |
| 💰 **模拟交易** | ¥100,000 模拟资金，自动止损止盈，限5只持仓 |
| 🧠 **自我学习** | 跟踪推荐胜率，自动调整评分权重 |
| 📧 **报告推送** | 每周一 08:00 QQ邮箱推送 + TOP5观察池 |
| 🔔 **价格警报** | 持仓达到止损/止盈线自动通知 |

### 快速开始

```bash
# 1. 安装依赖
pip install requests pandas numpy

# 2. 配置邮箱 (可选，不配置则只有命令行输出)
cp config/.email_config.example config/.email_config
# 编辑 .email_config 填入你的 QQ邮箱和授权码

# 3. 初始化
python stock_auto_analyst.py init

# 4. 运行分析
python stock_auto_analyst.py weekly    # 完整周分析
python stock_auto_analyst.py daily     # 每日更新
python stock_auto_analyst.py alert     # 价格警报检查
python stock_auto_analyst.py learn     # 自我学习评估
```

### 数据源

- **新浪财经** (免费，无需 Key) — 全A股候选列表、实时行情
- **腾讯财经** (免费，无需 Key) — 批量实时行情、K线数据
- 零成本，零 API 费用，无需注册

### 自定义配置

所有参数在脚本头部可调：

```python
POOL_SIZE = 80          # 候选池大小
MAX_POSITIONS = 5       # 最大持仓数
MAX_PRICE = 20.0        # 最高选股单价
TECH_WEIGHT = 0.55      # 技术面权重
FUND_WEIGHT = 0.30      # 基本面权重
PRICE_WEIGHT = 0.15     # 价格权重
```

---

## 🇬🇧 English

### Overview

A free, fully autonomous A-share (Chinese stock market) analysis system. Uses **Sina Finance + Tencent Finance** public APIs (no API key needed). Runs locally on any platform.

### Features

- 📊 **Market Simulation**: Real-time SH/SZ/ChiNext index tracking
- 🔍 **Dynamic Screening**: Full market scan, auto-filter stocks under ¥20
- 📈 **Technical Analysis**: MA, MACD, KDJ, RSI, Bollinger Bands, Volume
- 📋 **Fundamental Analysis**: PE, PB, ROE, Revenue Growth, Profit Growth
- 💰 **Paper Trading**: ¥100,000 simulated capital, auto stop-loss/take-profit
- 🧠 **Self-Learning**: Track win rate, auto-adjust scoring weights
- 📧 **Email Reports**: Weekly push every Monday 08:00 CST
- 🔔 **Price Alerts**: Auto-notify on stop-loss/take-profit triggers

### Quick Start

```bash
pip install requests pandas numpy
python stock_auto_analyst.py init
python stock_auto_analyst.py weekly  # Full weekly analysis
```

### Data Sources

- **Sina Finance** — stock list, real-time quotes (free, no key)
- **Tencent Finance** — batch quotes, K-line data (free, no key)

---

## 📊 Scoring Model

| Dimension | Weight | Indicators |
|-----------|--------|------------|
| Technical | 55% | MA trend +15, MACD +12/-12, KDJ +8/-8, RSI +5/-5, Volume +5/-5 |
| Fundamental | 30% | PE(25%), PB(20%), ROE(25%), Revenue Growth(15%), Profit Growth(15%) |
| Price | 15% | `(20-price)/20*100`, cheaper = higher score |

See [docs/scoring-model.md](docs/scoring-model.md) for full details.

---

## 🤝 Contributing

PRs welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 License

MIT License — free for personal and commercial use.

## ⚠️ Disclaimer

This is for **educational and research purposes only**. Not financial advice. Stock market investment carries risks.
