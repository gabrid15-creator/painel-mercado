# Baixa XAUUSD M1 (BID) com tick volume da Dukascopy, out/2020 até hoje -> duka/xau_m1_vol.parquet
import lzma, struct, datetime as dt, urllib.request, concurrent.futures as cf, os
import pandas as pd
def dia(d):
    u = f"https://datafeed.dukascopy.com/datafeed/XAUUSD/{d.year}/{d.month-1:02d}/{d.day:02d}/BID_candles_min_1.bi5"
    for _ in range(4):
        try:
            b = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=15).read()
            break
        except Exception as e:
            if '404' in str(e): return []
            b = None
    if not b: return []
    r = lzma.decompress(b); base = dt.datetime(d.year, d.month, d.day)
    out = []
    for i in range(0, len(r), 24):
        t, o, c, l, h, v = struct.unpack('>5if', r[i:i+24])
        if v > 0: out.append((base + dt.timedelta(seconds=t), o/1000, h/1000, l/1000, c/1000, v))
    return out
import sys
Y = int(sys.argv[1])
d0 = max(dt.date(Y, 1, 1), dt.date(2020, 10, 19)); d1 = min(dt.date(Y, 12, 31), dt.date.today() - dt.timedelta(days=1))
ds = [d0 + dt.timedelta(days=i) for i in range((d1-d0).days+1)]
ds = [d for d in ds if d.weekday() != 5]
rows = []
with cf.ThreadPoolExecutor(24) as ex:
    for i, r in enumerate(ex.map(dia, ds)):
        rows += r
        if i % 30 == 0: print(i, len(ds), len(rows), flush=True)
df = pd.DataFrame(rows, columns=['t','o','h','l','c','v']).set_index('t').sort_index()
os.makedirs('duka', exist_ok=True); df.to_parquet(f'duka/xau_{Y}.parquet')
print(len(df), df.index.min(), df.index.max())
