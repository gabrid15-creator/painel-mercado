import math, statistics as st
exec(open("faixa_bt.py").read().split("ATV = {")[0])
ATV = {"XAUUSD": ("GC=F", "^GVZ"), "USDJPY": ("JPY=X", None), "EURUSD": ("EURUSD=X", None), "USDCHF": ("CHF=X", None), "GBPUSD": ("GBPUSD=X", None)}
KS = [0.6, 0.8, 0.9, 1.0, 1.1, 1.2, 1.5, 2.0]
for a, (sym, ivx) in ATV.items():
    b = [x for x in diario(sym) if x[4] > 0]; b = [x for i, x in enumerate(b) if i == 0 or abs(math.log(x[4] / b[i - 1][4])) < 0.15]
    g = {d: c for d, o, h, l, c in diario(ivx)} if ivx else None
    dias = []
    for i in range(22, len(b)):
        c0 = b[i - 1][4]
        if g is not None:
            iv = g.get(b[i - 1][0])
            if not iv: continue
            sd = iv / 100 / math.sqrt(252)
        else: sd = st.stdev([math.log(b[j][4] / b[j - 1][4]) for j in range(i - 21, i)]) * 1.09
        if sd > 0: dias.append((math.log(b[i][2] / c0) / sd, math.log(b[i][3] / c0) / sd, math.log(b[i][4] / c0) / sd, b[i][0].year))
    print(f"\n{a} ({len(dias)} dias desde {dias[0][3]}): quando o preço PASSOU do nível durante o dia, quantas vezes FECHOU de volta dentro")
    for k in KS:
        ev = [(c <= k) for h, l, c, y in dias if h > k] + [(c >= -k) for h, l, c, y in dias if l < -k]
        n = len(ev); p = sum(ev) / n
        print(f"  {k:3}σ: passou em {n:5} lados · fechou de volta dentro {p*100:5.1f}%" + ("   ← 1σ" if k == 1.0 else ""))
    # fechou dentro do ±1σ sem condição
    print(f"  fechou dentro de ±1σ (todos os dias): {st.mean(abs(c) <= 1 for h, l, c, y in dias)*100:.1f}% · ±2σ: {st.mean(abs(c) <= 2 for h, l, c, y in dias)*100:.1f}%")
