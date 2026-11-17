"""Refaz as métricas do mapa das MOEDAS com o σ das opções de balcão (DTCC) — o mesmo σ que o painel usa desde 17/11/2026.
Futuros da CME (Yahoo 1 h, 2 anos; 6J e 6S invertidos para USDJPY/USDCHF). σ do dia D = vol. DTCC do dia útil anterior ÷ √252.
Gera: chance de tocar ±k·σ a partir da abertura (dia e semana), fecha dentro, curva "chance agora" (z = dist ÷ (σ √fração restante))
e rompimento (tocou 1σ / passou 1,25σ / 1,5σ → fecha fora, chega a 1,5σ/2σ). Metades. Saída JSON (para docs/data).
Uso: python3 testes/metricas_dtcc.py <serie_iv.json> <saida.json>"""
import sys, json, math, urllib.request, datetime as dt, statistics as st
from zoneinfo import ZoneInfo
NY = ZoneInfo("America/New_York")
IV = json.load(open(sys.argv[1])); OUTF = sys.argv[2]
FUT = {"USDJPY": ("6J%3DF", -1), "EURUSD": ("6E%3DF", 1), "USDCHF": ("6S%3DF", -1), "GBPUSD": ("6B%3DF", 1)}
K = [0.25, 0.5, 0.75, 1, 1.25, 1.5]; ZB = [0.1, 0.25, 0.5, 0.75, 1, 1.25]
def baixa(s):
    u = f"https://query2.finance.yahoo.com/v8/finance/chart/{s}?range=730d&interval=1h"
    j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read())["chart"]["result"][0]
    q = j["indicators"]["quote"][0]
    return [(dt.datetime.fromtimestamp(t, NY), o, h, l, c) for t, o, h, l, c in zip(j["timestamp"], q["open"], q["high"], q["low"], q["close"]) if None not in (o, h, l, c)]
def sig(d):
    v = [x for x in IV_par if x < d.isoformat()]
    return IV_par[v[-1]] / math.sqrt(252) if v and (d - dt.date.fromisoformat(v[-1])).days <= 4 else None
pc = lambda x: round(100 * sum(x) / len(x)) if x else None
res = {}
for par, (sym, sn) in FUT.items():
    IV_par = dict(sorted(IV[par].items())); b = baixa(sym)
    # inverte 6J/6S: preço do par = 1/futuro (máx ↔ mín)
    b = [(t, o, h, l, c) if sn > 0 else (t, 1 / o, 1 / l, 1 / h, 1 / c) for t, o, h, l, c in b]
    dias = {}
    for x in b:
        d = (x[0] + dt.timedelta(hours=6)).date()
        if d.weekday() < 5 and x[0].hour != 17: dias.setdefault(d, []).append(x)
    D = []; agora = {z: [] for z in ZB}; sem = {}
    for d in sorted(dias):
        v = dias[d]; s = sig(d)
        if not s or len(v) < 18: continue
        o = v[0][1]; c = v[-1][4]; up = max(x[2] for x in v); dn = min(x[3] for x in v)
        eu, ed, fe = math.log(up / o) / s, -math.log(dn / o) / s, math.log(c / o) / s
        D.append((eu, ed, fe)); sem.setdefault(d.isocalendar()[:2], []).append((d, v, s))
        # curva "agora": a cada hora, níveis ±0,5/1/1,5σ ainda não tocados → toca até o fim do dia?
        for i in range(1, len(v) - 1):
            P = v[i][4]; mx = max(x[2] for x in v[:i + 1]); mn = min(x[3] for x in v[:i + 1]); fr = (len(v) - 1 - i) / len(v)
            fmx = max(x[2] for x in v[i + 1:]); fmn = min(x[3] for x in v[i + 1:])
            for k in (0.5, 1, 1.5):
                for sg in (1, -1):
                    L = o * math.exp(sg * k * s)
                    if (sg > 0 and mx >= L) or (sg < 0 and mn <= L): continue
                    z = abs(math.log(L / P)) / (s * math.sqrt(fr))
                    zb = min(ZB, key=lambda q: abs(q - z))
                    if abs(zb - z) <= 0.13: agora[zb].append((fmx >= L) if sg > 0 else (fmn <= L))
    S = []
    for w, lst in sem.items():
        if len(lst) < 4: continue
        d0, v0, s0 = lst[0]; sw = s0 * math.sqrt(5); o = v0[0][1]; c = lst[-1][1][-1][4]
        up = max(x[2] for _, v, _ in lst for x in v); dn = min(x[3] for _, v, _ in lst for x in v)
        S.append((math.log(up / o) / sw, -math.log(dn / o) / sw, math.log(c / o) / sw))
    lados = [(e, f) for eu, ed, f in D for e, f in ((eu, f), (ed, -f))]
    tx = lambda cond, r: [round(pc([r(e, f) for e, f in lados if cond(e)]) or 0, 1), sum(1 for e, f in lados if cond(e))]
    h = len(D) // 2
    res[par] = {"toque": {"n_dias": len(D), "n_semanas": len(S), "k": K,
                "dia_toca_cima": [pc([x[0] >= k for x in D]) for k in K], "dia_toca_baixo": [pc([x[1] >= k for x in D]) for k in K],
                "dia_fecha_dentro": [pc([abs(x[2]) <= k for x in D]) for k in K],
                "sem_toca_cima": [pc([x[0] >= k for x in S]) for k in K], "sem_toca_baixo": [pc([x[1] >= k for x in S]) for k in K],
                "sem_fecha_dentro": [pc([abs(x[2]) <= k for x in S]) for k in K],
                "agora_z": ZB, "agora_p": [pc(agora[z]) for z in ZB], "agora_n": [len(agora[z]) for z in ZB],
                "metades_toca1": [pc([x[0] >= 1 or x[1] >= 1 for x in D[:h]]), pc([x[0] >= 1 or x[1] >= 1 for x in D[h:]])]},
                "romp": {"desde": 2024, "dias": len(D), "fecha_dentro_1s": pc([abs(f) <= 1 for _, _, f in D]),
                "toca_1s": tx(lambda e: True, lambda e, f: e >= 1), "tocou_1s_fecha_fora": tx(lambda e: e >= 1, lambda e, f: f > 1),
                "passou_125_fecha_fora": tx(lambda e: e >= 1.25, lambda e, f: f > 1), "passou_125_chega_15": tx(lambda e: e >= 1.25, lambda e, f: e >= 1.5),
                "passou_15_chega_2": tx(lambda e: e >= 1.5, lambda e, f: e >= 2), "passou_15_fecha_fora": tx(lambda e: e >= 1.5, lambda e, f: f > 1)}}
    print(par, json.dumps(res[par], ensure_ascii=False))
json.dump(res, open(OUTF, "w"), ensure_ascii=False)
