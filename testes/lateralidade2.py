"""Lateralidade, parte 2: (a) dia da semana e semana do mês na SESSÃO REAL (18h→17h NY; 1 h, 2 anos), (b) persistência (ontem estreito/largo → hoje),
(c) o nível do GVZ no dia (ouro, 15 anos) × dia estreito: confere a frase "faixas estreitas, mercado parado" do painel.
Mesmas definições de testes/lateralidade.py (estreito = amplitude ≤ 0,70 × média dos 20 dias anteriores). Uso: python3 testes/lateralidade2.py"""
import json, math, statistics as st, datetime as dt, collections, sys
sys.argv = ["x", "/tmp/x.json"]
ns = {}; exec(open("testes/lateralidade.py").read().split("RES = {}")[0], ns)
y, qui2 = ns["y"], ns["qui2"]
from zoneinfo import ZoneInfo
NY = ZoneInfo("America/New_York")
def p2x2(a, n1, b, n2):   # z de duas proporções
    p = (a + b) / (n1 + n2); se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2)); z = (a / n1 - b / n2) / se
    return z, math.erfc(abs(z) / math.sqrt(2))
for ativo, sym in ns["ATV"].items():
    dias = collections.defaultdict(list)
    for t, o, h, l, c in y(sym, "730d", "1h"):
        d = dt.datetime.fromtimestamp(t, NY)
        if d.hour != 17: dias[(d + dt.timedelta(hours=6)).date()].append((h, l))
    ds = sorted(d for d in dias if len(dias[d]) >= 20 and d.weekday() < 5)
    A = {d: math.log(max(x[0] for x in dias[d]) / min(x[1] for x in dias[d])) for d in ds}
    rel = {ds[i]: A[ds[i]] / st.mean(A[x] for x in ds[i - 20:i]) for i in range(20, len(ds))}; days = sorted(rel); tot = len(days); taxa = sum(1 for d in days if rel[d] <= .7) / tot
    for nome, key in (("dia da semana", lambda d: ["seg", "ter", "qua", "qui", "sex"][d.weekday()]), ("semana do mês", lambda d: (d.day - 1) // 7 + 1)):
        g = collections.defaultdict(lambda: [0, 0])
        for d in days: k = key(d); g[k][1] += 1; g[k][0] += 1 if rel[d] <= .7 else 0
        x2, p = qui2({k: tuple(v) for k, v in g.items()}, taxa)
        print(f"{ativo} SESSÃO {nome}: estreito geral {taxa*100:.0f}%", {k: f"{v[0]/v[1]*100:.0f}% (n={v[1]})" for k, v in sorted(g.items())}, f"p={p:.3f}")
    # persistência (15 anos, diário): ontem estreito → hoje estreito
    b = [x for x in y(sym, "15y", "1d")]; Ad = [math.log(x[2] / x[3]) for x in b if x[2] > x[3]]
    rl = [Ad[i] / st.mean(Ad[i - 20:i]) for i in range(20, len(Ad))]
    e = [r <= .7 for r in rl]; w = [r >= 1.4 for r in rl]
    ae = sum(1 for i in range(1, len(e)) if e[i] and e[i - 1]); ne = sum(1 for i in range(1, len(e)) if e[i - 1])
    aw = sum(1 for i in range(1, len(e)) if e[i] and w[i - 1]); nw = sum(1 for i in range(1, len(e)) if w[i - 1]); an = sum(e) / len(e)
    z, p = p2x2(ae, ne, aw, nw)
    print(f"{ativo} PERSISTÊNCIA (15 anos): base {an*100:.0f}% | ontem estreito → hoje estreito {ae/ne*100:.0f}% (n={ne}) | ontem largo → {aw/nw*100:.0f}% (n={nw}) | z={z:.1f} p={p:.1e}")
# (c) GVZ × dia estreito
gv = {dt.datetime.fromtimestamp(t, dt.timezone.utc).date(): c for t, o, h, l, c in y("%5EGVZ", "15y", "1d")}
gcs = [(dt.datetime.fromtimestamp(t, dt.timezone.utc).date(), h, l) for t, o, h, l, c in y("GC%3DF", "15y", "1d") if h > l]
Ad = [math.log(h / l) for d, h, l in gcs]; gd = sorted(gv); niv = {}
for i in range(20, len(gcs)):
    d = gcs[i][0]; ant = [x for x in gd if x < d]
    if len(ant) < 260: continue
    g = gv[ant[-1]]; m1 = st.mean(gv[x] for x in ant[-252:]); q = g / m1   # razão do GVZ de ontem contra a média de 1 ano (versão simples do painel)
    r = Ad[i] / st.mean(Ad[i - 20:i]); niv[d] = (q, r, Ad[i] / (g / 100 / math.sqrt(252)))
bins = [("bem abaixo (≤ 0,80)", lambda q: q <= .8), ("abaixo (0,80–0,90)", lambda q: .8 < q <= .9), ("normal (0,90–1,10)", lambda q: .9 < q <= 1.1), ("acima (1,10–1,25)", lambda q: 1.1 < q <= 1.25), ("bem acima (> 1,25)", lambda q: q > 1.25)]
print("OURO: nível do GVZ (contra a média de 1 ano) × dia:")
for nm, f in bins:
    v = [(r, s_) for q, r, s_ in niv.values() if f(q)]
    if v: print(f"  {nm}: n={len(v)} | dia estreito {sum(1 for r, _ in v if r <= .7)/len(v)*100:.0f}% | largo {sum(1 for r, _ in v if r >= 1.4)/len(v)*100:.0f}% | amplitude mediana do dia {st.median(a for _, a in v):.2f}σ")
