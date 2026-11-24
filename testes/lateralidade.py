"""Quando o mercado fica LATERAL (faixa estreita) e quando anda mais? Mapa por dia da semana, hora, semana do mês, mês, semana de payroll,
semana de vencimento de opções e fim de mês/trimestre. Futuros da CME (Yahoo): diário 15 anos (GC, 6J, 6E, 6S, 6B) e 1 h 2 anos (horas).
Definições FIXAS antes de olhar (sem ajuste depois):
  amplitude relativa = ln(máx/mín) do dia ÷ média das amplitudes dos 20 dias ANTERIORES (sem olhar o futuro)
  dia ESTREITO  = amplitude relativa ≤ 0,70 · dia LARGO = ≥ 1,40
  dia de CORPO PEQUENO (vai-e-volta) = |fech − abert| ≤ 25% da amplitude do dia
Teste: qui-quadrado de cada grupo (ex.: 5 dias da semana) contra a taxa geral, com correção pelo nº de testes (Bonferroni, α = 0,05 ÷ nº de testes),
e exigência de o mesmo desvio nas duas metades do período. Só vale o que passa nas duas coisas.
Uso: python3 testes/lateralidade.py <saida.json>"""
import sys, json, math, statistics as st, urllib.request, datetime as dt, collections
from zoneinfo import ZoneInfo
BR = ZoneInfo("America/Sao_Paulo")
ATV = {"XAUUSD": "GC%3DF", "USDJPY": "6J%3DF", "EURUSD": "6E%3DF", "USDCHF": "6S%3DF", "GBPUSD": "6B%3DF"}
def y(s, r, i):
    u = f"https://query2.finance.yahoo.com/v8/finance/chart/{s}?range={r}&interval={i}"
    j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read())["chart"]["result"][0]
    q = j["indicators"]["quote"][0]
    return [(t, o, h, l, c) for t, o, h, l, c in zip(j["timestamp"], q["open"], q["high"], q["low"], q["close"]) if None not in (o, h, l, c) and h >= max(o, c) and l <= min(o, c) and l > 0]
def gser(a, x):   # gama incompleta regularizada superior Q(a,x) (série + fração contínua)
    if x <= 0: return 1.0
    if x < a + 1:
        ap, s_, d = a, 1 / a, 1 / a
        for _ in range(200):
            ap += 1; d *= x / ap; s_ += d
            if abs(d) < abs(s_) * 1e-12: break
        return 1 - s_ * math.exp(-x + a * math.log(x) - math.lgamma(a))
    b = x + 1 - a; c = 1e300; d = 1 / b; h = d
    for i in range(1, 200):
        an = -i * (i - a); b += 2; d = an * d + b; d = 1e-300 if abs(d) < 1e-300 else d; c = b + an / c; c = 1e-300 if abs(c) < 1e-300 else c
        d = 1 / d; de = d * c; h *= de
        if abs(de - 1) < 1e-12: break
    return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h
def qui2(grupos, taxa):   # grupos: {nome: (acertos, n)}
    x2 = sum((a - n * taxa) ** 2 / (n * taxa * (1 - taxa)) for a, n in grupos.values() if n)
    return x2, gser((len(grupos) - 1) / 2, x2 / 2)
def decide(grupos_ano, taxa):
    return {k: (a / n if n else None, n) for k, (a, n) in grupos_ano.items()}
RES = {}; NTESTES = 0; TESTES = []
def analisa(ativo, nome_dim, chaves, flag, dias, metade):
    """chaves: dia -> grupo; flag: dia -> bool. Taxa por grupo + qui², e estabilidade nas metades."""
    global NTESTES
    g = collections.defaultdict(lambda: [0, 0]); g1 = collections.defaultdict(lambda: [0, 0]); g2 = collections.defaultdict(lambda: [0, 0])
    for i, d in enumerate(dias):
        k = chaves(d)
        if k is None: continue
        for G in (g, g1 if i < metade else g2):
            G[k][1] += 1; G[k][0] += 1 if flag(d) else 0
    tot_a = sum(a for a, n in g.values()); tot_n = sum(n for a, n in g.values()); taxa = tot_a / tot_n
    x2, p = qui2({k: tuple(v) for k, v in g.items()}, taxa); NTESTES += 1
    por = {}
    for k, (a, n) in sorted(g.items()):
        r1 = g1[k][0] / g1[k][1] if g1[k][1] else None; r2 = g2[k][0] / g2[k][1] if g2[k][1] else None
        por[str(k)] = {"taxa": round(a / n * 100, 1), "n": n, "metade1": None if r1 is None else round(r1 * 100, 1), "metade2": None if r2 is None else round(r2 * 100, 1)}
    t = {"ativo": ativo, "dim": nome_dim, "taxa_geral": round(taxa * 100, 1), "p": p, "grupos": por}
    TESTES.append(t); return t
