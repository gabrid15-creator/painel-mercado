"""Regras de bolso de trader, testadas nos futuros (Yahoo 1 h, 2 anos; diário 15 anos). Dia = 18h NY → 17h NY. Uma observação por dia.
Teste = correlação sinal × alvo (t), metades, e % de acerto do lado. ~35 testes → corte |t| ≥ 3 e metades com o mesmo sinal.
H1 1ª hora NY (9h→10h) prevê o resto (10h→17h).        H2 noite (18h→9h) prevê NY (9h→17h).
H3 Londres rompeu a máx./mín. da Ásia (18h→2h) → NY segue o rompimento?   H4 Varreu a máx./mín. de ontem até 9h e voltou para dentro → NY vai contra?
H5 Dia estreito (amplitude < 0,6× média 10 d) → amanhã é tendência (eficiência ≥ 0,30)?   H6 Fechou perto da máxima (CLV) → amanhã sobe? (diário 15 anos)
H7 Gap do domingo (18h dom × 17h sex) → segunda vai contra?
Rodar: python3 testes/regras_trader.py"""
import json, urllib.request, datetime as dt, math, statistics as st
from zoneinfo import ZoneInfo
NY = ZoneInfo("America/New_York")
def baixa(s, r, i):
    u = f"https://query2.finance.yahoo.com/v8/finance/chart/{s}?range={r}&interval={i}"
    j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read())["chart"]["result"][0]
    q = j["indicators"]["quote"][0]
    return [(dt.datetime.fromtimestamp(t, NY), o, h, l, c) for t, o, h, l, c in zip(j["timestamp"], q["open"], q["high"], q["low"], q["close"]) if None not in (o, h, l, c)]
def tc(x, y):
    n = len(x)
    if n < 30: return 0, 0, 0, 0, n
    mx, my = st.mean(x), st.mean(y); sx = math.sqrt(sum((a - mx) ** 2 for a in x)); sy = math.sqrt(sum((b - my) ** 2 for b in y))
    if not sx or not sy: return 0, 0, 0, 0, n
    r = sum((a - mx) * (b - my) for a, b in zip(x, y)) / sx / sy; t = r * math.sqrt((n - 2) / max(1e-9, 1 - r * r))
    h = n // 2; r1 = tc(x[:h], y[:h])[0] if h >= 30 else 0; r2 = tc(x[h:], y[h:])[0] if n - h >= 30 else 0
    return r, t, r1, r2, n
RES = []
def rep(nome, h, x, y):
    r, t, r1, r2, n = tc(x, y); ac = sum(1 for a, b in zip(x, y) if a * b > 0) / max(1, sum(1 for a, b in zip(x, y) if a * b != 0))
    ok = abs(t) >= 3 and r1 * r2 > 0
    RES.append((nome, h, n, t, r1, r2, ac, ok)); print(f"{'✅' if ok else '  '} {h} {nome}: n={n} t={t:+.1f} metades r={r1:+.2f}/{r2:+.2f} mesmo lado {ac:.0%}")
sg = lambda v: (v > 0) - (v < 0)
for nome, s in (("Ouro", "GC%3DF"), ("Iene", "6J%3DF"), ("Euro", "6E%3DF"), ("Franco", "6S%3DF"), ("Libra", "6B%3DF")):
    b = baixa(s, "730d", "1h"); dd = {}
    for t, o, h, l, c in b:
        d = (t + dt.timedelta(hours=6)).date()
        if d.weekday() < 5 and t.hour != 17: dd.setdefault(d, []).append((t, o, h, l, c))
    ds = [d for d in sorted(dd) if len(dd[d]) >= 20]
    def px(d, hh):   # fechamento da barra que termina às hh (barra que começa hh−1)
        v = [c for t, o, h, l, c in dd[d] if t.hour == (hh - 1) % 24]; return v[0] if v else None
    def faixa(d, f): v = [(h, l) for t, o, h, l, c in dd[d] if f(t)]; return (max(a for a, _ in v), min(z for _, z in v)) if v else None
    X = {k: ([], []) for k in ("H1", "H2", "H3", "H4", "H5", "H7")}
    for i, d in enumerate(ds):
        o = dd[d][0][1]; p9, p10, p17 = px(d, 9), px(d, 10), dd[d][-1][4]
        if None in (p9, p10): continue
        X["H1"][0].append(math.log(p10 / p9)); X["H1"][1].append(math.log(p17 / p10))
        X["H2"][0].append(math.log(p9 / o)); X["H2"][1].append(math.log(p17 / p9))
        asia = faixa(d, lambda t: t.hour >= 18 or t.hour < 2); lon = faixa(d, lambda t: 2 <= t.hour < 9)
        if asia and lon:
            sgn = (lon[0] > asia[0]) - (lon[1] < asia[1])
            if sgn: X["H3"][0].append(sgn); X["H3"][1].append(math.log(p17 / p9))
        if i and ds[i - 1] == d - dt.timedelta(days=1 if d.weekday() else 3):
            ont = dd[ds[i - 1]]; H0, L0 = max(x[2] for x in ont), min(x[3] for x in ont); cedo = faixa(d, lambda t: t.hour >= 18 or t.hour < 9)
            if cedo and L0 < p9 < H0:
                sw = (cedo[0] > H0) - (cedo[1] < L0)
                if sw: X["H4"][0].append(-sw); X["H4"][1].append(math.log(p17 / p9))
            if d.weekday() == 0: X["H7"][0].append(-math.log(o / ont[-1][4])); X["H7"][1].append(math.log(p17 / o))
        if i >= 11:
            amp = lambda dx: max(x[2] for x in dd[dx]) - min(x[3] for x in dd[dx])
            m10 = st.mean(amp(ds[k]) for k in range(i - 11, i - 1)); estreito = amp(ds[i - 1]) < 0.6 * m10
            cl = [x[4] for x in dd[d]]; perc = abs(cl[0] - o) + sum(abs(cl[k] - cl[k - 1]) for k in range(1, len(cl))); ef = abs(cl[-1] - o) / perc if perc else 0
            X["H5"][0].append(1 if estreito else 0); X["H5"][1].append(1 if ef >= 0.30 else 0)
    for h in ("H1", "H2", "H3", "H4", "H7"): rep(nome, h, *X[h])
    x5, y5 = X["H5"]; n1 = sum(x5); p1 = sum(b for a, b in zip(x5, y5) if a) / max(1, n1); p0 = sum(b for a, b in zip(x5, y5) if not a) / max(1, len(x5) - n1)
    r, t, r1, r2, n = tc(x5, y5); print(f"{'✅' if abs(t) >= 3 and r1 * r2 > 0 else '  '} H5 {nome}: tendência após dia estreito {p1:.0%} (n={n1}) × outros {p0:.0%}, t={t:+.1f}")
    RES.append((nome, "H5", n, t, r1, r2, p1, abs(t) >= 3 and r1 * r2 > 0))
    dv = baixa(s, "15y", "1d"); x6, y6 = [], []
    for k in range(1, len(dv) - 1):
        _, o, h, l, c = dv[k]
        if h > l: x6.append((c - l) / (h - l) - 0.5); y6.append(math.log(dv[k + 1][4] / c))
    rep(nome, "H6", x6, y6)
print("\nPASSOU:", [(a, b, round(t, 1)) for a, b, n, t, r1, r2, ac, ok in RES if ok] or "nada")
