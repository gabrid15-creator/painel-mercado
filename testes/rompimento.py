"""Rompimento do σ do dia (mesma régua do mapa: a partir da ABERTURA da sessão; ouro σ do GVZ, moedas vol. 21d × 1,09).
Futuros da CME (máx./mín. limpas). Para cada lado (cima/baixo), condicionado ao que já aconteceu (dá para usar ao vivo):
  tocou 1σ → fechou fora do 1σ? · passou de 1,25σ → fechou fora? chegou a 1,5σ? · passou de 1,5σ → chegou a 2σ? fechou fora?"""
import math, statistics as st, json, sys
exec(open("faixa_bt.py").read().split("ATV = {")[0])
ATV = {"XAUUSD": ("GC=F", "^GVZ", 1), "USDJPY": ("6J=F", None, -1), "EURUSD": ("6E=F", None, 1), "USDCHF": ("6S=F", None, -1), "GBPUSD": ("6B=F", None, 1)}
out = {}
for a, (sym, ivx, sinal) in ATV.items():
    b = [x for x in diario(sym) if x[4] > 0 and x[1] and x[1] > 0]; b = [x for i, x in enumerate(b) if i == 0 or abs(math.log(x[4] / b[i - 1][4])) < 0.15]
    g = {d: c for d, o, h, l, c in diario(ivx)} if ivx else None
    D = []
    for i in range(22, len(b)):
        d, o, h, l, c = b[i]
        if g is not None:
            iv = g.get(b[i - 1][0])
            if not iv: continue
            sd = iv / 100 / math.sqrt(252)
        else: sd = st.stdev([math.log(b[j][4] / b[j - 1][4]) for j in range(i - 21, i)]) * 1.09
        if sd <= 0 or abs(math.log(o / b[i - 1][4])) > 3 * sd: continue   # abertura com buraco grande (dado ruim): fora
        up, dn, fe = math.log(h / o) / sd, -math.log(l / o) / sd, math.log(c / o) / sd
        if sinal < 0: up, dn, fe = dn, up, -fe   # 6J e 6S são o inverso de USDJPY e USDCHF
        D.append((d.year, up, dn, fe))
    lados = [(y, e, f) for y, u, dn_, f in D for e, f in ((u, f),)] + [(y, dn_, -f) for y, u, dn_, f in D]
    def taxa(cond, res):
        x = [(e, f) for y, e, f in lados if cond(e)]; return round(sum(res(e, f) for e, f in x) / len(x) * 100, 1) if x else None, len(x)
    r = {"desde": D[0][0], "dias": len(D),
         "fecha_dentro_1s": round(st.mean(abs(f) <= 1 for y, u, dn_, f in D) * 100, 1),
         "toca_1s": taxa(lambda e: True, lambda e, f: e >= 1),
         "tocou_1s_fecha_fora": taxa(lambda e: e >= 1, lambda e, f: f > 1),
         "passou_125_fecha_fora": taxa(lambda e: e >= 1.25, lambda e, f: f > 1),
         "passou_125_chega_15": taxa(lambda e: e >= 1.25, lambda e, f: e >= 1.5),
         "passou_15_chega_2": taxa(lambda e: e >= 1.5, lambda e, f: e >= 2),
         "passou_15_fecha_fora": taxa(lambda e: e >= 1.5, lambda e, f: f > 1)}
    # estabilidade: mesma conta só desde 2016
    l2 = [(y, e, f) for y, e, f in lados if y >= 2016]
    x = [(e, f) for y, e, f in l2 if e >= 1.25]; r["passou_125_fecha_fora_2016"] = round(sum(f > 1 for e, f in x) / len(x) * 100, 1)
    out[a] = r
    print(a, json.dumps(r, ensure_ascii=False))
json.dump(out, open("rompimento.json", "w"), ensure_ascii=False)
