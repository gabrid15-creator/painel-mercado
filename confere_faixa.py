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
print(f"faixa: {len(erros)} falha(s)")
for x in erros: print(" -", x)
sys.exit(1 if erros else 0)
