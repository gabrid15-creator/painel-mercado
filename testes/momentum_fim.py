"""Baltussen et al. (JFE 2021) no ouro: o retorno do dia até perto do fim prevê o último trecho? (sem gamma: versão incondicional)
Futuro GC=F (Yahoo, só futuros). Dia = 18h NY da véspera → 17h NY. Janelas sem sobreposição, uma observação por dia.
Sinal: retorno 18h → 13h NY. Alvos: 13h → 14h (pregão do ajuste, 13h30) e 15h → 17h (fim do Globex). Placebo: sinal × alvo do dia seguinte.
Rodar: python3 testes/momentum_fim.py"""
import json, urllib.request, datetime as dt, math, statistics as st
from zoneinfo import ZoneInfo
NY = ZoneInfo("America/New_York")
def baixa(s, r, i):
    u = f"https://query2.finance.yahoo.com/v8/finance/chart/{s}?range={r}&interval={i}"
    j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read())["chart"]["result"][0]
    q = j["indicators"]["quote"][0]
    return [(dt.datetime.fromtimestamp(t, NY), o, c) for t, o, c in zip(j["timestamp"], q["open"], q["close"]) if o and c]
def preco_em(b, alvo, passo):   # FECHAMENTO da última barra que termina até `alvo` (nunca usa barra posterior)
    v = [c for t, o, c in b if t + dt.timedelta(seconds=passo) <= alvo]
    ult = [t for t, o, c in b if t + dt.timedelta(seconds=passo) <= alvo]
    return v[-1] if v and (alvo - ult[-1]).total_seconds() <= 2 * passo else None
def reg(x, y):
    n = len(x); mx, my = st.mean(x), st.mean(y); sxx = sum((a - mx) ** 2 for a in x)
    bt = sum((a - mx) * (c - my) for a, c in zip(x, y)) / sxx; res = [c - my - bt * (a - mx) for a, c in zip(x, y)]
    se = math.sqrt(sum(r * r for r in res) / (n - 2) / sxx); return bt, bt / se, n
def roda(b, passo, j1, j2, rot):
    dias = sorted({(t + dt.timedelta(hours=6)).date() for t, _, _ in b if (t + dt.timedelta(hours=6)).weekday() < 5})
    obs = []
    for d in dias:
        ini = dt.datetime.combine(d - dt.timedelta(days=1), dt.time(18), NY)
        ab = [o for t, o, c in b if ini <= t < ini + dt.timedelta(seconds=2 * passo)]   # abertura da sessão (18h NY)
        p = [ab[0] if ab else None, preco_em(b, dt.datetime.combine(d, j1[1], NY), passo)]
        p.insert(1, p[1])
        q = [preco_em(b, dt.datetime.combine(d, j2[0], NY), passo), preco_em(b, dt.datetime.combine(d, j2[1], NY), passo)]
        if None in p + q: continue
        obs.append((d, math.log(p[1] / p[0]), math.log(q[1] / q[0])))
    x = [o[1] for o in obs]; y = [o[2] for o in obs]
    bt, t, n = reg(x, y); h = n // 2
    _, t1, _ = reg(x[:h], y[:h]); _, t2, _ = reg(x[h:], y[h:]); _, tp, _ = reg(x[:-1], y[1:])
    ac = sum(1 for a, c in zip(x, y) if a * c > 0) / n
    print(f"{rot}: n={n} beta={bt:.4f} t={t:.2f} | metades t={t1:.2f}/{t2:.2f} | placebo (dia seguinte) t={tp:.2f} | mesmo sinal {ac:.1%}")
b1 = baixa("GC%3DF", "730d", "1h")
roda(b1, 3600, (dt.time(18), dt.time(13)), (dt.time(13), dt.time(14)), "1h 2 anos, 18h→13h prevê 13h→14h")
roda(b1, 3600, (dt.time(18), dt.time(15)), (dt.time(15), dt.time(17)), "1h 2 anos, 18h→15h prevê 15h→17h")
b5 = baixa("GC%3DF", "60d", "5m")
roda(b5, 300, (dt.time(18), dt.time(13)), (dt.time(13), dt.time(13, 30)), "5m 60 dias, 18h→13h prevê 13h→13h30")
roda(b5, 300, (dt.time(18), dt.time(16, 25)), (dt.time(16, 25), dt.time(16, 55)), "5m 60 dias, 18h→16h25 prevê últimos 30 min")
