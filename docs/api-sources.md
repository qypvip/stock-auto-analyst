# Data Source Documentation

## Sina Finance (Stock List + Realtime)

**Endpoints:**
- SH A-shares: `https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page={p}&num=40&sort=changepercent&asc=0&node=sh_a`
- SZ A-shares: `https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page={p}&num=40&sort=changepercent&asc=0&node=sz_a`

**Fields:** code, name, trade, pricechange, changepercent, open, high, low, volume, amount, per(PE), pb, mktcap, turnratio

**Status:** ✅ Working (no auth, no rate limit)

## Tencent Finance (Batch Quotes + K-line)

**Endpoints:**
- Realtime: `https://qt.gtimg.cn/q={codes}` (comma-separated, up to ~50)
- K-line: `http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},day,,,{count},qfq`
- Market: `https://qt.gtimg.cn/q=sh000001,sz399001,sz399006`

**Format:** Returns pipe-delimited text, response in GBK encoding

**Status:** ✅ Working (no auth, rate limit is generous)

## East Money (Deprecated)

**Endpoint:** `http://push2.eastmoney.com/api/qt/clist/get`

**Status:** ❌ Blocked from some IP ranges (connection reset). Replaced by Sina Finance.
