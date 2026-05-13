# Scoring Model Detail

## Composite Score Formula

```
Final = Technical × 0.55 + Fundamental × 0.30 + Price × 0.15
```

## Technical Score (0-100)

### MA Trend (Weight within tech: ~25%)
- MA5 > MA10 > MA20 (bullish alignment): +15
- MA5 < MA10 < MA20 (bearish alignment): -15
- Mixed: 0

### MACD (Weight within tech: ~20%)
- DIF > DEA and histogram expanding (golden cross up): +12
- DIF > DEA but histogram shrinking: +5
- DIF < DEA and histogram shrinking (death cross down): -12
- DIF < DEA but histogram shrinking: -5

### KDJ (Weight within tech: ~15%)
- J < 20 (oversold): +8
- K > D (golden cross): +5
- 20 <= J <= 80 and K > D: +3
- J > 80 (overbought): -8
- K < D (death cross): -3

### RSI (Weight within tech: ~10%)
- RSI > 50 (bullish): +5
- RSI < 30 (oversold): +3
- RSI > 70 (overbought): -5

### Volume (Weight within tech: ~10%)
- Volume ratio > 1.5 AND MA bullish: +5
- Volume ratio > 1.5: +2
- Volume ratio < 0.5: -5

### Bonus/Penalty
- Base: 50
- Final: clamped to [5, 95]

## Fundamental Score (0-100)

### PE Ratio (25%)
| Range | Score |
|-------|-------|
| 0 < PE ≤ 12 | 85 (undervalued) |
| 12 < PE ≤ 25 | 70 (fair) |
| 25 < PE ≤ 40 | 50 (slightly high) |
| 40 < PE ≤ 60 | 30 (high) |
| PE > 60 or PE ≤ 0 | 15 (extremely high or negative) |

### PB Ratio (20%)
| Range | Score |
|-------|-------|
| 0 < PB ≤ 1 | 80 (below net asset) |
| 1 < PB ≤ 3 | 65 (fair) |
| 3 < PB ≤ 5 | 45 (high) |
| 5 < PB ≤ 10 | 30 (very high) |
| PB > 10 or PB ≤ 0 | 15 (extremely high) |

### ROE - Return on Equity (25%)
| Range | Score |
|-------|-------|
| > 20% | 90 (excellent) |
| 15-20% | 80 (good) |
| 10-15% | 65 (fair) |
| 5-10% | 45 (low) |
| 0-5% | 30 (poor) |
| < 0% | 40 (negative) |

### Revenue Growth (15%)
| Range | Score |
|-------|-------|
| > 30% | 85 (strong) |
| 15-30% | 70 (good) |
| 5-15% | 55 (fair) |
| 0-5% | 40 (weak) |
| -10 to 0% | 25 (declining) |
| < -10% | 10 (bad) |

### Profit Growth (15%)
Same scale as Revenue Growth.

## Price Score (0-100)

```
Price_Score = max(0, min(100, (MAX_PRICE - price) / MAX_PRICE * 100))
```

Default MAX_PRICE = 20.0

## Confidence Levels

| Score | Stars | Action |
|-------|-------|--------|
| ≥ 70 | ⭐⭐⭐ | Strong buy signal |
| 58-69 | ⭐⭐ | Watch, consider buying |
| < 58 | ⭐ | Neutral/hold |

## Self-Learning Weight Adjustment

After each weekly analysis, the system evaluates past recommendations:

- **Win condition**: Stock price hit target price (+12%)
- **Loss condition**: Stock price hit stop-loss (-8%)

If win rate > 65% over last 10 recommendations:
  → Increase technical weight (market trending, TA works)
If win rate < 35%:
  → Increase fundamental weight (market not trending, FA matters better)
