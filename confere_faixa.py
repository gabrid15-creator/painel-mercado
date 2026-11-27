#!/usr/bin/env python3
"""Conferente independente da faixa do ouro (teto e piso de 50/80/95%). Só leitura. Uso: python3 confere_faixa.py <pasta da branch dados>
Regra (27/11/2026): faixa = abertura x exp(±k x σ); σ = fechamento anterior do GVZ / raiz(252); k = quantis da excursão/σ das últimas
250 sessões completas ANTERIORES ao dia; acerto só com sessão encerrada, completa, sem feriado e com abertura real."""
import sys, json, os, math
D = sys.argv[1]
def ler(f):
    try: return json.load(open(os.path.join(D, f), encoding="utf-8"))
    except FileNotFoundError: return []
erros = []
def e(cond, msg):
    if cond: erros.append(msg)
r = next((x for x in ler("mi_faixa.json") if x["ativo"] == "XAUUSD"), {}); m = r.get("mapa") or {}; T = m.get("teto")
ks = ler("mi_faixa_k.json"); reg = ler("mi_faixa_ouro.json")
if not T: erros.append("faixa nova do ouro não publicada")
else:
    k_ = next((x for x in ks if x["dia"] == T["k_dia"] and x.get("aprovado")), None)
    if not k_: erros.append(f"k de {T['k_dia']} não está gravado ou não foi aprovado")
    else:
        k = k_["k"]
        e(not 0 < k[0] < k[1] < k[2] < 5, f"k fora de ordem: {k}")
        e(k_["ate"] >= k_["dia"], "k usa sessão do próprio dia ou futura")
        e(k_["n"] < 200 or k_["n"] > 250, f"k com {k_['n']} sessões")
        e(k_["gvz_data"] >= k_["dia"], "GVZ do próprio dia: tem de ser o anterior")
        sd = m["sd_dia"]
        if k_["dia"] >= "2026-11-30": e(abs(sd - k_["gvz"] / 100 / math.sqrt(252)) > 2e-5, f"σ do dia {sd} não vem do GVZ anterior ({k_['gvz']})")
        for f, p, kk in zip(T["faixas"], (50, 80, 95), k):
            lo, hi = m["ab_dia"] * math.exp(-kk * sd), m["ab_dia"] * math.exp(kk * sd)
            e(f["p"] != p or f["k"] != kk or abs(f["baixo"] - lo) > 0.06 or abs(f["cima"] - hi) > 0.06, f"faixa {p}%: publicado {f['baixo']}–{f['cima']}, esperado {lo:.2f}–{hi:.2f}")
    val = [x for x in reg if x.get("encerrada") and not x.get("ab_estimada") and not x.get("feriado") and x.get("barras", 0) >= 20 and x.get("saiu")]
    A = T["acerto"]; e(A["sessoes"] != len(val), f"acerto conta {A['sessoes']} sessões, registro tem {len(val)}")
    for x in val:
        for f in x["faixas"]:
            e(x["saiu"][str(f["p"])] != (x["maxima"] > f["cima"] or x["minima"] < f["baixo"]), f"{x['dia']}: marca de saída errada na faixa {f['p']}%")
    for p in ("50", "80", "95"):
        if val: e(abs(A[p] - 100 * sum(not x["saiu"][p] for x in val) / len(val)) > 0.6, f"acerto {p}% errado")
    hoje = reg[-1] if reg else {}
    e(bool(hoje.get("ab_estimada")) and hoje.get("saiu") is not None, "abertura estimada com toque marcado")
    print("faixa do ouro " + " | ".join(f"{f['p']}% {f['baixo']}–{f['cima']}" for f in T["faixas"]) + f" | k {T['k_dia']} | sessões no acerto: {A['sessoes']}")