saida = {}
for ativo, sym in ATV.items():
    b = y(sym, "15y", "1d"); dias = []
    for t, o, h, l, c in b:
        d = dt.datetime.fromtimestamp(t, dt.timezone.utc).date()
        if d.weekday() > 4 or math.log(h / l) > 0.08: continue
        dias.append({"d": d, "o": o, "h": h, "l": l, "c": c, "A": math.log(h / l)})
    dias = [x for x in dias if x["A"] > 0]
    for i in range(20, len(dias)):
        atr = st.mean(x["A"] for x in dias[i - 20:i]); x = dias[i]; x["rel"] = x["A"] / atr
        x["corpo"] = abs(math.log(x["c"] / x["o"])) / x["A"]
    dias = dias[20:]; n = len(dias); metade = n // 2
    est = lambda x: x["rel"] <= 0.70; larg = lambda x: x["rel"] >= 1.40; corp = lambda x: x["corpo"] <= 0.25
    primeira_sex = lambda d: d.weekday() == 4 and d.day <= 7
    terceira_sex = lambda d: d.weekday() == 4 and 15 <= d.day <= 21
    def sem_mes(d): return (d.day - 1) // 7 + 1
    def semana_payroll(d):   # semana (seg–sex) que contém a 1ª sexta do mês
        sx = d + dt.timedelta(days=4 - d.weekday()); return sx.day <= 7
    def semana_venc(d):
        sx = d + dt.timedelta(days=4 - d.weekday()); return 15 <= sx.day <= 21
    def fim_mes(d): return (d + dt.timedelta(days=7)).month != d.month
    A_ = {}
    for rot, fl in (("estreito", est), ("largo", larg), ("corpo_pequeno", corp)):
        f = lambda x, fl=fl: fl(x)
        # dia da semana e semana do mês NÃO são testados nas barras diárias do Yahoo: elas são por dia-calendário (corte à meia-noite de NY) e o
        # "efeito segunda" (segunda mais estreita) era só isso. Esses dois cortes são feitos na sessão real 18h→17h NY em testes/lateralidade2.py.
        T = {"mes": analisa(ativo, rot + " × mês do ano", lambda x: x["d"].month, f, dias, metade),
             "payroll": analisa(ativo, rot + " × semana de payroll", lambda x: "semana do payroll" if semana_payroll(x["d"]) else "outras", f, dias, metade),
             "dia_payroll": analisa(ativo, rot + " × dia do payroll (1ª sexta)", lambda x: "1ª sexta" if primeira_sex(x["d"]) else "outros", f, dias, metade),
             "vencimento": analisa(ativo, rot + " × semana de vencimento de opções", lambda x: "semana do vencimento" if semana_venc(x["d"]) else "outras", f, dias, metade),
             "fim_mes": analisa(ativo, rot + " × última semana do mês", lambda x: "última semana" if fim_mes(x["d"]) else "outras", f, dias, metade)}
        A_[rot] = T
    # agrupamento: quanto o dia anda (amplitude relativa média) por dia da semana, e persistência (estreito ontem → estreito hoje)
    amp_dow = None
    pers = {"estreito_hoje_dado_estreito_ontem": round(sum(1 for i in range(1, n) if est(dias[i]) and est(dias[i - 1])) / max(1, sum(1 for i in range(1, n) if est(dias[i - 1]))) * 100, 1),
            "estreito_hoje_dado_largo_ontem": round(sum(1 for i in range(1, n) if est(dias[i]) and larg(dias[i - 1])) / max(1, sum(1 for i in range(1, n) if larg(dias[i - 1]))) * 100, 1)}
    # horas (1 h, 2 anos): % de horas "paradas" = amplitude da hora ≤ 0,5 × a mediana de TODAS as horas do ativo (limite fixo, em BRT)
    h1 = y(sym, "730d", "1h"); hr = collections.defaultdict(list)
    for t, o, h, l, c in h1:
        d = dt.datetime.fromtimestamp(t, BR)
        if d.weekday() < 5 or (d.weekday() == 6 and d.hour >= 19): hr[d.hour].append((d, math.log(h / l)))
    todas = [a for v in hr.values() for _, a in v]; med = st.median(todas)
    horas = {}
    for hh in sorted(hr):
        v = hr[hh]
        if len(v) < 150: continue
        k = len(v) // 2
        horas[f"{hh:02d}h"] = {"parada": round(sum(1 for _, a in v if a <= 0.5 * med) / len(v) * 100, 1), "agitada": round(sum(1 for _, a in v if a >= 2 * med) / len(v) * 100, 1), "n": len(v),
                               "parada_metade1": round(sum(1 for _, a in v[:k] if a <= 0.5 * med) / k * 100, 1), "parada_metade2": round(sum(1 for _, a in v[k:] if a <= 0.5 * med) / (len(v) - k) * 100, 1)}
    saida[ativo] = {"dias": n, "desde": str(dias[0]["d"]), "pct_estreito": round(sum(1 for x in dias if est(x)) / n * 100, 1), "pct_largo": round(sum(1 for x in dias if larg(x)) / n * 100, 1),
                    "pct_corpo_pequeno": round(sum(1 for x in dias if corp(x)) / n * 100, 1), "amplitude_relativa_por_dia_semana": amp_dow, "persistencia": pers, "horas": horas, "testes": {r: {k: v for k, v in T.items()} for r, T in A_.items()}}
