# Laboratório: grava a cadeia de opções do GLD (CBOE, atraso de 15 min) várias vezes no pregão.
# Guarda só vencimentos até 35 dias e strikes até ±8% do preço. Um CSV por dia: <pasta>/gld/AAAA-MM-DD.csv
import json, sys, os, re, csv, urllib.request, datetime as dt
OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) painel-lab'}
raw = json.load(urllib.request.urlopen(urllib.request.Request('https://cdn.cboe.com/api/global/delayed_quotes/options/GLD.json', headers=UA), timeout=60))
d = raw['data']; ts = raw.get('timestamp', '')
px = float(d.get('current_price') or d.get('close'))
hoje = dt.date.fromisoformat(ts[:10]) if ts else dt.date.today()
rows = []
for o in d.get('options', []):
    m = re.match(r'^[A-Z]+(\d{6})([CP])(\d{8})$', o.get('option', ''))
    if not m: continue
    venc = dt.date(2000 + int(m.group(1)[:2]), int(m.group(1)[2:4]), int(m.group(1)[4:]))
    k = int(m.group(3)) / 1000
    if (venc - hoje).days > 35 or abs(k / px - 1) > 0.08: continue
    rows.append([ts, round(px, 2), venc.isoformat(), m.group(2), k, o.get('open_interest') or 0, o.get('volume') or 0,
                 o.get('iv'), o.get('delta'), o.get('gamma'), o.get('bid'), o.get('ask'), o.get('last_trade_price')])
os.makedirs(f'{OUT}/gld', exist_ok=True)
f = f'{OUT}/gld/{hoje.isoformat()}.csv'; novo = not os.path.exists(f)
# não grava foto repetida (CBOE às vezes devolve o mesmo horário)
if not novo:
    with open(f) as fh:
        last = fh.readlines()[-1].split(',')[0]
    if last == ts:
        print('foto repetida', ts); sys.exit(0)
with open(f, 'a', newline='') as fh:
    w = csv.writer(fh)
    if novo: w.writerow(['ts', 'preco', 'venc', 'tipo', 'strike', 'oi', 'vol', 'iv', 'delta', 'gamma', 'bid', 'ask', 'ultimo'])
    w.writerows(rows)
print(ts, 'GLD', px, 'linhas', len(rows))