# abertura pelo MT5: tem de ser a congelada
if m.get("ab_fonte"):
    fx_ = (ler("mapa_fixo.json") or [{}])[0]; ab_ = [v.get("ab_mt5") for k_, v in fx_.items() if k_.startswith("XAUUSD|") and "|sem|" not in k_ and v.get("ab_mt5")]
    e(not any(abs(m["ab_dia"] - v) < 0.06 for v in ab_), f"abertura {m['ab_dia']} diz ser do MT5 e não está congelada como tal")
# HAR + GVZ em sombra: refaz a conta da última previsão por outro caminho (mínimos quadrados por Gram-Schmidt) e o placar
sb = ler("mi_har_sombra.json")
if sb:
    z = sb[-1]; rv = {x["dia"]: x for x in ler("mi_har_rv.json")}
    base = [k_ for k_ in sorted(rv) if k_ < z["dia"] and rv[k_].get("gvz")]
    e(len(base) != z["sessoes_base"] or base[-1] != z["ultima_base"], f"sombra: base de {len(base)} sessões difere da gravada ({z['sessoes_base']})")
    lv = [math.log(max(rv[k_]["rv"], 1e-10)) for k_ in base]; gv = [rv[k_]["gvz"] for k_ in base] + [z["gvz"]]
    X = lambda i: [1.0, lv[i - 1], sum(lv[i - 5:i]) / 5, sum(lv[i - 22:i]) / 22, math.log(gv[i] / 100 / math.sqrt(252))]
    A = [X(i) for i in range(23, len(lv))]; y = lv[23:]; Q_ = []; R = [[0.0] * 5 for _ in range(5)]
    for c in range(5):
        v = [a[c] for a in A]
        for j, q_ in enumerate(Q_):
            R[j][c] = sum(a * b for a, b in zip(q_, v)); v = [a - R[j][c] * b for a, b in zip(v, q_)]
        R[c][c] = math.sqrt(sum(a * a for a in v)); Q_.append([a / R[c][c] for a in v])
    qty = [sum(a * b for a, b in zip(q_, y)) for q_ in Q_]; k = [0.0] * 5
    for i in range(4, -1, -1): k[i] = (qty[i] - sum(R[i][j] * k[j] for j in range(i + 1, 5))) / R[i][i]
    res = [b - sum(c * d for c, d in zip(k, a)) for a, b in zip(A, y)]; md = sum(res) / len(res); var = sum((x - md) ** 2 for x in res) / len(res)
    sig = math.sqrt(math.exp(sum(c * d for c, d in zip(k, X(len(lv)))) + var / 2)) * 100
    e(abs(sig - z["sigma_har_pct"]) > 0.002, f"sombra: σ HAR gravado {z['sigma_har_pct']}%, refeito {sig:.4f}%")
    e(not 0 < z["k_har"][0] < z["k_har"][1] < z["k_har"][2], f"sombra: k fora de ordem {z['k_har']}")
    for r_ in sb:
        e(any(abs(d_ - kk * r_["sigma_har_pct"]) > 0.003 for d_, kk in zip(r_["dist_har_pct"], r_["k_har"])), f"sombra {r_['dia']}: distâncias não são k × σ")
        if r_.get("excursao_pct") is not None:
            for nm in ("har", "gvz"):
                er = sum(max(q * (r_["excursao_pct"] - f_), (q - 1) * (r_["excursao_pct"] - f_)) for q, f_ in zip((0.5, 0.8, 0.95), r_[f"dist_{nm}_pct"])) / 3
                e(abs(er - r_[f"erro_{nm}"]) > 0.0002, f"sombra {r_['dia']}: erro {nm} errado")
    print(f"sombra HAR {z['dia']}: σ {z['sigma_har_pct']}% | 50/80/95% a {z['dist_har_pct']} (GVZ: {z['dist_gvz_pct']}) | no placar {sum(1 for r_ in sb if r_.get('conta'))}")
print(f"faixa: {len(erros)} falha(s)")
for x in erros: print(" -", x)
sys.exit(1 if erros else 0)
