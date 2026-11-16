"""A amplitude até cedo (Ásia + Londres, 18h → 9h NY) diz se o RESTO do dia (9h → 17h NY) vai ser grande? Futuros 1 h, 2 anos (Yahoo).
σ = vol. realizada 21 dias × 1,09 de fechamentos diários anteriores (sem olhar o futuro). Mede correlação de log(amplitude cedo/σ) com
log(amplitude do resto/σ), t, metades, e % de dias "grandes" (resto ≥ mediana) quando o cedo está no terço de cima × de baixo.
Rodar: python3 testes/range_cedo.py"""
import json, urllib.request, datetime as dt, math, statistics as st
from zoneinfo import ZoneInfo
NY = ZoneInfo("America/New_York")
def baixa(s, r, i):
    u = f"https://query2.finance.yahoo.com/v8/finance/chart/{s}?range={r}&interval={i}"
    j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read())["chart"]["result"][0]
    q = j["indicators"]["quote"][0]
    return [(dt.datetime.fromtimestamp(t, NY), h, l, c) for t, h, l, c in zip(j["timestamp"], q["high"], q["low"], q["close"]) if None not in (h, l, c)]
def corr(x, y):
    mx, my = st.mean(x), st.mean(y); n = len(x)
    r = sum((a - mx) * (b - my) for a, b in zip(x, y)) / math.sqrt(sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y))
    return r, r * math.sqrt((n - 2) / (1 - r * r)), n
CORTES = {}
_g = json.loads(urllib.request.urlopen(urllib.request.Request("https://query2.finance.yahoo.com/v8/finance/chart/%5EGVZ?range=5y&interval=1d", headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read())["chart"]["result"][0]
GVZ = dict(sorted((dt.date.fromtimestamp(t), c) for t, c in zip(_g["timestamp"], _g["indicators"]["quote"][0]["close"]) if c))
for nome, s in (("Ouro GC", "GC%3DF"), ("Iene 6J", "6J%3DF"), ("Euro 6E", "6E%3DF"), ("Franco 6S", "6S%3DF"), ("Libra 6B", "6B%3DF")):
    b = baixa(s, "730d", "1h"); dd = {}
    for t, h, l, c in b:
        d = (t + dt.timedelta(hours=6)).date()
        if d.weekday() > 4: continue
        x = dd.setdefault(d, {"cedo": [], "resto": [], "c": None})
        if t.hour >= 18 or t.hour < 9: x["cedo"].append((h, l))
        elif t.hour < 17: x["resto"].append((h, l))
        if t.hour < 17: x["c"] = c
    ds = [d for d in sorted(dd) if len(dd[d]["cedo"]) >= 12 and len(dd[d]["resto"]) >= 7]
    X, Y = [], []
    for i in range(22, len(ds)):
        r = [math.log(dd[ds[k]]["c"] / dd[ds[k - 1]]["c"]) for k in range(i - 21, i)]
        sd = st.stdev(r) * 1.09; a = dd[ds[i]]
        if nome == "Ouro GC":   # ouro: σ do painel = GVZ do fechamento anterior
            ant = [d for d in GVZ if d < ds[i]]
            if not ant: continue
            sd = GVZ[ant[-1]] / 100 / math.sqrt(252)
        ce = math.log(max(h for h, l in a["cedo"]) / min(l for h, l in a["cedo"])) / sd
        re = math.log(max(h for h, l in a["resto"]) / min(l for h, l in a["resto"])) / sd
        if 0 < ce < 8 and 0 < re < 8: X.append(math.log(ce)); Y.append(math.log(re))
    r, t, n = corr(X, Y); m = n // 2; r1, _, _ = corr(X[:m], Y[:m]); r2, _, _ = corr(X[m:], Y[m:])
    ter = sorted(X); lo, hi = ter[n // 3], ter[2 * n // 3]; med = sorted(Y)[n // 2]
    g_hi = sum(1 for a, b in zip(X, Y) if a >= hi and b >= med) / sum(1 for a in X if a >= hi)
    g_lo = sum(1 for a, b in zip(X, Y) if a < lo and b >= med) / sum(1 for a in X if a < lo)
    mh = sorted(b_ for a, b_ in zip(X, Y) if a >= hi); ml = sorted(b_ for a, b_ in zip(X, Y) if a < lo); mm = sorted(b_ for a, b_ in zip(X, Y) if lo <= a < hi)
    CORTES[nome] = [round(math.exp(lo), 2), round(math.exp(hi), 2), round(math.exp(ml[len(ml) // 2]), 2), round(math.exp(mm[len(mm) // 2]), 2), round(math.exp(mh[len(mh) // 2]), 2)]
    print(f"{nome}: n={n} r={r:.2f} t={t:.1f} metades r={r1:.2f}/{r2:.2f} | resto grande: cedo alto {g_hi:.0%} × cedo baixo {g_lo:.0%} (acaso 50%)")
print("cortes [terço baixo <, terço alto ≥, resto mediano se baixo, se médio, se alto] em σ:", CORTES)
