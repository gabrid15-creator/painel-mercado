"""Gap do domingo fecha? Futuros diários 15 anos (barra de segunda abre no domingo 18h NY). x = −gap (abertura seg ÷ fech. sex), y = abertura→fech. da segunda.
Também: % de segundas em que o gap fecha (toca o fechamento de sexta). Rodar: python3 testes/gap_domingo.py"""
import json, urllib.request, datetime as dt, math, statistics as st
def baixa(s):
    u = f"https://query2.finance.yahoo.com/v8/finance/chart/{s}?range=15y&interval=1d"
    j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read())["chart"]["result"][0]
    q = j["indicators"]["quote"][0]
    return [(dt.date.fromtimestamp(t), o, h, l, c) for t, o, h, l, c in zip(j["timestamp"], q["open"], q["high"], q["low"], q["close"]) if None not in (o, h, l, c)]
for nome, s in (("Ouro", "GC%3DF"), ("Iene", "6J%3DF"), ("Euro", "6E%3DF"), ("Franco", "6S%3DF"), ("Libra", "6B%3DF")):
    b = baixa(s); x, y, fecha, base = [], [], 0, 0
    for k in range(1, len(b)):
        d, o, h, l, c = b[k]; c0 = b[k - 1][4]
        if d.weekday() != 0 or b[k - 1][0].weekday() != 4: continue
        g = math.log(o / c0)
        if abs(g) > 0.03 or g == 0: continue   # rolagem de contrato / dado podre
        x.append(-g); y.append(math.log(c / o)); base += 1; fecha += (l <= c0 <= h)
    n = len(x); mx, my = st.mean(x), st.mean(y)
    r = sum((a - mx) * (bb - my) for a, bb in zip(x, y)) / math.sqrt(sum((a - mx) ** 2 for a in x) * sum((bb - my) ** 2 for bb in y)); t = r * math.sqrt((n - 2) / (1 - r * r))
    hh = n // 2; f = lambda X, Y: sum((a - st.mean(X)) * (bb - st.mean(Y)) for a, bb in zip(X, Y)) / math.sqrt(sum((a - st.mean(X)) ** 2 for a in X) * sum((bb - st.mean(Y)) ** 2 for bb in Y))
    ac = sum(1 for a, bb in zip(x, y) if a * bb > 0) / n
    print(f"{nome}: n={n} t={t:+.1f} metades r={f(x[:hh], y[:hh]):+.2f}/{f(x[hh:], y[hh:]):+.2f} | segunda vai contra o gap {ac:.0%} | gap fecha no dia {fecha / base:.0%}")
