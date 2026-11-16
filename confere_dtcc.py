#!/usr/bin/env python3
"""Auditoria independente do dtcc.py: confere o TIPO (call/put) e o TAMANHO de cada negócio pelo prêmio pago.
Para cada opção de até 60 dias: valor teórico (Black-Scholes, vol. realizada 21d × 1,1, preço da hora do negócio)
de uma call e de uma put; o tipo atribuído tem de ser o que fica mais perto do prêmio real (só conta quando a
diferença é decisiva). Uso: python3 confere_dtcc.py <dtcc_estado.json>   (o arquivo fica na branch "dados")
Resultado 16/11/2026: iene 97,2% · euro 98,9% · franco 100% · libra 98,3%; prêmio real ÷ teórico 0,92–1,19."""
import json, math, statistics as st, datetime as dt, sys, urllib.request, urllib.parse, time, bisect
from zoneinfo import ZoneInfo
def _y(sym, extra):
    u = f"https://query2.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?{extra}"
    j = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60))["chart"]["result"][0]; q = j["indicators"]["quote"][0]
    return [(t, o, h, l, c) for t, o, h, l, c in zip(j["timestamp"], q["open"], q["high"], q["low"], q["close"]) if None not in (o, h, l, c)]
NY = ZoneInfo("America/New_York")
def diario(sym): return [(dt.datetime.fromtimestamp(t, NY).date(), o, h, l, c) for t, o, h, l, c in _y(sym, f"period1={int(time.time()) - 400 * 86400}&period2={int(time.time())}&interval=1d")]
def chart(sym, iv, rg): return _y(sym, f"range={rg}&interval={iv}")
N = st.NormalDist(); NY = ZoneInfo("America/New_York")
e = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "dtcc_estado.json"))["neg"]
YH = {"USDJPY": "JPY=X", "EURUSD": "EURUSD=X", "USDCHF": "CHF=X", "GBPUSD": "GBPUSD=X"}
for par, sym in YH.items():
    px = {d: c for d, o, h, l, c in diario(sym)}
    hb = sorted((t, c) for t, o, h, l, c in chart(sym, "1h", "730d")); ts_ = [t for t, c in hb]
    dias = sorted(px)
    rv = {}
    for i in range(21, len(dias)):
        r = [math.log(px[dias[j]] / px[dias[j - 1]]) for j in range(i - 20, i + 1)]; rv[dias[i]] = st.stdev(r) * math.sqrt(252)
    base, quote = par[:3], par[3:]
    ok = ruim = amb = 0; razoes = []
    for v in e.values():
        if v["p"] != par or not v.get("pr") or v.get("c"): continue
        d0 = dt.date.fromisoformat(v["ts"][:10]); T = (dt.date.fromisoformat(v["v"]) - d0).days / 365
        ant = [d for d in dias if d <= d0]
        if not ant or T <= 0 or T > 60 / 365: continue
        te = dt.datetime.fromisoformat(v["ts"] + ":00+00:00").timestamp(); i_ = bisect.bisect_right(ts_, te) - 1
        if i_ < 0 or te - ts_[i_] > 7200: continue
        S = hb[i_][1]; sg = rv.get(ant[-1], 0.08) * 1.1; K = v["k"]
        d1 = (math.log(S / K) + sg * sg * T / 2) / (sg * math.sqrt(T)); d2 = d1 - sg * math.sqrt(T)
        C = S * N.cdf(d1) - K * N.cdf(d2); P = K * N.cdf(-d2) - S * N.cdf(-d1)   # em cotada por 1 unidade de base
        nb = v["n"] * 1e6 / (1 if base == "USD" else S)   # quantidade da moeda base
        pm = v.get("pm"); pr = v["pr"]
        if pm == quote: prem_q = pr
        elif pm == base: prem_q = pr * S
        else: continue
        real = prem_q / nb   # prêmio por unidade de base, em cotada
        tc, tp = C, P
        if min(tc, tp) <= 0: continue
        lc, lp = abs(math.log(real / tc)) if real > 0 else 9, abs(math.log(real / tp)) if real > 0 else 9
        if abs(lc - lp) < 1.5: amb += 1; continue   # perto do dinheiro: call e put valem parecido, não dá para decidir
        meu = v["t"]; melhor = "C" if lc < lp else "P"
        if meu == melhor: ok += 1; razoes.append(real / (tc if meu == "C" else tp))
        else: ruim += 1
    tot = ok + ruim
    print(f"{par}: tipo confirmado pelo prêmio em {ok}/{tot} = {ok / tot * 100:.1f}% (fora {amb} perto do dinheiro, indecidíveis)"
          + (f" · prêmio real ÷ teórico (mediana) {st.median(razoes):.2f}" if razoes else ""))
