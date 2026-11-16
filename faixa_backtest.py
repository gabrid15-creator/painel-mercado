import urllib.parse, math, statistics as st, json, datetime as dt, collections
from zoneinfo import ZoneInfo
# (histórico diário completo do Yahoo; o resumo vai para docs/data/faixa_backtest.json)
NY = ZoneInfo("America/New_York")
import urllib.request, os, time as _t
def diario(sym):
    f = "hist_" + sym.replace("=", "_").replace("^", "") + ".json"
    if not os.path.exists(f):
        u = f"https://query2.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?period1=0&period2={int(_t.time())}&interval=1d"
        j = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60))["chart"]["result"][0]; q = j["indicators"]["quote"][0]
        json.dump([(t, o, h, l, c) for t, o, h, l, c in zip(j["timestamp"], q["open"], q["high"], q["low"], q["close"]) if None not in (o, h, l, c)], open(f, "w"))
    return [(dt.datetime.fromtimestamp(t, NY).date(), o, h, l, c) for t, o, h, l, c in json.load(open(f))]
ATV = {"XAUUSD": ("GC=F", "^GVZ"), "USDJPY": ("JPY=X", None), "USDCHF": ("CHF=X", None), "EURUSD": ("EURUSD=X", None), "GBPUSD": ("GBPUSD=X", None)}
out = {}
for a, (sym, ivx) in ATV.items():
    b = [x for x in diario(sym) if x[4] > 0]
    # limpa barras ruins (FX do Yahoo tem dias repetidos/zerados): exige variação diária < 15%
    b = [x for i, x in enumerate(b) if i == 0 or abs(math.log(x[4] / b[i - 1][4])) < 0.15]
    g = {d: c for d, o, h, l, c in diario(ivx)} if ivx else None
    res = {}
    for n, nome in ((1, "dia"), (5, "semana"), (21, "mês")):
        anos = collections.defaultdict(lambda: [0, 0, 0, 0])   # n, dentro1, dentro2, nunca saiu 1σ
        i = 22
        while i + n < len(b):
            d0, c0 = b[i][0], b[i][4]
            if g is not None:
                iv = g.get(d0)
                if iv is None: i += 1; continue
                sd = iv / 100 * math.sqrt(n / 252)
            else:
                r = [math.log(b[j][4] / b[j - 1][4]) for j in range(i - 20, i + 1)]
                sd = st.stdev(r) * math.sqrt(252) * 1.09 * math.sqrt(n / 252)
            if sd <= 0: i += n; continue
            c1 = b[i + n][4]; z = abs(math.log(c1 / c0)) / sd
            hi = max(x[2] for x in b[i + 1:i + n + 1]); lo = min(x[3] for x in b[i + 1:i + n + 1])
            dentro_tudo = math.log(hi / c0) <= sd and math.log(c0 / lo) <= sd
            y = anos[b[i + n][0].year]; y[0] += 1; y[1] += z <= 1; y[2] += z <= 2; y[3] += dentro_tudo
            i += n
        tot = [sum(v[k] for v in anos.values()) for k in range(4)]
        res[nome] = {"n": tot[0], "s1": round(tot[1] / tot[0] * 100, 1), "s2": round(tot[2] / tot[0] * 100, 1), "nunca_saiu_s1": round(tot[3] / tot[0] * 100, 1),
                     "desde": min(anos), "anos": {y: [v[0], round(v[1] / v[0] * 100), round(v[2] / v[0] * 100)] for y, v in sorted(anos.items()) if v[0]}}
    out[a] = res
    print(f"\n{a} ({'GVZ' if ivx else 'vol. realizada 21d × 1,09'}), desde {res['dia']['desde']}")
    for nome, r in res.items():
        lim = 30 if nome == 'dia' else 8 if nome == 'semana' else 6; vv = [v[1] for y, v in r['anos'].items() if v[0] >= lim] or [0]; pior1 = min(vv)
        melhor1 = max(vv)
        print(f"  {nome:6} n={r['n']:5}  fechou dentro ±1σ {r['s1']:5}%  ±2σ {r['s2']:5}%  nunca saiu de ±1σ {r['nunca_saiu_s1']:5}%   ±1σ por ano: {pior1}–{melhor1}%")
json.dump(out, open("faixa_bt.json", "w"), ensure_ascii=False)
