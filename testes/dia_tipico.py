"""Quanto o dia anda de verdade, em σ do painel (vol. realizada 21 d × 1,09; ouro também assim, para comparar). Futuros CME diários
(Yahoo, só futuros: máx./mín. do Yahoo FX têm picos falsos). Sem olhar o futuro: σ do dia usa só os 21 retornos anteriores.
Mede: |fechamento − abertura| em σ (quantis 50/68/80/90/95%) e amplitude (máx − mín) em σ (quantis 50/80%). Metades do período.
Rodar: python3 testes/dia_tipico.py"""
import json, urllib.request, math, statistics as st
def baixa(s):
    u = f"https://query2.finance.yahoo.com/v8/finance/chart/{s}?range=15y&interval=1d"
    j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read())["chart"]["result"][0]
    q = j["indicators"]["quote"][0]
    return [(o, h, l, c) for o, h, l, c in zip(q["open"], q["high"], q["low"], q["close"]) if None not in (o, h, l, c) and h >= max(o, c) and l <= min(o, c) and l > 0]
def qt(v, p): v = sorted(v); return v[min(len(v) - 1, int(p * len(v)))]
for nome, s in (("Iene 6J", "6J%3DF"), ("Euro 6E", "6E%3DF"), ("Franco 6S", "6S%3DF"), ("Libra 6B", "6B%3DF"), ("Ouro GC", "GC%3DF")):
    b = baixa(s); mv, rg = [], []
    for i in range(22, len(b)):
        r = [math.log(b[k][3] / b[k - 1][3]) for k in range(i - 21, i)]
        sd = st.stdev(r) * 1.09
        if sd <= 0: continue
        o, h, l, c = b[i]; mv.append(abs(math.log(c / o)) / sd); rg.append(math.log(h / l) / sd)
        if rg[-1] > 8: mv.pop(); rg.pop()   # dado podre
    m = len(mv) // 2
    print(f"{nome}: n={len(mv)} | |fech−abert| em σ: 50%≤{qt(mv,.5):.2f} 68%≤{qt(mv,.68):.2f} 80%≤{qt(mv,.8):.2f} 90%≤{qt(mv,.9):.2f} 95%≤{qt(mv,.95):.2f}"
          f" | dentro de ±1σ {sum(x<=1 for x in mv)/len(mv):.0%} | amplitude 50%≤{qt(rg,.5):.2f} 80%≤{qt(rg,.8):.2f}"
          f" | metades 50%: {qt(mv[:m],.5):.2f}/{qt(mv[m:],.5):.2f}")

# Ouro com o σ do PAINEL (GVZ do fechamento anterior ÷ √252), casado por data
import datetime as dt
def baixa_d(s):
    u = f"https://query2.finance.yahoo.com/v8/finance/chart/{s}?range=15y&interval=1d"
    j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read())["chart"]["result"][0]
    q = j["indicators"]["quote"][0]
    return {dt.date.fromtimestamp(t): (o, h, l, c) for t, o, h, l, c in zip(j["timestamp"], q["open"], q["high"], q["low"], q["close"]) if None not in (o, h, l, c)}
g, v = baixa_d("GC%3DF"), baixa_d("%5EGVZ"); ds = sorted(g); mv, rg = [], []
for i in range(1, len(ds)):
    ant = max((d for d in v if d < ds[i]), default=None) if ds[i - 1] not in v else ds[i - 1]
    if ant is None or (ds[i] - ant).days > 5: continue
    sd = v[ant][3] / 100 / math.sqrt(252); o, h, l, c = g[ds[i]]
    if not (h >= max(o, c) and l <= min(o, c) and l > 0): continue
    x, y = abs(math.log(c / o)) / sd, math.log(h / l) / sd
    if y > 8: continue
    mv.append(x); rg.append(y)
m = len(mv) // 2
print(f"Ouro GC, σ GVZ: n={len(mv)} | |fech−abert| em σ: 50%≤{qt(mv,.5):.2f} 68%≤{qt(mv,.68):.2f} 80%≤{qt(mv,.8):.2f} 90%≤{qt(mv,.9):.2f} 95%≤{qt(mv,.95):.2f}"
      f" | dentro de ±1σ {sum(x<=1 for x in mv)/len(mv):.0%} | amplitude 50%≤{qt(rg,.5):.2f} 80%≤{qt(rg,.8):.2f} | metades 50%: {qt(mv[:m],.5):.2f}/{qt(mv[m:],.5):.2f}")
