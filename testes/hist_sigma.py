import math, statistics as st, collections
exec(open("faixa_bt.py").read().split("ATV = {")[0])
ATV = {"XAUUSD": ("GC=F", "^GVZ"), "USDJPY": ("JPY=X", None), "EURUSD": ("EURUSD=X", None), "USDCHF": ("CHF=X", None)}
for a, (sym, ivx) in ATV.items():
    b = [x for x in diario(sym) if x[4] > 0]; b = [x for i, x in enumerate(b) if i == 0 or abs(math.log(x[4] / b[i - 1][4])) < 0.15]
    g = {d: c for d, o, h, l, c in diario(ivx)} if ivx else None
    zs = []
    for i in range(22, len(b)):
        c0 = b[i - 1][4]
        if g is not None:
            iv = g.get(b[i - 1][0])
            if not iv: continue
            sd = iv / 100 / math.sqrt(252)
        else:
            r = [math.log(b[j][4] / b[j - 1][4]) for j in range(i - 21, i)]; sd = st.stdev(r) * 1.09
        if sd <= 0: continue
        h, l = math.log(b[i][2] / c0) / sd, -math.log(b[i][3] / c0) / sd
        if 0 <= h < 4: zs.append(h)
        if 0 <= l < 4: zs.append(l)
    cnt = collections.Counter(int(z / 0.1) for z in zs); n = len(zs)
    print(f"\n{a}: {n} extremos (máximas e mínimas do dia, em σ). Quantos pararam em cada faixa:")
    for k in range(5, 16):
        barra = "█" * int(cnt[k] / n * 600)
        print(f"  {k/10:.1f}–{(k+1)/10:.1f}σ {cnt[k]/n*100:5.2f}% {barra}{'  ← 1σ' if k == 9 else ''}")
    antes, depois = cnt[9] / n, cnt[10] / n; viz = (cnt[8] + cnt[11]) / 2 / n
    print(f"  logo antes do 1σ (0,9–1,0): {antes*100:.2f}% · logo depois (1,0–1,1): {depois*100:.2f}% · razão antes/depois {antes/depois:.2f} (sem efeito ≈ {cnt[8]/cnt[9]:.2f}–{cnt[10]/cnt[11]:.2f}, a queda natural de uma faixa para a próxima)")
