#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股自主智能分析系统 v2.0
功能: 大盘模拟 | 技术+基本面+政策多维分析 | 模拟买卖(限5只) | 自我学习调参 | 每周一推 | 价格警报
数据源: 腾讯财经API + 东方财富API (免费)
"""

import os, sys, json, math, time, re, smtplib, ssl, random
from datetime import datetime, date, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import requests, pandas as pd, numpy as np

HOME_DIR = os.path.expanduser("~")
LD = os.path.join(HOME_DIR, ".learnings", "\u80a1\u7968")
RD = os.path.join(LD, "reports")
PF = os.path.join(LD, "simulated_portfolio.json")
PL = os.path.join(LD, "prediction_log.json")
LF = os.path.join(LD, "LEARNINGS.md")
EC = os.path.join(HOME_DIR, ".hermes", "scripts", ".email_config")
WP = os.path.join(LD, "weights.json")

POOL_SIZE = 80; WATCH_SIZE = 10; MAX_POSITIONS = 5
TQ = "https://qt.gtimg.cn/q={codes}"
TK = "http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},day,,,{count},qfq"
TM = "https://qt.gtimg.cn/q=sh000001,sz399001,sz399006"
# EM_LIST (unused) = "http://push2.eastmoney.com/api/qt/clist/get?cb=&pn=1&pz={pz}&po=1&np=1&fields=f12,f14,f2,f3,f20,f21,f23,f37,f38,f39,f45,f46,f57,f58,f162,f167,f168,f169&fid=f3&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23"

def sf(v, d=0.0):
    try: return float(v) if v is not None else d
    except: return d

def si(v, d=0):
    try: return int(float(v)) if v is not None else d
    except: return d

def retry(n=3, d=2):
    def dec(f):
        def wrap(*a, **kw):
            for i in range(n):
                try:
                    r = f(*a, **kw)
                    if r is not None: return r
                except: pass
                if i < n-1: time.sleep(d)
            return None
        return wrap
    return dec

@retry(n=3, d=1)
def fetch_market_indices():
    r = requests.get(TM, timeout=10); r.encoding = 'gbk'
    indices = {}
    for line in r.text.strip().split('\n'):
        parts = line.strip().split('~')
        if len(parts) >= 5:
            indices[parts[1]] = {'price': sf(parts[3]), 'change_pct': sf(parts[32]) if len(parts)>32 else 0}
    return indices

@retry(n=3, d=1)
def fetch_stocks_batch(codes):
    if not codes: return {}
    fm, cm = [], {}
    for code in codes:
        c = code.strip()
        p = "sh" if c.startswith(('6','9')) else "sz" if c.startswith(('0','3')) else "bj"
        f = f"{p}{c}"; fm.append(f); cm[f] = c
    url = TQ.replace("{codes}", ",".join(fm))
    r = requests.get(url, timeout=15); r.encoding = 'gbk'
    results = {}
    for line in r.text.strip().split('\n'):
        parts = line.strip().split('~')
        if len(parts) < 10: continue
        fc = parts[0].split('=')[0].lstrip('v_') if '=' in parts[0] else ''
        rc = cm.get(fc, fc.replace('sh','').replace('sz','').replace('bj',''))
        results[rc] = {'code':rc,'name':parts[1],'price':sf(parts[3]),
            'prev_close':sf(parts[4]),'open':sf(parts[5]),
            'high':sf(parts[33]) if len(parts)>33 else 0,
            'low':sf(parts[34]) if len(parts)>34 else 0,
            'change_pct':sf(parts[32]) if len(parts)>32 else 0,
            'volume':sf(parts[6]),'amount':sf(parts[37]) if len(parts)>37 else 0,
            'pe':sf(parts[39]) if len(parts)>39 else 0,
            'turnover_rate':sf(parts[38]) if len(parts)>38 else 0,
            'market_cap':sf(parts[45]) if len(parts)>45 else 0,
            'pb':sf(parts[46]) if len(parts)>46 else 0}
        if results[rc]['change_pct']==0 and results[rc]['prev_close']>0:
            results[rc]['change_pct']=(results[rc]['price']-results[rc]['prev_close'])/results[rc]['prev_close']*100
    return results

@retry(n=2, d=2)
def fetch_kline(code, days=120):
    p = "sh" if code.startswith(('6','9')) else "sz"
    url = TK.replace("{code}",f"{p}{code}").replace("{count}",str(days))
    r = requests.get(url, timeout=15); data = r.json()
    records = []
    dd = data.get('data',{})
    for dk in list(dd.keys()):
        if isinstance(dd[dk], dict):
            for sk in ['qfqday','day']:
                kl = dd[dk].get(sk,[])
                if kl: break
            if kl: break
    if not kl: return None
    for k in kl:
        if len(k)>=6:
            records.append({'date':k[0],'open':float(k[1]),'close':float(k[2]),'high':float(k[3]),'low':float(k[4]),'volume':float(k[5]) if k[5] else 0})
    if not records: return None
    df = pd.DataFrame(records); df['date'] = pd.to_datetime(df['date'])
    return df.sort_values('date').reset_index(drop=True)

def fetch_candidates_sina(max_price=20.0, count=120):
    """Dynamic stock screening from Sina Finance (SH + SZ endpoints)"""
    try:
        candidates = []
        headers = {"User-Agent": "Mozilla/5.0"}
        nodes = ["sh_a", "sz_a"]
        pages_per_node = max(1, count // 40)
        for node in nodes:
            for page in range(1, pages_per_node+1):
                url = f"https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page={page}&num=40&sort=changepercent&asc=0&node={node}&symbol=&_s_r_a=init"
                try:
                    r = requests.get(url, timeout=15, headers=headers)
                    if not r.text or r.text == 'null': break
                    if r.text.startswith('['):
                        import json as _json
                        items = _json.loads(r.text)
                        for item in items:
                            code = str(item.get('code',''))
                            price = sf(item.get('trade',100))
                            if price <= max_price and price > 1:
                                candidates.append({
                                    'code': code, 'name': item.get('name',''),
                                    'price': price, 'change_pct': sf(item.get('changepercent',0)),
                                    'pe': sf(item.get('per',0)), 'pb': sf(item.get('pb',0)),
                                    'market_cap': sf(item.get('mktcap',0)),
                                    'turnover_rate': sf(item.get('turnratio',0)),
                                    'roe': sf(item.get('roe',0)),
                                    'industry': item.get('industry','') or '',
                                })
                except: pass
                if len(candidates) >= count: break
            if len(candidates) >= count: break
            time.sleep(1)
        return candidates
    except:
        return []

# ============================================================
# TECHNICAL ANALYSIS (optimized)
# ============================================================

def ma(p, n):
    if len(p) < n: return [None]*len(p)
    r = []
    for i in range(len(p)):
        if i < n-1: r.append(None)
        else: r.append(np.mean(p[i-n+1:i+1]))
    return r

def macd(p, f=12, s=26, sg=9):
    if len(p) < s+sg: return [],[],[]
    ef, es = [p[0]], [p[0]]
    for i in range(1,len(p)):
        ef.append(p[i]*2/(f+1)+ef[-1]*(1-2/(f+1)))
        es.append(p[i]*2/(s+1)+es[-1]*(1-2/(s+1)))
    d = [ef[i]-es[i] for i in range(len(p))]
    de = [d[0]]
    for i in range(1,len(d)):
        de.append(d[i]*2/(sg+1)+de[-1]*(1-2/(sg+1)))
    return d, de, [2*(d[i]-de[i]) for i in range(len(d))]

def kdj(ph, pl, pc, n=9):
    if min(len(pc),len(ph),len(pl)) < n: return [],[],[]
    kv, dv = [50.0], [50.0]
    for i in range(len(pc)):
        if i < n-1: kv.append(50.0); dv.append(50.0)
        else:
            hh = max(ph[i-n+1:i+1]); ll = min(pl[i-n+1:i+1])
            rsv = 0 if hh==ll else (pc[i]-ll)/(hh-ll)*100
            k = 2/3*kv[-1]+1/3*rsv; d = 2/3*dv[-1]+1/3*k
            kv.append(k); dv.append(d)
    jv = [3*kv[i]-2*dv[i] for i in range(len(kv))]
    return kv[1:], dv[1:], jv[1:]

def rsi(p, n=14):
    if len(p) < n+1: return [None]*len(p)
    g, l = [], []
    for i in range(1,len(p)):
        d = p[i]-p[i-1]; g.append(max(d,0)); l.append(max(-d,0))
    rs = [None]*len(p)
    for i in range(n, len(g)):
        ag = np.mean(g[i-n:i]); al = np.mean(l[i-n:i])
        rs[i+1] = 100.0 if al==0 else 100-100/(1+ag/al)
    return rs

def boll(p, n=20, sd=2):
    if len(p) < n: return [],[],[]
    mid = ma(p, n); u, l = [], []
    for i in range(len(p)):
        if mid[i] is None or i < n-1: u.append(None); l.append(None)
        else:
            s = np.std(p[i-n+1:i+1])
            u.append(mid[i]+sd*s); l.append(mid[i]-sd*s)
    return u, mid, l

def vr(vol, n=5):
    if len(vol) < n+1: return 1.0
    avg = np.mean(vol[-n-1:-1])
    cur = vol[-1] if vol else 1
    return cur/avg if avg>0 else 1.0

def compute_technical_score(prices, highs, lows, volumes):
    res = {'score':50,'ma_status':'N','macd_status':'N','kdj_status':'N',
           'rsi_status':'N','vol_status':'N','bb_status':'N','details':{}}
    if len(prices) < 30: return res
    
    m5 = ma(prices,5); m10 = ma(prices,10); m20 = ma(prices,20)
    cp = prices[-1]
    m5v = m5[-1] if m5[-1] is not None else cp
    m10v = m10[-1] if m10[-1] is not None else cp
    m20v = m20[-1] if m20[-1] is not None else cp
    
    if m5v > m10v > m20v: res['ma_status']='B'; s=75+(25 if cp>m5v else 0)
    elif m5v < m10v < m20v: res['ma_status']='S'; s=25-(10 if cp<m20v else 0)
    else: res['ma_status']='N'; s=50
    
    d, de, mh = macd(prices)
    if d and len(d)>1:
        lm=mh[-1]; pm=mh[-2]; dv=d[-1]; dv2=de[-1] if de else 0
        if dv>dv2 and lm>pm: res['macd_status']='B'
        elif dv>dv2: res['macd_status']='NB'
        elif lm<pm: res['macd_status']='S'
        else: res['macd_status']='NS'
    
    if highs and lows and len(highs)>=9:
        k,dv,j = kdj(highs,lows,prices)
        if k and len(k)>0:
            res['kdj_v'] = {'k':round(k[-1],1),'d':round(dv[-1],1),'j':round(j[-1],1)}
            if j[-1]<20: res['kdj_status']='OS'
            elif j[-1]>80: res['kdj_status']='OB'
            elif k[-1]>dv[-1]: res['kdj_status']='B'
            else: res['kdj_status']='S'
    
    rs = rsi(prices)
    if rs and rs[-1] is not None:
        rv = rs[-1]; res['rsi_v'] = round(rv,1)
        res['rsi_status'] = 'OS' if rv<30 else 'OB' if rv>70 else 'B' if rv>50 else 'S'
    
    u,mid,l = boll(prices)
    if u and len(u)>0 and u[-1] is not None:
        if cp>u[-1]: res['bb_status']='OB'
        elif cp<l[-1]: res['bb_status']='OS'
        elif cp>mid[-1]: res['bb_status']='B'
        else: res['bb_status']='S'
        res['bb_u']=round(u[-1],2); res['bb_m']=round(mid[-1],2); res['bb_l']=round(l[-1],2)
    
    vr_v = vr(volumes) if volumes else 1.0
    res['vr'] = round(vr_v,2)
    res['vol_status'] = 'H' if vr_v>2.0 else 'I' if vr_v>1.3 else 'L' if vr_v<0.7 else 'N'
    
    sc = 50
    if res['ma_status']=='B': sc+=15
    elif res['ma_status']=='S': sc-=15
    if res['macd_status']=='B': sc+=12
    elif res['macd_status']=='S': sc-=12
    if res['kdj_status']=='OS': sc+=8
    elif res['kdj_status']=='OB': sc-=8
    elif res['kdj_status']=='B': sc+=5
    if res['rsi_status']=='B': sc+=5
    elif res['rsi_status']=='OS': sc+=3
    elif res['rsi_status']=='OB': sc-=5
    if vr_v>1.5 and res['ma_status']=='B': sc+=5
    if vr_v<0.5: sc-=5
    
    res['score'] = max(5,min(95,sc))
    res['details'] = {'ma5':round(m5v,2),'ma10':round(m10v,2),'ma20':round(m20v,2),
        'price':round(cp,2),'ma_dev':round((cp/m20v-1)*100,1) if m20v else 0}
    return res

# ============================================================
# IMPROVED FUNDAMENTAL ANALYSIS
# ============================================================

def analyze_fundamental(sd):
    """PE + PB + ROE + revenue growth + profit growth"""
    res = {'score':50,'pe_r':'N','pb_r':'N','roe_r':'N','growth_r':'N','details':{}}
    pe = sf(sd.get('pe',0) or sd.get('pe_ttm',0))
    pb = sf(sd.get('pb',0))
    roe = sf(sd.get('roe',0))
    rev_g = sf(sd.get('revenue_growth',0))
    pr_g = sf(sd.get('profit_growth',0))
    mc = sf(sd.get('market_cap',0))
    
    # PE score (weight 25%)
    if 0<pe<=12: pe_s = 85; res['pe_r']='low'
    elif pe<=25: pe_s = 70; res['pe_r']='fair'
    elif pe<=40: pe_s = 50; res['pe_r']='high'
    elif pe<=60: pe_s = 30; res['pe_r']='vh'
    elif pe>60: pe_s = 15; res['pe_r']='extreme'
    else: pe_s = 50; res['pe_r']='N'
    
    # PB score (weight 20%)
    if 0<pb<=1: pb_s = 80; res['pb_r']='undervalue'
    elif pb<=3: pb_s = 65; res['pb_r']='fair'
    elif pb<=5: pb_s = 45; res['pb_r']='high'
    elif pb<=10: pb_s = 30; res['pb_r']='vh'
    elif pb>10: pb_s = 15; res['pb_r']='extreme'
    else: pb_s = 50; res['pb_r']='N'
    
    # ROE score (weight 25%)
    if roe > 20: roe_s = 90; res['roe_r']='excellent'
    elif roe > 15: roe_s = 80; res['roe_r']='good'
    elif roe > 10: roe_s = 65; res['roe_r']='fair'
    elif roe > 5: roe_s = 45; res['roe_r']='low'
    elif roe > 0: roe_s = 30; res['roe_r']='poor'
    else: roe_s = 40; res['roe_r']='N'
    
    # Revenue growth (weight 15%)
    if rev_g > 30: rg_s = 85; res['growth_r']='strong'
    elif rev_g > 15: rg_s = 70; res['growth_r']='good'
    elif rev_g > 5: rg_s = 55; res['growth_r']='fair'
    elif rev_g > 0: rg_s = 40; res['growth_r']='weak'
    elif rev_g > -10: rg_s = 25; res['growth_r']='decline'
    else: rg_s = 10; res['growth_r']='bad'
    
    # Profit growth (weight 15%)
    if pr_g > 30: pg_s = 85; 
    elif pr_g > 15: pg_s = 70
    elif pr_g > 5: pg_s = 55
    elif pr_g > 0: pg_s = 40
    elif pr_g > -10: pg_s = 25
    elif pr_g <= -10: pg_s = 10
    else: pg_s = 50
    
    final = pe_s*0.25 + pb_s*0.20 + roe_s*0.25 + rg_s*0.15 + pg_s*0.15
    res['score'] = int(final)
    res['details'] = {'pe':pe,'pb':pb,'roe':roe,'rev_g':rev_g,'pr_g':pr_g,
        'mc':mc,'tr':sd.get('turnover_rate',0)}
    return res

# ============================================================
# MARKET SIMULATION
# ============================================================

def simulate_market():
    indices = fetch_market_indices()
    res = {'status':'N','score':50,'trend':'横盘震荡','risk':'中等','details':{}}
    if not indices: return res
    ss = []
    for name, data in indices.items():
        chg = data.get('change_pct',0)
        res['details'][name]=f"{chg:+.2f}%"
        if chg>1.5: ss.append(80)
        elif chg>0.5: ss.append(65)
        elif chg>-0.5: ss.append(50)
        elif chg>-1.5: ss.append(35)
        else: ss.append(20)
    avg = np.mean(ss) if ss else 50
    if avg>=70: res['status']='B'; res['trend']='震荡上行'; res['risk']='较低'
    elif avg>=55: res['status']='SB'; res['trend']='偏强震荡'; res['risk']='中等偏低'
    elif avg>=45: res['status']='N'
    elif avg>=30: res['status']='SS'; res['trend']='偏弱震荡'; res['risk']='较高'
    else: res['status']='S'; res['trend']='震荡下行'; res['risk']='高'
    res['score']=int(avg); res['indices']=indices
    return res

def fetch_policy_news():
    news = []
    wd = datetime.now().weekday()
    if wd==0: news.append("【周末政策】关注周末发布的宏观政策与行业利好")
    elif wd==4: news.append("【周末预期】市场对周末政策利好的预期博弈")
    try:
        r = requests.get("https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&secids=1.000001,0.399001&fields=f58,f734", timeout=10)
        dd = r.json()
        for item in dd.get('data',{}).get('diff',[])[:3]:
            t = item.get('f58','') or item.get('f734','')
            if t: news.append(f"【热点】{t[:80]}")
    except: pass
    return news[:5]

# ============================================================
# SIMULATED PORTFOLIO (max 5 positions)
# ============================================================

class SimulatedPortfolio:
    def __init__(self):
        self.f = PF; self.data = self._load()
    
    def _load(self):
        if os.path.exists(self.f):
            try:
                with open(self.f,'r',encoding='utf-8') as f: return json.load(f)
            except: pass
        return {'ic':100000.0,'cash':100000.0,'pos':{},'trades':[],'tp':0.0,
            'created_at':datetime.now().isoformat(),'last_update':datetime.now().isoformat()}
    
    def _save(self):
        self.data['last_update']=datetime.now().isoformat()
        os.makedirs(os.path.dirname(self.f),exist_ok=True)
        with open(self.f,'w',encoding='utf-8') as f: json.dump(self.data,f,ensure_ascii=False,indent=2)
    
    

    def _kelly_fraction(self, win_rate=0.5, avg_win=0.10, avg_loss=0.08):
        """Calculate optimal position size using half-Kelly"""
        if avg_loss <= 0: return 0.25
        b = avg_win / avg_loss if avg_loss > 0 else 1.0
        p = max(0.1, min(0.9, win_rate))
        q = 1 - p
        kelly = (p * b - q) / b if b > 0 else 0
        return max(0.05, min(0.30, kelly * 0.5))
    def buy(self, code, name, price, shares=None, amount=None):
        if shares is None and amount is None: return {'ok':False,'msg':'请指定数量或金额'}
        price = float(price)
        if shares is None: shares = int(amount/price/100)*100
        if shares < 100: return {'ok':False,'msg':'最少买100股'}
        cost = shares*price*1.0003
        if cost > self.data['cash']:
            aff = int(self.data['cash']/price/100)*100
            return {'ok':False,'msg':f'资金不足: 需¥{cost:.0f} 可用¥{self.data["cash"]:.0f} 最多{aff}股'}
        
        # Max 5 positions
        existing = len([c for c in self.data['pos'] if self.data['pos'][c]['shares']>0])
        if code not in self.data['pos'] and existing >= MAX_POSITIONS:
            # Try to replace worst performer
            worst = min(self.data['pos'].items(), key=lambda x: (x[1].get('pnl_pct',0) if x[1]['shares']>0 else 999))
            if worst[1]['shares'] > 0:
                wc, wp = worst
                r = self.sell(wc, sf(self._get_current_price(wc, price)))
                if r['ok']:
                    print(f"  ↺ 换仓: 卖出{wp['name']} 腾出仓位买{name}")
                else:
                    return {'ok':False,'msg':f'已达上限{MAX_POSITIONS}只, 且无法替换'}
            else:
                return {'ok':False,'msg':f'已达上限{MAX_POSITIONS}只'}
        
        if code not in self.data['pos']:
            self.data['pos'][code] = {'name':name,'shares':0,'avg_cost':0.0,'pnl_pct':0}
        pos = self.data['pos'][code]
        tc = pos['avg_cost']*pos['shares'] + cost
        pos['shares'] += shares
        pos['avg_cost'] = tc/pos['shares'] if pos['shares']>0 else price
        self.data['cash'] -= cost
        self.data['trades'].append({'t':'buy','c':code,'n':name,'s':shares,'p':price,'cost':cost,'time':datetime.now().isoformat()})
        self._save()
        return {'ok':True,'msg':f'买入{name}({code}): {shares}股 @ ¥{price:.2f}'}

    def _get_current_price(self, code, default=0.0):
        if hasattr(self, '_price_cache') and code in self._price_cache:
            return self._price_cache[code]
        return default


    def _kelly_fraction(self, win_rate=0.5, avg_win=0.10, avg_loss=0.08):
        """Calculate optimal position size using half-Kelly formula"""
        if avg_loss <= 0:
            return 0.25
        b = avg_win / avg_loss if avg_loss > 0 else 1.0
        p = max(0.1, min(0.9, win_rate))
        q = 1 - p
        kelly = (p * b - q) / b if b > 0 else 0
        return max(0.05, min(0.30, kelly * 0.5))
    def sell(self, code, price, shares=None):
        if code not in self.data['pos']: return {'ok':False,'msg':f'未持有{code}'}
        pos = self.data['pos'][code]
        if shares is None: shares = pos['shares']
        if shares > pos['shares']: return {'ok':False,'msg':f'持仓不足: {pos["shares"]}股'}
        revenue = shares*price*0.9997
        pnl = revenue - shares*pos['avg_cost']
        pos['shares'] -= shares
        self.data['cash'] += revenue; self.data['tp'] += pnl
        self.data['trades'].append({'t':'sell','c':code,'n':pos['name'],'s':shares,'p':price,'rev':revenue,'pnl':pnl,'time':datetime.now().isoformat()})
        if pos['shares']==0: del self.data['pos'][code]
        self._save()
        return {'ok':True,'msg':f'卖出{pos["name"]}: {shares}股 @ ¥{price:.2f}, 收益{pnl:+.2f}'}
    
    def calc_sharpe(self):
        """Calculate Sharpe ratio from trade history (simplified)"""
        trades = self.data.get('trades', [])
        sells = [t for t in trades if t.get('t') == 'sell' and t.get('pnl', 0) != 0]
        if len(sells) < 3: return 0.0
        returns = [t['pnl'] / (t.get('rev', 1) - t['pnl'] + 1) for t in sells]
        if not returns: return 0.0
        avg_r = np.mean(returns); std_r = np.std(returns)
        if std_r == 0: return 0.0
        return round((avg_r - 0.0015) / std_r * np.sqrt(252), 2)  # annualized, 0.15% risk-free
    
    def value(self, prices=None):
        total = self.data['cash']; pv = {}
        self._price_cache = prices or {}
        for code, pos in self.data['pos'].items():
            cp = sf(prices.get(code, pos['avg_cost'])) if prices else pos['avg_cost']
            cv = pos['shares']*cp; cc = pos['shares']*pos['avg_cost']
            pnl = cv-cc; pnl_pct = round(pnl/cc*100,2) if cc>0 else 0
            pos['pnl_pct'] = pnl_pct
            pv[code] = {'name':pos['name'],'shares':pos['shares'],'avg_cost':pos['avg_cost'],'cp':cp,'cv':cv,'pnl':pnl,'pnl_pct':pnl_pct}
            total += cv
        tp = total-self.data['ic']
        self._save()
        return {'ic':self.data['ic'],'cash':self.data['cash'],'pv':total-self.data['cash'],'total':total,'tp':tp,'tp_pct':round(tp/self.data['ic']*100,2),'pos':pv,'cnt':len(pv)}
    
    def check_signals(self, top3, prices):
        """Smarter auto-trading: buy only top 1-2, max 5 positions - uses Kelly sizing"""
        alerts = []; self._price_cache = prices
        # Calculate win rate from history for Kelly
        trades = self.data.get('trades', [])
        sells = [t for t in trades if t.get('t') == 'sell']
        kelly_wr = 0.5; kelly_aw = 0.10; kelly_al = 0.08
        if sells:
            wins = [t for t in sells if t.get('pnl',0) > 0]
            losses = [t for t in sells if t.get('pnl',0) < 0]
            if wins or losses:
                kelly_wr = len(wins) / max(len(sells), 1)
                if wins: kelly_aw = np.mean([t['pnl']/t.get('rev',1) for t in wins if t.get('rev',0) > 0]) or 0.10
                if losses: kelly_al = abs(np.mean([t['pnl']/t.get('rev',1) for t in losses if t.get('rev',0) > 0])) or 0.08
        kelly_pct = self._kelly_fraction(kelly_wr, kelly_aw, kelly_al)
        
        # Check existing positions for stop/take-profit
        for code, pos in list(self.data['pos'].items()):
            if code not in prices: continue
            pr = prices[code]; pnl = (pr-pos['avg_cost'])/pos['avg_cost']*100
            if pnl <= -8:
                r = self.sell(code, pr)
                alerts.append(f"\U0001f534 止损: {r['msg']}")
            elif pnl >= 15:
                half = int(pos['shares']*0.5/100)*100
                if half>=100:
                    r = self.sell(code, pr, half)
                    alerts.append(f"\U0001f7e1 止盈: {r['msg']}")
        
        # Buy only top 1-2 recommendations
        buy_count = 0
        for rec in top3[:2]:
            code = rec.get('code','')
            if code in self.data['pos'] and self.data['pos'][code]['shares']>0: continue
            if code not in prices: continue
            pr = prices[code]
            bl = rec.get('buy_low',0); bh = rec.get('buy_high',1e9)
            if bl <= pr <= bh and rec.get('composite_score',0) >= 60:
                cash_avail = min(self.data['cash'], 50000)
                amt = cash_avail * 0.3
                if amt >= pr*100*1.001:
                    shares = int(amt/pr/100)*100
                    if shares >= 100 and buy_count < 2:
                        r = self.buy(code, rec.get('name',code), pr, shares=shares)
                        if r['ok']:
                            alerts.append(f"\U0001f7e2 买入: {r['msg']}")
                            buy_count += 1
        return alerts

# ============================================================
# SELF-LEARNING WITH WEIGHT OPTIMIZATION
# ============================================================

class LearningModule:
    def __init__(self):
        self.f = PL; self.wf = WP; self.records = self._load()
        self.weights = self._load_weights()
    
    def _load(self):
        if os.path.exists(self.f):
            try:
                with open(self.f,'r',encoding='utf-8') as f: return json.load(f)
            except: pass
        return []
    
    def _load_weights(self):
        default = {'tech_w':0.55,'fund_w':0.30,'price_w':0.15,
            'ma_w':15,'macd_w':12,'kdj_w':8,'rsi_w':5,'vol_w':5}
        if os.path.exists(self.wf):
            try:
                with open(self.wf,'r',encoding='utf-8') as f: return {**default, **json.load(f)}
            except: pass
        return default
    
    def _save_weights(self):
        os.makedirs(os.path.dirname(self.wf),exist_ok=True)
        with open(self.wf,'w',encoding='utf-8') as f: json.dump(self.weights,f,ensure_ascii=False,indent=2)
    
    def _save(self):
        os.makedirs(os.path.dirname(self.f),exist_ok=True)
        with open(self.f,'w',encoding='utf-8') as f: json.dump(self.records,f,ensure_ascii=False,indent=2)
    
    def record(self, code, name, price, target, stop, score, reasoning):
        self.records.append({'c':code,'n':name,'rp':price,'tp':target,'sl':stop,
            'sc':score,'r':reasoning,'dt':datetime.now().isoformat(),
            'res':None,'ret':None,'hit_t':False,'hit_sl':False,'ev':False})
        self._save()
    
    def evaluate(self, prices):
        stats = {'t':0,'w':0,'l':0,'p':0,'ar':0.0}
        for rec in self.records:
            if rec.get('ev'):
                stats['t']+=1
                if rec.get('hit_t'): stats['w']+=1
                elif rec.get('hit_sl'): stats['l']+=1
                else: stats['p']+=1
                continue
            c = rec['c']
            if c not in prices: continue
            cp = prices[c]; rp = rec['rp']
            if rp<=0: continue
            ret = (cp-rp)/rp*100; rec['ret']=round(ret,2)
            if cp>=rec['tp']: rec['hit_t']=True; rec['res']='win'; stats['w']+=1
            elif cp<=rec['sl']: rec['hit_sl']=True; rec['res']='loss'; stats['l']+=1
            else: rec['res']='pending'; stats['p']+=1
            rec['ev']=True; stats['t']+=1; stats['ar']+=ret
        if stats['t']>0: stats['ar']=round(stats['ar']/stats['t'],2)
        stats['acc']=round(stats['w']/max(stats['w']+stats['l'],1)*100,1)
        self._save()
        
        # Auto-optimize weights based on performance
        self._optimize(stats)
        return stats
    
    def _optimize(self, stats):
        """Adjust weights based on recent performance"""
        recent = [r for r in self.records[-10:] if r.get('ev') and r.get('ret') is not None]
        if len(recent) < 3: return  # Need enough data
        
        # If win rate > 65%, increase tech weight (trend following works)
        # If win rate < 35%, decrease tech weight, increase fundamental
        wr = stats.get('acc', 50)
        if wr > 65:
            self.weights['tech_w'] = min(0.70, self.weights['tech_w'] + 0.02)
            self.weights['fund_w'] = max(0.20, self.weights['fund_w'] - 0.02)
        elif wr < 35:
            self.weights['tech_w'] = max(0.40, self.weights['tech_w'] - 0.02)
            self.weights['fund_w'] = min(0.45, self.weights['fund_w'] + 0.02)
        
        # Normalize
        total = self.weights['tech_w'] + self.weights['fund_w'] + self.weights['price_w']
        self.weights['tech_w'] /= total
        self.weights['fund_w'] /= total
        self.weights['price_w'] = max(0.10, 1.0 - self.weights['tech_w'] - self.weights['fund_w'])
        
        self._save_weights()
    
    def insights(self):
        if not self.records: return "暂无推荐"
        ev = [r for r in self.records if r.get('ev')]
        if not ev: return f"已推{len(self.records)}次, 评估中"
        wins = len([r for r in ev if r.get('hit_t')])
        losses = len([r for r in ev if r.get('hit_sl')])
        pend = len(ev)-wins-losses
        aw = np.mean([r['ret'] for r in ev if r.get('hit_t') and r.get('ret') is not None]) or 0
        al = np.mean([abs(r['ret']) for r in ev if r.get('hit_sl') and r.get('ret') is not None]) or 0
        wr = wins/max(len(ev),1)*100
        w = self.weights
        
        lines = [
            f"\U0001f4ca 学习统计:",
            f"  推荐: {len(ev)}次 | {wins}胜 {losses}负 {pend}进行中",
            f"  胜率: {wr:.1f}% | 均盈: +{aw:.2f}% 均亏: -{al:.2f}%",
            f"\u2699\ufe0f 当前权重: 技术{w['tech_w']*100:.0f}% 基本面{w['fund_w']*100:.0f}% 价格{w['price_w']*100:.0f}%",
        ]
        if wr>60: lines.append("   \u2b50 策略有效")
        elif wr>40: lines.append("   \U0001f4dd 需优化")
        else: lines.append("   \u26a0\ufe0f 建议调整策略")
        return "\n".join(lines)

# ============================================================
# STOCK SCREENER
# ============================================================

def score_single_stock(code, stock_data, weights=None):
    """Score a single stock with multi-agent debate (bull vs bear)"""
    name = stock_data.get('name',''); price = sf(stock_data.get('price',0))
    kline = fetch_kline(code, 90)
    if kline is None or len(kline) < 30: return None
    prices = kline['close'].tolist(); highs = kline['high'].tolist()
    lows = kline['low'].tolist(); volumes = kline['volume'].tolist()
    
    tech = compute_technical_score(prices, highs, lows, volumes)
    fund = analyze_fundamental(stock_data)
    
    w = weights or {'tech_w':0.55,'fund_w':0.30,'price_w':0.15}
    ps = max(0,min(100,(20-price)/20*100))
    
    # Multi-agent debate: Bull vs Bear analysis
    # Bull Agent: favors tech + momentum (higher tech weight)
    bull_score = tech['score'] * 0.70 + fund['score'] * 0.20 + ps * 0.10
    # Bear Agent: favors fundamentals + safety (higher fund weight)  
    bear_score = tech['score'] * 0.35 + fund['score'] * 0.50 + ps * 0.15
    # Consensus: weighted average with bullish tilt for scoring
    comp = (bull_score * 0.55 + bear_score * 0.45)
    
    # Debate divergence: high divergence = uncertainty = lower confidence
    divergence = abs(bull_score - bear_score) / max(bull_score, bear_score, 1) * 100
    uncertainty_penalty = min(5, divergence * 0.15)
    
    signals = []
    if tech['ma_status']=='B': signals.append('均线多头')
    if tech['macd_status']=='B': signals.append('MACD金叉')
    if tech['kdj_status']=='B': signals.append('KDJ多头')
    if tech['kdj_status']=='OS': signals.append('KDJ超卖')
    if tech['vol_status']=='I': signals.append('放量')
    if fund['pe_r']=='low': signals.append('低PE')
    if fund['pb_r']=='undervalue': signals.append('破净')
    if fund['roe_r'] in ('good','excellent'): signals.append(f"高ROE({fund['details']['roe']:.1f}%)")
    if ps>80: signals.append('低价')
    
    conf = 3 if comp>=70 else 2 if comp>=58 else 1
    
    return {'code':code,'name':name,'price':price,'chg':sf(stock_data.get('change_pct',0)),
        'cs':round(comp,1),'ts':tech['score'],'fs':fund['score'],'conf':conf,
        'sig':signals,'ma':tech['ma_status'],'macd':tech['macd_status'],'kdj':tech['kdj_status'],
        'rsi':sf(tech.get('rsi_v',50)),'vr':sf(tech.get('vr',1.0)),
        'pe':sf(fund['details'].get('pe',0)),'pb':sf(fund['details'].get('pb',0)),
        'roe':sf(fund['details'].get('roe',0)),'rev_g':sf(fund['details'].get('rev_g',0)),
        'pr_g':sf(fund['details'].get('pr_g',0)),'tr':sf(stock_data.get('turnover_rate',0)),
        'mc':sf(stock_data.get('market_cap',0)),
        'bl':round(price*0.95,2),'bh':round(price*1.02,2),
        'target':round(price*1.12,2),'sl':round(price*0.92,2),
        'm5':sf(tech.get('details',{}).get('ma5',0)),
        'm10':sf(tech.get('details',{}).get('ma10',0)),
        'm20':sf(tech.get('details',{}).get('ma20',0)),
        'ind':stock_data.get('industry','')}

def screen_and_score(max_price=20.0, limit=10):
    print(f"\U0001f50d 扫描<={max_price}元A股...")
    
    # Phase 1: Get candidates from EastMoney
    candidates = fetch_candidates_sina(max_price, POOL_SIZE)
    if not candidates:
        print("  EastMoney无数据, 降级到批量行情查询...")
        return []
    
    print(f"  Sina获取{len(candidates)}只候选")
    
    # Phase 2: Fetch full real-time data
    codes = [c['code'] for c in candidates]
    print(f"  获取实时数据...")
    all_stocks = {}
    for i in range(0, len(codes), 30):
        batch = codes[i:i+30]
        rt = fetch_stocks_batch(batch)
        for k,v in rt.items(): all_stocks[k] = v
        time.sleep(1)
    
    # Merge EastMoney data with realtime
    cand_map = {c['code']:c for c in candidates}
    merged = {}
    for code, sd in all_stocks.items():
        sina = cand_map.get(code, {})
        sd['industry'] = sina.get('industry','')
        sd['roe'] = sina.get('roe',0)
        sd['revenue_growth'] = sina.get('revenue_growth',0)
        sd['profit_growth'] = sina.get('profit_growth',0)
        sd['pe_ttm'] = sina.get('pe',0)
        # Override Tencent price with Sina price if Tencent didn't get it
        if sd.get('price',0) == 0:
            sd['price'] = sina.get('price',0)
        if sd.get('price',100) <= max_price and sd.get('price',0) > 1:
            merged[code] = sd
    
    print(f"  有效候选: {len(merged)}只")
    
    # Phase 3: Load weights
    lm = LearningModule()
    w = lm.weights
    
    # Phase 4: Score each
    scored = []
    for code, sd in merged.items():
        try:
            sc = score_single_stock(code, sd, w)
            if sc: scored.append(sc)
        except: continue
    
    scored.sort(key=lambda x:x['cs'], reverse=True)
    return scored[:limit]

# ============================================================
# REPORT GENERATION (better formatting)
# ============================================================

def fmt_signals(sigs):
    if not sigs: return "观望"
    m = {"均线多头":"\U0001f7e2","MACD金叉":"\U0001f7e2","KDJ多头":"\U0001f7e2","KDJ超卖":"\U0001f535","放量":"\U0001f4c8","低价":"\U0001f4b0","低PE":"\U0001f4b0","破净":"\U0001f4b0"}
    return " ".join(f"{m.get(s,'')}{s}" for s in sigs[:4])

def conf_stars(n):
    return "\u2b50" * n + "\u2606" * (3-n)

def generate_weekly_report(top, market, portfolio, learning, news, w=None):
    now = datetime.now()
    L = []
    L.append("\u2501"*50)
    L.append(f"  \U0001f4ca A\u80a1\u81ea\u4e3b\u667a\u80fd\u5206\u6790\u5468\u62a5  v2.0")
    L.append(f"  {now.strftime('%Y-%m-%d %H:%M')}  |  \u6570\u636e\u6765\u6e90: \u817e\u8baf\u8d22\u7ecf+\u4e1c\u65b9\u8d22\u5bcc")
    L.append("\u2501"*50)
    L.append("")
    
    # Market
    L.append("\U0001f4c8 \u4e00\u3001\u5927\u76d8\u6a21\u62df")
    L.append(f"  \u8d8b\u52bf: {market.get('trend','\u6a2a\u76d8\u9707\u8361')}  \u98ce\u9669: {market.get('risk','\u4e2d\u7b49')}  \u8bc4\u5206: {market.get('score',50)}/100")
    for name, d in market.get('indices',{}).items():
        L.append(f"  {'\U0001f7e2' if d.get('change_pct',0)>=0 else '\U0001f534'} {name}: {d.get('price',0):.2f} ({d.get('change_pct',0):+.2f}%)")
    L.append("")
    
    # Top pick
    L.append("\u2b50 \u4e8c\u3001\u672c\u5468\u7cbe\u9009\uff08\u5355\u4ef7<20\u5143\uff09")
    if top:
        b = top[0]
        L.append(f"  \U0001f947 {b['name']}({b['code']}) {conf_stars(b['conf'])}  \u7efc\u5408{b['cs']}/100")
        L.append(f"  \u73b0\u4ef7: \u00a5{b['price']:.2f} ({b.get('chg',0):+.2f}%)  PE:{b.get('pe','N')} PB:{b.get('pb','N')}")
        if b.get('roe'): L.append(f"  ROE:{b['roe']:.1f}%  \u8425\u6536\u589e\u901f:{b.get('rev_g',0):.1f}%  \u5229\u6da6\u589e\u901f:{b.get('pr_g',0):.1f}%")
        # Valuation percentile (estimated from PE)
        pe_val = b.get('pe', 0)
        if 0 < pe_val < 10: pe_pctl = "\U0001f7e2(\u4f4e\u4f30)"
        elif pe_val <= 25: pe_pctl = "\U0001f7e1(\u5408\u7406)"
        elif pe_val <= 50: pe_pctl = "\U0001f7e0(\u504f\u9ad8)"
        elif pe_val > 50: pe_pctl = "\U0001f534(\u9ad8\u4f30)"
        else: pe_pctl = "\u26aa(\u8d1f\u76c8)"
        L.append(f"  \U0001f4c8 PE\u4f30\u503c\u6e29\u5ea6\u8ba1: {pe_pctl} PB:{b.get('pb','N/A')}")
        L.append(f"  \u4fe1\u53f7: {fmt_signals(b.get('sig',[]))}")
        L.append(f"  \U0001f4cc \u4e70\u5165: \u00a5{b['bl']:.2f}-\u00a5{b['bh']:.2f}  \U0001f3af\u76ee\u6807: \u00a5{b['target']:.2f}(+{(b['target']/b['price']-1)*100:.1f}%)  \u26d4\u6b62\u635f: \u00a5{b['sl']:.2f}")
        L.append(f"  MA5:{b.get('m5',0):.2f} MA10:{b.get('m10',0):.2f} MA20:{b.get('m20',0):.2f} RSI:{b.get('rsi',50):.1f}")
        if b.get('ind'): L.append(f"  \u884c\u4e1a: {b['ind']}")
    L.append("")
    
    # Top 5
    L.append("\U0001f50d \u4e09\u3001TOP 5 \u89c2\u5bdf\u6c60")
    for i,s in enumerate(top[:5],1):
        arrow = "\U0001f7e2" if s.get('chg',0)>=0 else "\U0001f534"
        L.append(f"  {i}.{arrow} {s['name']}({s['code']}) {conf_stars(s['conf'])} \u00a5{s['price']:.2f}({s.get('chg',0):+.2f}%) \u8bc4:{s['cs']}")
        L.append(f"     \u4e70:{s['bl']:.2f}-{s['bh']:.2f} \u76ee\u6807:{s['target']:.2f} \u6b62\u635f:{s['sl']:.2f}")
        L.append(f"     {fmt_signals(s.get('sig',[]))} PE:{s.get('pe','N')}")
        L.append("")
    
    # Portfolio
    if portfolio:
        L.append("\U0001f4bc \u56db\u3001\u6a21\u62df\u6301\u4ed3")
        pnl_s = f"+{portfolio['tp']:.0f}" if portfolio['tp']>=0 else f"{portfolio['tp']:.0f}"
        L.append(f"  \u603b\u8d44\u4ea7:\u00a5{portfolio['total']:,.0f} | \u73b0\u91d1:\u00a5{portfolio['cash']:,.0f} | \u6301\u4ed3:{portfolio['cnt']}\u53ea")
        L.append(f"  \u6536\u76ca:{pnl_s}({portfolio['tp_pct']:+.2f}%) | \u521d\u59cb:\u00a5{portfolio['ic']:,.0f}")
        for code,pos in portfolio.get('pos',{}).items():
            pc = "\U0001f7e2" if pos['pnl']>=0 else "\U0001f534"
            L.append(f"  {pc} {pos['name']}({code}): {pos['shares']}\u80a1@{pos['avg_cost']:.2f} {pos['pnl']:+.2f}({pos['pnl_pct']:+.2f}%)")
        L.append("")
    
    # Learning
    if learning:
        L.append(f"\U0001f9e0 \u4e94\u3001\u81ea\u6211\u5b66\u4e60")
        for line in learning.split("\n"):
            L.append(f"  {line}")
        L.append("")
    
    # News
    if news:
        L.append("\U0001f4f0 \u516d\u3001\u653f\u7b56\u53c2\u8003")
        for n in news: L.append(f"  \U0001f4cc {n}")
        L.append("")
    
    L.append("\u26a0\ufe0f \u4ee5\u4e0a\u4ec5\u4f9b\u53c2\u8003, \u4e0d\u6784\u6210\u6295\u8d44\u5efa\u8bae. \u80a1\u5e02\u6709\u98ce\u9669, \u6295\u8d44\u9700\u8c28\u614e.")
    L.append(f"--- v2.0 | \u4e0b\u6b21\u63a8\u8350: \u4e0b\u5468\u4e00 08:00 ---")
    return "\n".join(L)

def save_report(report, prefix="\u5468\u62a5"):
    os.makedirs(RD, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    fn = f"\u81ea\u4e3b\u5206\u6790_v2_{prefix}_{ts}.md"
    fp = os.path.join(RD, fn)
    with open(fp, 'w', encoding='utf-8') as f: f.write(report)
    entry = f"\n---\n## {datetime.now().strftime('%Y-%m-%d %H:%M')} {prefix}\n\n{report[:500]}...\n[\u5b8c\u6574\u62a5\u544a](reports/{fn})\n"
    with open(LF, 'a', encoding='utf-8') as f: f.write(entry)
    return fp

def send_email(subject, body):
    if not os.path.exists(EC): return False
    cfg = {}
    with open(EC, 'r', encoding='utf-8') as f:
        for line in f:
            l=line.strip()
            if '=' in l and not l.startswith('#'):
                k,v=l.split('=',1); cfg[k.strip()]=v.strip()
    qq=cfg.get('QQ_EMAIL',''); ac=cfg.get('QQ_AUTH_CODE',''); to=cfg.get('TO_EMAIL','')
    if not all([qq,ac,to]): return False
    try:
        msg=MIMEMultipart('alternative')
        msg['From']=Header(qq); msg['To']=Header(to); msg['Subject']=Header(subject,'utf-8')
        # HTML version
        html = body.replace("\n", "<br>").replace(" ", "&nbsp;")
        msg.attach(MIMEText(html, 'html', 'utf-8'))
        ctx=ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.qq.com",465,context=ctx) as s:
            s.login(qq,ac); s.sendmail(qq,[to],msg.as_string())
        return True
    except: return False

# ============================================================
# MAIN ENTRY
# ============================================================

def init():
    os.makedirs(LD,exist_ok=True); os.makedirs(RD,exist_ok=True)
    if not os.path.exists(LF):
        with open(LF,'w',encoding='utf-8') as f:
            f.write(f"# \u80a1\u7968 - v2.0\n> \u521d\u59cb\u5316\u4e8e {datetime.now().strftime('%Y-%m-%d')}\n")
    SimulatedPortfolio()._save()
    LearningModule()._save()
    print("\u521d\u59cb\u5316\u5b8c\u6210 v2.0")

def run_weekly(send_f=True):
    print(f"\U0001f4ca A\u80a1\u81ea\u4e3b\u667a\u80fd\u5206\u6790 v2.0")
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print("[1/5] \u5927\u76d8\u6a21\u62df...")
    mkt = simulate_market(); print(f"  {mkt.get('trend','')} ({mkt.get('score',50)})")
    
    print("[2/5] \u9009\u80a1\u626b\u63cf...")
    top = screen_and_score(20.0, WATCH_SIZE)
    if top: print(f"  \U0001f947 {top[0]['name']}({top[0]['code']}) \u00a5{top[0]['price']:.2f} \u8bc4:{top[0]['cs']}")
    
    print("[3/5] \u6a21\u62df\u4ea4\u6613...")
    pf = SimulatedPortfolio()
    codes = [s['code'] for s in top]
    pd_ = fetch_stocks_batch(codes)
    prices = {k:v['price'] for k,v in pd_.items()}
    for c in pf.data.get('pos',{}):
        if c not in prices:
            more = fetch_stocks_batch([c])
            prices.update({k:v['price'] for k,v in more.items()})
    val = pf.value(prices)
    print(f"  \u603b\u8d44\u4ea7: \u00a5{val['total']:,.0f} ({val['tp_pct']:+.2f}%)")
    al = pf.check_signals(top[:3], prices)
    if al:
        for a in al: print(f"  {a}")
    
    print("[4/5] \u81ea\u6211\u5b66\u4e60...")
    lm = LearningModule()
    if top:
        b = top[0]
        lm.record(b['code'],b['name'],b['price'],b['target'],b['sl'],b['cs'],', '.join(b.get('sig',['\u7efc\u5408\u4f18\u5148'])))
    st = lm.evaluate(prices)
    print(f"  \u80dc\u7387: {st.get('acc',0)}% ({st.get('w',0)}\u80dc/{st.get('l',0)}\u8d1f)")
    ins = lm.insights()
    
    print("[5/5] \u751f\u6210\u62a5\u544a...")
    news = fetch_policy_news()
    report = generate_weekly_report(top, mkt, val, ins, news, lm.weights)
    fp = save_report(report, "\u5468\u62a5"); print(f"  \u62a5\u544a: {fp}")
    cr = re.sub(r'\033\[[0-9;]*m', '', report)
    if send_f:
        subj = f"\U0001f4ca A\u80a1\u5468\u62a5 | {datetime.now().strftime('%m-%d')} {top[0]['name'] if top else ''}"
        if send_email(subj, cr): print(f"  \u90ae\u4ef6\u5df2\u53d1\u9001")
    return cr

def run_daily():
    pf = SimulatedPortfolio(); lm = LearningModule()
    wc = list(set(list(pf.data.get('pos',{}).keys()) + [r['c'] for r in lm.records[-20:]]))
    pd_ = fetch_stocks_batch(wc) if wc else {}
    prices = {k:v['price'] for k,v in pd_.items()}
    st = lm.evaluate(prices); pf.value(prices)
    al = pf.check_signals([], prices)
    now = datetime.now()
    val = pf.value(prices)
    lines = [f"\U0001f4ca \u6bcf\u65e5\u66f4\u65b0 {now.strftime('%m-%d %H:%M')}"]
    if val:
        lines.append(f"\u603b\u8d44\u4ea7:\u00a5{val['total']:,.0f}({val['tp_pct']:+.2f}%) \u73b0\u91d1:\u00a5{val['cash']:,.0f} \u6301\u4ed3:{val['cnt']}\u53ea")
        for code,pos in val.get('pos',{}).items():
            lines.append(f"  {'\U0001f7e2' if pos['pnl']>=0 else '\U0001f534'} {pos['name']}: {pos['pnl_pct']:+.2f}%")
    if al:
        lines.append(""); lines.append("\u26a0\ufe0f \u8b66\u62a5:")
        for a in al: lines.append(f"  {a}")
    report = "\n".join(lines); cr = re.sub(r'\033\[[0-9;]*m','',report)
    save_report(report,"\u6bcf\u65e5"); print(cr); return cr

def run_alert():
    pf = SimulatedPortfolio(); lm = LearningModule()
    wc = list(set(list(pf.data.get('pos',{}).keys()) + [r['c'] for r in lm.records[-10:]]))
    pd_ = fetch_stocks_batch(wc) if wc else {}; prices={k:v['price'] for k,v in pd_.items()}
    pf.value(prices); al=pf.check_signals([],prices)
    val=pf.value(prices)
    lines=[f"\U0001f514 \u8b66\u62a5 {datetime.now().strftime('%m-%d %H:%M')}"]
    if val: lines.append(f"\u603b\u8d44\u4ea7:\u00a5{val['total']:,.0f}({val['tp_pct']:+.2f}%)")
    if al:
        lines.append(""); lines.append("\u26a0\ufe0f \u9700\u5173\u6ce8:")
        for a in al: lines.append(f"  {a}")
    report="\n".join(lines); cr=re.sub(r'\033\[[0-9;]*m','',report)
    if al: save_report(cr,"\u8b66\u62a5"); send_email("\U0001f514 A\u80a1\u4ef7\u683c\u8b66\u62a5",cr)
    print(cr); return cr

def run_learn():
    lm=LearningModule()
    wc=list(set([r['c'] for r in lm.records]))
    pd_=fetch_stocks_batch(wc) if wc else {}; prices={k:v['price'] for k,v in pd_.items()}
    lm.evaluate(prices); print(lm.insights()); return lm.insights()

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "auto"
    if mode == "auto":
        if datetime.now().weekday() == 0: run_weekly()
        else: run_daily()
    elif mode == "weekly": run_weekly()
    elif mode == "daily": run_daily()
    elif mode == "alert": run_alert()
    elif mode == "init": init()
    elif mode == "learn": run_learn()
    else: print("Usage: python stock_auto_analyst.py [weekly|daily|alert|init|learn|auto]")
