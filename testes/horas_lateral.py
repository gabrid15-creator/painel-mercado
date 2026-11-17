"""Em que horário (Brasília) o ouro anda de lado? GC=F (futuro da CME, Yahoo). Sem olhar o futuro; metades para estabilidade.
1) Por hora (1 h, 2 anos): amplitude da hora em σ do dia (σ = GVZ do fechamento anterior ÷ √252) — quanto anda.
2) Por hora (5 min, 60 dias): eficiência dentro da hora = |fech − abert| ÷ caminho percorrido (≤ 0,25 = vai e volta).
3) Por bloco (1 h, 2 anos): Ásia, Londres, NY manhã, NY tarde, fim — amplitude em σ e eficiência do bloco.
Rodar: python3 testes/horas_lateral.py"""
import json, urllib.request, datetime as dt, math, statistics as st
from zoneinfo import ZoneInfo
BR = ZoneInfo("America/Sao_Paulo")
def baixa(s, r, i):
    u = f"https://query2.finance.yahoo.com/v8/finance/chart/{s}?range={r}&interval={i}"
    j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read())["chart"]["result"][0]
    q = j["indicators"]["quote"][0]
    return [(dt.datetime.fromtimestamp(t, BR), o, h, l, c) for t, o, h, l, c in zip(j["timestamp"], q["open"], q["high"], q["low"], q["close"]) if None not in (o, h, l, c)]
g = baixa("%5EGVZ", "5y", "1d"); GVZ = sorted((t.date(), c) for t, o, h, l, c in g)
def sd(d):
    v = [c for x, c in GVZ if x < d]; return v[-1] / 100 / math.sqrt(252) if v else None
b1 = baixa("GC%3DF", "730d", "1h")
por_h = {}
for t, o, h, l, c in b1:
    s = sd(t.date())
    if s and t.weekday() < 5 or (t.weekday() == 6 and t.hour >= 19):
        if s: por_h.setdefault(t.hour, []).append((t, math.log(h / l) / s))
b5 = baixa("GC%3DF", "60d", "5m"); ef = {}
grp = {}
for t, o, h, l, c in b5: grp.setdefault((t.date(), t.hour), []).append((o, c))
for (d, hh), v in grp.items():
    if len(v) < 10: continue
    cam = sum(abs(v[i][1] - (v[i - 1][1] if i else v[0][0])) for i in range(len(v)))
    if cam: ef.setdefault(hh, []).append(abs(v[-1][1] - v[0][0]) / cam)
print("HORA (BRT) | amplitude média em σ do dia (2 anos) [metades] | eficiência mediana na hora (60 dias) | % horas vai-e-volta (ef ≤ 0,25)")
for hh in sorted(por_h):
    x = [a for _, a in por_h[hh]]
    if len(x) < 100: continue
    m = len(x) // 2; e = ef.get(hh, [])
    print(f"{hh:02d}h | {st.mean(x):.3f} [{st.mean(x[:m]):.3f}/{st.mean(x[m:]):.3f}] n={len(x)} | " + (f"{st.median(e):.2f} | {sum(1 for y in e if y <= .25) / len(e):.0%} (n={len(e)})" if len(e) >= 20 else "—"))
# blocos
BL = {"Ásia 20h–04h": (20, 4), "Londres 05h–10h": (5, 10), "NY manhã 11h–14h": (11, 14), "NY tarde 15h–18h": (15, 18)}
print("\nBLOCO | amplitude em σ (mediana) [metades] | eficiência mediana [metades] | % ping-pong (ef ≤ 0,12) | % tendência (ef ≥ 0,30)")
for nome, (a, z) in BL.items():
    dias = {}
    for t, o, h, l, c in b1:
        hh = t.hour; dentro = (a <= hh or hh <= z) if a > z else (a <= hh <= z)
        if not dentro: continue
        k = (t + dt.timedelta(hours=4)).date() if a > z else t.date()
        dias.setdefault(k, []).append((t, o, h, l, c))
    A, E = [], []
    for k in sorted(dias):
        v = sorted(dias[k]); s = sd(k)
        if len(v) < (z - a) % 24 or not s: continue
        o = v[0][1]; cl = [x[4] for x in v]; cam = abs(cl[0] - o) + sum(abs(cl[i] - cl[i - 1]) for i in range(1, len(cl)))
        A.append(math.log(max(x[2] for x in v) / min(x[3] for x in v)) / s); E.append(abs(cl[-1] - o) / cam if cam else 0)
    m = len(A) // 2
    print(f"{nome} | {st.median(A):.2f} [{st.median(A[:m]):.2f}/{st.median(A[m:]):.2f}] | {st.median(E):.2f} [{st.median(E[:m]):.2f}/{st.median(E[m:]):.2f}] | {sum(1 for y in E if y <= .12) / len(E):.0%} | {sum(1 for y in E if y >= .30) / len(E):.0%} | n={len(A)}")
