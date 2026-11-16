import math, statistics as st
exec(open("faixa_bt.py").read().split("ATV = {")[0])
ATV = {"6J (iene, futuro)": ("6J=F", None), "6E (euro, futuro)": ("6E=F", None), "6S (franco, futuro)": ("6S=F", None), "6B (libra, futuro)": ("6B=F", None), "GC (ouro, futuro)": ("GC=F", None)}
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
    meio = dias[len(dias) // 2][3]; ult = [x for x in dias if x[3] >= 2021]
    for k in (1.0, 1.5, 2.0):
        def taxa(dd):
            ev = [(c <= k) for h, l, c, y in dd if h > k] + [(c >= -k) for h, l, c, y in dd if l < -k]; return sum(ev) / len(ev) * 100, len(ev)
        a1, n1 = taxa([x for x in dias if x[3] < meio]); a2, n2 = taxa([x for x in dias if x[3] >= meio]); a3, n3 = taxa(ult)
        tt = (taxa(dias)[0] / 100 - 0.5) / math.sqrt(0.25 / taxa(dias)[1])
        print(f"  {k}σ: 1ª metade (até {meio}) {a1:.1f}% (n={n1}) · 2ª metade {a2:.1f}% (n={n2}) · desde 2021 {a3:.1f}% (n={n3}) · t vs 50% = {tt:.1f}")
    # fechou dentro do ±1σ sem condição
    print(f"  fechou dentro de ±1σ (todos os dias): {st.mean(abs(c) <= 1 for h, l, c, y in dias)*100:.1f}% · ±2σ: {st.mean(abs(c) <= 2 for h, l, c, y in dias)*100:.1f}%")
