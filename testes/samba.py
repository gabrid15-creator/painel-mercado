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
    print(f"\n{a} — {len(D)} dias. Passou do nível só um pouco e FECHOU DE VOLTA DENTRO:")
    for dl in (0.1, 0.25):
        lin = []
        for k in (0.8, 1.0, 1.2):
            ev = [c <= k for h, l, c in D if k < h <= k + dl] + [c >= -k for h, l, c in D if k < l <= k + dl]
            lin.append(f"{k}σ: {sum(ev)/len(ev)*100:4.0f}% (n={len(ev)})")
        print(f"  passou até {dl}σ além →  " + "   ".join(lin))
