# Customization Guide

## Quick Config Changes

Edit these constants at the top of `stock_auto_analyst.py`:

### Stock Screening
```python
POOL_SIZE = 80        # How many candidates to scan (more = slower)
MAX_PRICE = 20.0      # Maximum stock price to consider
```

### Portfolio Management
```python
MAX_POSITIONS = 5     # Maximum concurrent positions
INITIAL_CAPITAL = 100000  # Starting simulation capital
BUY_CASH_RATIO = 0.30     # % of available cash per buy
```

### Risk Management
```python
STOP_LOSS_THRESHOLD = -8   # Stop loss trigger (%)
TAKE_PROFIT_THRESHOLD = 15 # Take profit trigger (%)
```

### Scoring Weights (must sum to ~1.0)
```python
TECH_WEIGHT = 0.55    # Technical analysis weight
FUND_WEIGHT = 0.30    # Fundamental analysis weight
PRICE_WEIGHT = 0.15   # Price factor weight
```

## Example Configs

### Value Investor
```python
MAX_PRICE = 15.0
FUND_WEIGHT = 0.50
TECH_WEIGHT = 0.35
# Only stocks with PE < 15 and ROE > 15%
```

### Momentum Trader
```python
TECH_WEIGHT = 0.70
FUND_WEIGHT = 0.15
# Only stocks with MA bullish + MACD golden cross + volume expanding
```

### Growth Seeker
```python
MAX_PRICE = 30.0
# Require revenue growth > 20%, ROE > 10%
# Accept higher PE for growth potential
```

## Email Configuration

Copy `config/.email_config.example` to `config/.email_config`:

```ini
QQ_EMAIL=yourname@qq.com
QQ_AUTH_CODE=your-smtp-auth-code
TO_EMAIL=recipient@qq.com
```

Get QQ auth code: QQ Mail → Settings → Account → POP3/IMAP/SMTP → Generate
