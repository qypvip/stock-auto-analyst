# Contributing Guide

## Ways to Contribute

### 🐛 Report Bugs
- Open an issue with the full error output
- Include your Python version and OS
- Describe steps to reproduce

### 💡 Feature Requests
- Suggest new scoring indicators
- Propose new data sources
- Share your custom strategy configs

### 🔧 Code Contributions
1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -am "Add my feature"`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

### 📊 Data & Models
- Share your prediction logs (anonymized)
- Contribute backtest results
- Help improve the scoring weights through experimentation

## Development Setup

```bash
git clone https://github.com/qypvip/stock-auto-analyst.git
cd stock-auto-analyst
pip install -r requirements.txt
python stock_auto_analyst.py init
python stock_auto_analyst.py weekly
```

## Code Style

- Follow PEP 8
- Add docstrings for new functions
- Keep the script self-contained (single file)
