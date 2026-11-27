#!/usr/bin/env python3
"""Conferente independente das opções mostradas na tela (call wall e put wall da CME). Só leitura. Uso: python3 confere_opcoes.py <pasta da branch dados>
Regra (27/11/2026, claude/quant-opcoes-fica-sai.md): fixas na chegada do boletim; vencimentos coletados ainda vivos; só strikes a até 1σ
semanal do ajuste; call = mais calls acima, put = mais puts abaixo; nível = strike menos o desconto; passou = rompida e mostra a 2ª.
Sai com código 1 se alguma parede publicada não puder ser usada. Gamma, max pain etc. só são gravados em arquivo e não são conferidos aqui."""
import sys, json, os, math, datetime as dt

D = sys.argv[1]
# GC fev - XAUUSD Vantage: 27,6 medido em 25/11/2026, encolhendo em linha reta até o vencimento. Remedir 1 vez por semana (aqui e em REGUA no coletor.py).
BASE_MEDIDA, MEDIDO_EM, VENCE, TOL = 27.6, dt.date(2026, 11, 25), dt.date(2027, 2, 24), 3.0
def ler(f):
    try: return json.load(open(os.path.join(D, f), encoding="utf-8"))
    except FileNotFoundError: return []
erros = []; resumo = []

def e(cond, msg):
    if cond: erros.append(msg)

paredes = {r["ativo"]: r for r in ler("mi_paredes.json")}
faixa = {r["ativo"]: r for r in ler("mi_faixa.json")}
for ativo, pref in (("XAUUSD", "ouro"), ("USDJPY", "iene")):
    cad = [o for o in ler(pref + "_cadeia.json") if o.get("settle") not in (None, "") and len(str(o.get("venc"))) == 10]
    r = paredes.get(ativo)
    if not cad: e(r and not r.get("sem_dado"), f"{ativo}: parede publicada sem cadeia"); continue
    if not r: erros.append(f"{ativo}: há cadeia, mas não há registro das paredes"); continue
    if r.get("sem_dado"): resumo.append(f"{ativo} sem dado ({r['sem_dado']})"); continue
    pg = cad[0]["data_pregao"]
    if ativo == "XAUUSD":
        mens = [o for o in ler("ouro_mensal.json") if o.get("data_pregao") == pg]; cad = cad + mens
        e(bool(mens) and not r.get("com_mensal"), "ouro: há vencimento mensal do mesmo boletim, mas as paredes não o somam")
    e(r["pregao"] != pg, f"{ativo}: parede do boletim {r['pregao']}, cadeia é de {pg}")
    fut = {o["venc"]: float(o["futuro"]) for o in cad if o["venc"] > pg}
    F = fut[min(fut)]; vivos = sorted(v for v in fut if abs(fut[v] / F - 1) < 0.004)
    e(r["vencimentos"] != vivos or abs(r["ajuste"] / F - 1) > 1e-9, f"{ativo}: vencimentos ou ajuste diferentes da cadeia")
    sd = r["sd_sem"]; iv = (faixa.get(ativo) or {}).get("iv")
    e(bool(iv) and not 0.7 < sd / (iv / 100 * math.sqrt(5 / 252)) < 1.4, f"{ativo}: 1σ semanal usado ({sd}) longe da volatilidade atual ({iv}%)")
    if ativo == "XAUUSD":
        venc = dt.date.fromisoformat(vivos[0]); desc = round(BASE_MEDIDA * (VENCE - venc).days / (VENCE - MEDIDO_EM).days, 1)
        e(abs(r["desconto"] - desc) > TOL, f"régua: painel desconta {r['desconto']}, esperado {desc}")
        e((venc - MEDIDO_EM).days > 14, f"régua medida há mais de 14 dias ({MEDIDO_EM}): medir de novo no MT5")
    p = r["preco"]
    for lado in ("call", "put"):
        acima = (lado == "call") == (ativo == "XAUUSD")          # no iene a call wall do USDJPY vem das puts de iene (strike abaixo)
        tipo = "C" if acima else "P"; oi = {}
        for o in cad:
            k = float(o["strike"])
            if o["venc"] in vivos and str(o["tipo"]).startswith(tipo) and (o.get("oi") or 0) > 0 and (F < k <= F * (1 + sd) if acima else F * (1 - sd) <= k < F):
                oi[k] = oi.get(k, 0) + o["oi"]
        nivel = (lambda k: k - r["desconto"]) if ativo == "XAUUSD" else (lambda k: r["ajuste_nivel"] * F / k)
        tol = 0.11 if ativo == "XAUUSD" else 0.005
        w = r.get(lado)
        if not oi: e(w is not None, f"{ativo} {lado} wall publicada sem contratos no limite"); continue
        if not w: erros.append(f"{ativo} {lado} wall vazia, mas há contratos no limite"); continue
        topo = max(oi.values())
        e(oi.get(w["strike"]) != topo or w["oi"] != topo, f"{ativo} {lado} wall {w['strike']} ({w['oi']}) não é o strike com mais contratos ({topo})")
        e(abs(w["nivel"] - nivel(w["strike"])) > tol, f"{ativo} {lado} wall nível {w['nivel']} diferente do strike convertido {nivel(w['strike']):.3f}")
        passou = (lambda n: p > n) if lado == "call" else (lambda n: p < n)
        e(passou(w["nivel"]) and not r.get("rompida_" + lado), f"{ativo} {lado} wall {w['nivel']} passada (preço {p}) sem marca de rompida")
        if r.get("rompida_" + lado):
            resto = [k for k in oi if k != w["strike"] and not passou(nivel(k))]; w2 = r.get(lado + "2")
            if not w2: e(bool(resto), f"{ativo}: falta a 2ª {lado} wall")
            else: e(w2["strike"] not in resto or oi.get(w2["strike"]) != w2["oi"] or abs(w2["nivel"] - nivel(w2["strike"])) > tol, f"{ativo} 2ª {lado} wall {w2} inválida")
        for x in (w, r.get(lado + "2")):
            if x: e(not any(abs(b[0] - x["nivel"]) < tol and b[1 if lado == "call" else 2] == x["oi"] for b in r.get("barras", [])), f"{ativo}: o mapa não mostra a {lado} wall {x['nivel']} com {x['oi']} contratos")
        resumo.append(f"{ativo} {lado} {w['nivel']}" + (" rompida" if r.get("rompida_" + lado) else "") + (f", 2ª {r[lado + '2']['nivel']}" if r.get(lado + "2") else ""))
