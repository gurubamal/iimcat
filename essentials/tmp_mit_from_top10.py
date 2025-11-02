import csv, os, re, sys, math
from glob import glob
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

csv_path = sorted(glob(os.path.join('outputs','top10_news_rank_*.csv')))[-1]
rows=[*csv.DictReader(open(csv_path,'r',encoding='utf-8',errors='ignore'))]

def classify_event(title):
    t=(title or '').lower()
    if re.search(r"\bipo\b|listing|fpo|qip|rights issue", t): return 'IPO/listing'
    if re.search(r"acquisit|merger|buyout|joint venture|\bjv\b|stake (?:buy|sale)", t): return 'M&A/JV'
    if re.search(r"order\b|contract\b|tender|project|deal", t): return 'Order/contract'
    if re.search(r"approval|usfda|sebi|nod|clearance|regulator", t): return 'Regulatory'
    if re.search(r"block deal", t): return 'Block deal'
    if re.search(r"dividend|buyback|payout", t): return 'Dividend/return'
    if re.search(r"result|profit|ebitda|margin|q[1-4]|quarter|yoy|growth", t): return 'Results/metrics'
    if re.search(r"appoints|resigns|ceo|cfo", t): return 'Management'
    return 'General'

def event_baseline(ev):
    e=(ev or '').lower()
    if e.startswith('ipo') or 'listing' in e: return 0.65
    if 'm&a' in e or 'jv' in e: return 0.7
    if 'order' in e or 'contract' in e or 'tender' in e or 'project' in e or 'deal' in e: return 0.8
    if 'regulatory' in e or 'approval' in e: return 0.75
    if 'results' in e or 'metrics' in e: return 0.55
    if 'block deal' in e: return 0.45
    if 'management' in e: return 0.4
    return 0.35

def clamp(v,lo,hi):
    return lo if v<lo else hi if v>hi else v

try:
    import yfinance as yf
except Exception:
    yf=None

def timing_for(ticker):
    global yf
    if yf is None: return None
    sym=ticker if ticker.endswith('.NS') else f"{ticker}.NS"
    try:
        df=yf.download(sym, period='2mo', interval='1d', progress=False, group_by='ticker', auto_adjust=False)
        if df is None or df.empty or len(df)<2:
            return None
        df=df.dropna(); last=df.iloc[-1]; prev=df.iloc[-2]
        pct=None if float(prev['Close'])==0 else (float(last['Close'])-float(prev['Close']))/float(prev['Close'])*100.0
        vol20=float(df['Volume'].iloc[:-1].tail(20).mean() or 0.0)
        vratio=(float(last['Volume'])/vol20) if vol20>0 else None
        if pct is None or vratio is None: return None
        p=clamp(max(0.0,pct)/5.0,0.0,1.0); v=clamp((min(vratio,3.0)-1.0)/2.0,0.0,1.0)
        return 0.5*p+0.5*v
    except Exception:
        return None

results=[]
for r in rows[:20]:
    t=(r.get('ticker') or '').strip().upper(); title=r.get('best_title') or ''; src=r.get('best_source') or ''
    ev=classify_event(title); base=event_baseline(ev)
    magnitude=clamp(0.4*base,0.0,1.0); intensity=clamp(base,0.0,1.2)
    timing=timing_for(t)
    if timing is None: timing=clamp(0.2+base*0.85,0.4,0.9)
    score=magnitude*intensity*timing
    results.append((score,t,ev,title,src,magnitude,intensity,timing))

results.sort(key=lambda x: x[0], reverse=True)
for i,(s,t,ev,title,src,m,i2,tim) in enumerate(results[:10],1):
    print(f"{i:2d}. {t:<10} MIT={s:.4f}  M={m:.3f} I={i2:.3f} T={tim:.3f}  | {ev} - {title[:110]} ({src})")
