---
name: stock-autonomous-analyst
description: "A股自主智能分析系统 v2.0 — 大盘模拟、技术面(MA/MACD/KDJ/RSI/布林带)+基本面(PE/PB/ROE/营收增速)+政策面、模拟买卖(限5只)、自我学习调参、每周一推优质股(单价<20元)、买卖区间+止损止盈警报。数据源:新浪财经+腾讯财经(免费)"
version: 2.0.0
author: Hermes Agent
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [stock, a-shares, analysis, trading, autonomous, ai, deep-learning, chinese-stocks]
---

# A股自主智能分析系统 v2.0

全自动A股智能分析系统。运行流程：大盘模拟 → 动态选股(新浪财经SH+SZ) → 技术面+基本面多维评分 → 模拟交易(限5只) → 自我学习调参 → 报告生成 → QQ邮箱推送。

## v2.0 改进

| 问题 | v1.0 | v2.0 |
|------|------|------|
| 候选股 | 硬编码60只 | 新浪API动态获取SH+SZ全市场 |
| 基本面 | 仅PE+PB | PE(25%)+PB(20%)+ROE(25%)+营收增速(15%)+利润增速(15%) |
| 自动买入 | 买10只激进 | 限5只，买TOP2，评分≥60 |
| 自我学习 | 只统计不调参 | 根据胜率自动调整技术/基本面权重 |
| 邮件报告 | 纯文本 | HTML格式增强 |
| K线稳定性 | 无重试 | 3次重试+2秒延迟 |

## 核心功能

1. **自主分析**: 技术面(MA/MACD/KDJ/RSI/布林带/量比) + 基本面(PE/PB/ROE/营收增速/利润增速) + 政策资讯
2. **大盘模拟**: 实时上证/深证/创业板指数分析
3. **模拟买卖**: 初始¥100,000，限5只并行持仓，自动止损(-8%)/止盈(+15%减半)
4. **自我学习**: 跟踪推荐胜率，自动调整技术/基本面评分权重
5. **每周推荐**: 每周一8:00推送1只优质股 + TOP5观察池
6. **警报系统**: 止损自动卖出、止盈自动减仓、价格警报邮件

## 脚本位置

- 主脚本: `~/.hermes/scripts/stock_auto_analyst.py`
- 学习档案: `~/.learnings/股票/LEARNINGS.md`
- 报告存档: `~/.learnings/股票/reports/`
- 模拟持仓: `~/.learnings/股票/simulated_portfolio.json`
- 推荐记录: `~/.learnings/股票/prediction_log.json`
- 评分权重: `~/.learnings/股票/weights.json`

## 评分模型

### 技术面(55%权重)
- 均线MA5>MA10>MA20多头 +15分
- MACD金叉 +12分 | 死叉 -12分
- KDJ超卖 +8分 | 多头 +5分 | 超买 -8分
- RSI>50 +5分 | RSI<30 +3分 | RSI>70 -5分
- 量比>1.5且多头 +5分 | 量比<0.5 -5分

### 基本面(30%权重)
- PE(25%): ≤12低估值85分 | 12-25合理70分 | >60极端15分
- PB(20%): ≤1破净80分 | 1-3合理65分 | >10泡沫15分
- ROE(25%): >20优秀90分 | >15良好80分 | >10一般65分 | 负值40分
- 营收增速(15%): >30%强85分 | >15%良好70分 | 负增长10分
- 利润增速(15%): 同上

### 价格(15%权重)
`(20 - price) / 20 * 100`，价格越低分越高

### 置信度
- ≥70分: ⭐⭐⭐
- 58-69分: ⭐⭐
- <58分: ⭐

## 数据源

- **新浪财经(免费, 无需Key)**: 全A股候选列表、实时行情
  - SH: `vip.stock.finance.sina.com.cn/.../sh_a`
  - SZ: `vip.stock.finance.sina.com.cn/.../sz_a`
- **腾讯财经(免费, 无需Key)**: 批量实时行情+K线
  - 实时: `qt.gtimg.cn/q={codes}`
  - K线: `web.ifzq.gtimg.cn/appstock/app/fqkline/...`
  - 大盘: `qt.gtimg.cn/q=sh000001,sz399001,sz399006`
- ~~东方财富~~ (已更换为新浪，东方财富API被IP封锁)

## Cronjob设置

```bash
cronjob action=create name="A股周推荐-周一8点" \
  schedule="0 8 * * 1" \
  script=stock_auto_analyst.py \
  no_agent=true
```

## 选股逻辑

1. 新浪财经SH_A + SZ_A双端点获取候选股(按涨跌幅排序)
2. 过滤单价<20元、>1元的股票
3. 腾讯财经批量获取实时行情+K线数据
4. 技术面+基本面+价格综合评分排序
5. TOP10观察池，TOP1每周推荐

## 买卖区间

- **买入区间**: 现价的95%-102%
- **目标价位**: +12%
- **止损价位**: -8%
- **自动止损**: 持仓亏损≥8%自动卖出
- **自动止盈**: 盈利≥15%自动减仓50%
- **最大持仓**: 5只股票
- **每次买入**: 可用现金30%，不超过¥50,000

## 自我学习

- 记录每次推荐的股票代码、价格、目标/止损价
- 后期评估: 达到目标价=胜、触及止损=负、未达=进行中
- 胜率>65%: 增加技术权重(趋势有效)
- 胜率<35%: 增加基本面权重(趋势失效)
- 权重持久化到 `weights.json`

## Windows注意事项

- `write_file`/`read_file`工具在Windows上写入0字节文件。用 `execute_code` + Python `open()` 操作文件
- 含中文路径(`.learnings/股票/`)需用Python而非shell命令
- 新浪财经API无需Proxy可直连；东方财富API被IP封锁