# GLD complementar: só com pregão aberto, contratos em aberto, no máximo 1 dia útil de idade; não soma nem move a CME
r = paredes.get("XAUUSD") or {}; g = r.get("gld") or {}
if g and not g.get("sem_dado"):
    f = (ler("mi_gld_oi.json") or [None])[0]
    if not f: erros.append("GLD publicado sem a foto mi_gld_oi.json")
    else:
        d0 = dt.date.fromisoformat(f["dia"])
        e(d0.weekday() >= 5 or not "10:00" <= f["hora_ny"] < "16:00", f"GLD coletado fora do pregão ({f['dia']} {f['hora_ny']} NY)")
        e(g["dia"] != f["dia"] or abs(g["r"] - f["r"]) > 1e-9, "GLD publicado não é o da foto gravada")
        e((dt.date.today() - d0).days > 4, f"GLD velho ({d0})")
        e(any(c < 0 or p_ < 0 for _, c, p_ in f["linhas"]) or sum(c + p_ for _, c, p_ in f["linhas"]) <= 0, "GLD sem contratos em aberto")
        aj, sd = r["ajuste_nivel"], r["sd_sem"]
        for lado, i in (("call", 1), ("put", 2)):
            oi = {l[0]: l[i] for l in f["linhas"] if l[i] > 0 and (aj < l[0] * f["r"] <= aj * (1 + sd) + 0.06 if lado == "call" else aj * (1 - sd) - 0.06 <= l[0] * f["r"] < aj)}
            w = g.get(lado)
            if not oi: e(w is not None, f"GLD {lado} wall publicada sem contratos no limite"); continue
            if not w: erros.append(f"GLD {lado} wall vazia"); continue
            e(oi.get(w["strike_gld"]) != max(oi.values()), f"GLD {lado} wall strike {w['strike_gld']} não é o maior")
            e(abs(w["nivel"] - w["strike_gld"] * f["r"]) > 0.11 or abs(w["oi"] - w["contratos_gld"] / f["r"]) > 1, f"GLD {lado} wall: conversão errada {w}")
            e((r["preco"] > w["nivel"] if lado == "call" else r["preco"] < w["nivel"]) and not g.get("rompida_" + lado), f"GLD {lado} wall passada sem marca")
        for c_ in ("call", "call2", "put", "put2"):
            perto = [g[x]["nivel"] for x in (c_.rstrip("2"), c_.rstrip("2") + "2") if r.get(c_) and g.get(x) and abs(g[x]["nivel"] - r[c_]["nivel"]) <= 6]
            e(bool(perto) != (c_ in g.get("coincide", {})), f"'coincide com o GLD' errado na {c_}")
        resumo.append("GLD " + ", ".join(f"{l} {g[l]['nivel']}" for l in ("call", "put") if g.get(l)) + (f" (coincide: {g['coincide']})" if g.get("coincide") else ""))
elif r: resumo.append("GLD sem dado" + (f" ({g.get('sem_dado')})" if g else ""))
z = (ler("mi_0dte.json") or [{}])[0]
e(bool(z) and not z.get("preco_hora"), "preço do ouro sem horário (campo preco_hora)")

print(" | ".join(resumo)); print(f"paredes: {len(erros)} falha(s)")
for x in erros: print(" -", x)
sys.exit(1 if erros else 0)
