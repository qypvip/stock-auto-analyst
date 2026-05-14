---
name: stock-auto-analyst
description: "A股智能分析系统 v1.5 — 东方财富API驱动，全市场筛选(≤¥20) + 四维评分(技术35%/基本面35%/估值15%/动量15%) + K线形态识别(10+种) + 量价背离检测 + 资金流向分析 + 模拟交易(凯利公式仓位) + 自我学习调参 + 每周一推送。附加足球预测系统 v6.5双推(早晚)。"
version: 1.5.0
author: Hermes Agent
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [stock, a-shares, analysis, trading, autonomous, ai, football-prediction, chinese-stocks, kelly-formula]
---

# 📊 A股智能分析系统 v1.5 + ⚽ 足球预测 v6.5

全自动A股智能分析系统 + 足球预测双推系统。

## A股核心功能

### 四维评分模型
| 维度 | 权重 | 指标 |
|------|------|------|
| 📈 技术面 | 35% | MA趋势、MACD金叉/死叉、KDJ超买超卖、RSI强弱、布林带位置、量比、CCI |
| 📋 基本面 | 35% | PE(25%)、PB(20%)、ROE(25%)、营收增速(15%)、利润增速(15%) |
| 💰 估值 | 15% | 动态PE分位、PB分位、PS分位、股息率溢价 |
| 🚀 动量 | 15% | 5日涨幅、20日涨幅、成交量变化率、RSI动量 |

### K线形态识别 (10+种)
- 十字星、锤子线、吊颈线、吞没形态、晨星/黄昏星
- 三连阳/三连阴、上升/下降三法
- 量价背离检测 (顶背离/底背离)

### 模拟交易
- 初始资金: ¥100,000
- 最大持仓: 5只
- **凯利公式仓位管理**: `f* = (bp - q) / b`
- 止损: -8% | 止盈: 3档 (+8%减30%, +15%减50%, +25%清仓)
- 买卖区间: 支撑价/阻力价/三档止盈/止损价

### 自我学习
- 根据历史胜率自动调整四维权重
- 胜率 >60% → 增加动量权重
- 胜率 <40% → 增加基本面权重
- 权重持久化到 `weights.json`

## 足球预测 v6.5

### 14因子深度分析
1. Elo评级 (动态调整)
2. 动机因子 (保级/冲欧冠/争冠)
3. 主客场优势
4. 近期趋势 (6场加权)
5. 防守稳定性 (场均失球)
6. H2H历史交锋
7. 伤病影响 (轮换关键度)
8. 休息时间 (疲劳度)
9. 天气影响 (wttr.in免费获取)
10. 裁判风格 (出牌率/点球倾向)
11. 球队球风 (攻势/防反/控场)
12. 赛程密集度 (周中杯赛)
13. 指数隐含概率 (市场热度校正)
14. 媒体热度 (异常舆情感知)

### 早晚双推
- **08:00**: 未来3天Top10预测 + 天气 + 动机 + 可信度评分
- **17:00**: 已赛复盘 + 准确率统计 + 未赛调整

### 覆盖联赛
英超(PL) | 西甲(PD) | 德甲(BL1) | 意甲(SA) | 法甲(FL1) | 欧冠(CL)

### 数据源 (全部免费)
- Football-Data.org API (Free Tier)
- wttr.in (天气)
- 内置Elo/Motivation模型

## 脚本位置

### A股系统
- `stock_auto_analyst.py` — 主分析脚本 (四维评分+模拟交易)
- 学习档案: `~/.learnings/股票/`

### 足球系统
- `football_predict.py` — v6.5主引擎
- 学习档案: `~/.learnings/足球/LEARNINGS.md`

### 推送配置
- QQ邮箱: lpzjqyp@qq.com
- Cron: 足球早08:00 + 晚17:00 | A股每周一08:00

## Cronjob配置

```bash
# 足球早间预测 (08:00)
cronjob create name="足球早间预测" schedule="0 8 * * *" script=football_predict.py no_agent=true

# 足球午后复盘 (17:00)
cronjob create name="足球午后复盘" schedule="0 17 * * *" script=football_review.py no_agent=true

# A股周推荐 (周一08:00)
cronjob create name="A股周推荐" schedule="0 8 * * 1" script=stock_auto_analyst.py no_agent=true
```

## 数据源

- **东方财富** — 全市场选股 + K线数据
- **新浪财经** — 备选数据源
- **腾讯财经** — 实时行情批量查询
- **Football-Data.org** — 足球赛程+比分
- **wttr.in** — 天气数据 (免费, 无需Key)