alpha = 0.05 / NTESTES
print(f"{NTESTES} testes (5 ativos × 3 definições × 5 cortes); corte de p = {alpha:.5f}")
robustos = []
for t in TESTES:
    if t["p"] >= alpha: continue
    est_ok = all(v["metade1"] is not None and v["metade2"] is not None and (v["metade1"] - t["taxa_geral"]) * (v["metade2"] - t["taxa_geral"]) > 0 for v in t["grupos"].values() if abs(v["taxa"] - t["taxa_geral"]) >= 3)
    if est_ok: robustos.append(t)
for t in robustos: print("PASSOU:", t["ativo"], t["dim"], "taxa geral", t["taxa_geral"], "%", {k: f"{v['taxa']}% [{v['metade1']}/{v['metade2']}] n={v['n']}" for k, v in t["grupos"].items()}, f"p={t['p']:.1e}")
# resumo compacto para o painel (só o que passou: payroll, horas, persistência; mês só se passou)
rob = {(t["ativo"], t["dim"]) for t in robustos}; resumo = {}
for a_ in ATV:
    T_ = saida[a_]["testes"]; r_ = {"dias": saida[a_]["dias"], "desde": saida[a_]["desde"], "pct_estreito": saida[a_]["pct_estreito"], "pct_largo": saida[a_]["pct_largo"],
         "pct_corpo_pequeno": saida[a_]["pct_corpo_pequeno"], "persistencia": saida[a_]["persistencia"], "horas": {h: {"parada": v["parada"], "agitada": v["agitada"]} for h, v in saida[a_]["horas"].items()}}
    for nm, k in (("payroll_dia", "dia_payroll"), ("payroll_semana", "payroll"), ("vencimento_semana", "vencimento"), ("ultima_semana_mes", "fim_mes")):
        e1, l1 = T_["estreito"][k], T_["largo"][k]
        ok = (a_, e1["dim"]) in rob or (a_, l1["dim"]) in rob
        r_[nm] = {"estreito": {g: v["taxa"] for g, v in e1["grupos"].items()}, "largo": {g: v["taxa"] for g, v in l1["grupos"].items()}, "comprovado": ok}
    if (a_, T_["estreito"]["mes"]["dim"]) in rob: r_["mes_estreito"] = {g: v["taxa"] for g, v in T_["estreito"]["mes"]["grupos"].items()}
    resumo[a_] = r_
resumo["_meta"] = {"definicao": "estreito = amplitude do dia ≤ 0,70 × média dos 20 dias anteriores; largo ≥ 1,40; corpo pequeno = |fech − abert| ≤ 25% da amplitude. Diário 15 anos (futuros CME), horas 2 anos (1 h, horário de Brasília, mistura horário de verão)", "gerado": str(dt.date.today()), "testes": NTESTES}
json.dump(resumo, open(sys.argv[1].replace(".json", "_resumo.json"), "w"), ensure_ascii=False)
saida["_meta"] = {"testes": NTESTES, "corte_p": alpha, "robustos": [(t["ativo"], t["dim"]) for t in robustos], "gerado": str(dt.date.today())}
json.dump(saida, open(sys.argv[1], "w"), ensure_ascii=False)
for a in ATV: print(a, saida[a]["dias"], "dias | estreito", saida[a]["pct_estreito"], "% largo", saida[a]["pct_largo"], "% corpo pequeno", saida[a]["pct_corpo_pequeno"], "% | amplitude por dia", saida[a]["amplitude_relativa_por_dia_semana"], "| persistência", saida[a]["persistencia"])
