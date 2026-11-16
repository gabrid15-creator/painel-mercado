import math, statistics as st
exec(open("faixa_bt.py").read().split("ATV = {")[0])
ATV = {"Ouro (GC, σ do GVZ)": ("GC=F", "^GVZ"), "Iene (6J)": ("6J=F", None), "Euro (6E)": ("6E=F", None), "Franco (6S)": ("6S=F", None), "Libra (6B)": ("6B=F", None)}
for a, (sym, ivx) in ATV.items():
    b = [x for x in diario(sym) if x[4] > 0]; b = [x for i, x in enumerate(b) if i == 0 or abs(math.log(x[4] / b[i - 1][4])) < 0.15]
    g = {d: c for d, o, h, l, c in diario(ivx)} if ivx else None
    D = []
    for i in range(22, len(b)):
        c0 = b[i - 1][4]
        if g is not None:
            iv = g.get(b[i - 1][0])
            if not iv: continue
            sd = iv / 100 / math.sqrt(252)
        else: sd = st.stdev([math.log(b[j][4] / b[j - 1][4]) for j in range(i - 21, i)]) * 1.09
        if sd > 0: D.append((math.log(b[i][2] / c0) / sd, -math.log(b[i][3] / c0) / sd, math.log(b[i][4] / c0) / sd))
    lados = [(h, c) for h, l, c in D if h > 1] + [(l, -c) for h, l, c in D if l > 1]
    n = len(lados); seguiu = sum(e > 1.25 for e, c in lados) / n; dentro = sum(c <= 1 for e, c in lados) / n
    sam = [(e, c) for e, c in lados if e <= 1.25]; dsam = sum(c <= 1 for e, c in sam) / len(sam)
    seg = [(e, c) for e, c in lados if e > 1.25]; dseg = sum(c <= 1 for e, c in seg) / len(seg)
    print(f"{a}: passou do 1σ em {n} lados → só sambou (≤ 0,25σ além) {100-seguiu*100:.0f}% · seguiu (> 0,25σ além) {seguiu*100:.0f}% | fechou dentro: no total {dentro*100:.0f}% · quando só sambou {dsam*100:.0f}% · quando seguiu {dseg*100:.0f}%")
