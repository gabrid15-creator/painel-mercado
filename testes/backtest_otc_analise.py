import json, math, statistics as st, collections
import os
obs = json.load(open(os.environ.get("SAIDA", "bt2.json"))); PARES = ["USDJPY", "EURUSD", "USDCHF", "GBPUSD"]
def t_(d):
    return st.mean(d) / (st.stdev(d) / math.sqrt(len(d))) if len(d) > 2 and st.stdev(d) > 0 else 0
def linha(nome, ys, ps, extra=""):
    d = [y - p for y, p in zip(ys, ps)]
    if not d: print(f"  {nome}: sem dados"); return
    t = t_(d); mark = " ← PASSA" if abs(t) >= 2.5 else ""
    print(f"  {nome}: real {st.mean(ys)*100:5.1f}% · acaso {st.mean(ps)*100:5.1f}% · dif {st.mean(d)*100:+5.1f} p.p. · t={t:5.2f} · n={len(d)}{extra}{mark}")
def metades(ys, ps):
    n = len(ys) // 2; return [st.mean([y - p for y, p in zip(ys[:n], ps[:n])]) * 100, st.mean([y - p for y, p in zip(ys[n:], ps[n:])]) * 100] if n > 5 else None
por_par = collections.defaultdict(list)
for o in obs: por_par[o["par"]].append(o)
print(f"Amostra: {len(obs)} (par × dia), {len({o['dia'] for o in obs})} dias, {obs[0]['dia']} → {obs[-1]['dia']}\n")
print("A) ATRAÇÃO (7h → corte 10h NY): andou em direção ao strike com mais dinheiro vencendo?")
for lim in (100, 500, 1000):
    x = [o for o in obs if o["k"] and o["mi_k"] >= lim and o["rumo_base"] is not None]
    linha(f"strike ≥ US$ {lim} mi", [int(o["rumo"]) for o in x], [o["rumo_base"] for o in x])
for par in PARES:
    x = [o for o in obs if o["par"] == par and o["k"] and o["mi_k"] >= 100 and o["rumo_base"] is not None]
    linha(f"   {par}", [int(o["rumo"]) for o in x], [o["rumo_base"] for o in x])
def base(o, f):   # acaso: mesma régua aplicada aos outros dias do mesmo par
    return st.mean(f(q) for q in por_par[o["par"]] if q["dia"] != o["dia"])
print("\nB) RANGE DO DIA (0h–17h NY, a partir do fechamento 17h):")
x = [o for o in obs if o["a"] and o["b"]]
ys = [int(o["hi"] < o["b"] and o["lo"] > -o["a"]) for o in x]; ps = [base(o, lambda q, o=o: int(q["hi"] < o["b"] and q["lo"] > -o["a"])) for o in x]
linha("range inteiro dentro de piso–teto", ys, ps, f" · metades {metades(ys, ps)}")
for lado, lv, ex in (("teto", "b", "hi"), ("piso", "a", "lo")):
    y2, p2 = [], []
    for o in x:
        nivel = o[lv] if lado == "teto" else -o[lv]; perto = lambda e: abs(e - nivel) <= o["passo"]
        y2.append(int(perto(o[ex]))); p2.append(base(o, lambda q: int(perto(q[ex]))))
    linha(f"extremo do dia parou a ≤ 1 degrau do {lado}", y2, p2, f" · metades {metades(y2, p2)}")
print("\nC) σ DO DIA (vol. 21d × 1,09):")
dentro = [int(o["hi"] < o["sg"] and o["lo"] > -o["sg"]) for o in obs]
print(f"  range inteiro dentro de ±1σ: {st.mean(dentro)*100:.1f}% (n={len(obs)}) · tocou +1σ {st.mean(int(o['hi'] >= o['sg']) for o in obs)*100:.1f}% · tocou −1σ {st.mean(int(o['lo'] <= -o['sg']) for o in obs)*100:.1f}%")
y3, p3 = [], []
for o in obs:
    for s, ex in ((1, "hi"), (-1, "lo")):
        nivel = s * o["sg"]; perto = lambda e: abs(e - nivel) <= 0.1 * o["sg"]
        y3.append(int(perto(o[ex]))); p3.append(base(o, lambda q: int(abs(q[ex] - s * q["sg"]) <= 0.1 * q["sg"]) if False else int(perto(q[ex]))))
linha("extremo do dia parou a ≤ 0,1σ do ±1σ", y3, p3)
# paredes medidas em σ: extremo parou a ≤ 0,1σ da parede, vs mesmo nível em outros dias
y4, p4, y5, p5 = [], [], [], []
for o in x:
    for lado, lv, ex, s in (("teto", "b", "hi", 1), ("piso", "a", "lo", -1)):
        nivel = s * o[lv]; perto = lambda e: abs(e - nivel) <= 0.1 * o["sg"]
        yy, pp = int(perto(o[ex])), base(o, lambda q: int(perto(q[ex])))
        y4.append(yy); p4.append(pp)
        if abs(o[lv] - o["sg"]) <= 0.25 * o["sg"]: y5.append(yy); p5.append(pp)
linha("extremo parou a ≤ 0,1σ da PAREDE", y4, p4)
linha("CONFLUÊNCIA (parede a ≤ 0,25σ do ±1σ): parou ali", y5, p5)
