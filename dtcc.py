#!/usr/bin/env python3
"""Opções de câmbio de balcão (OTC) publicadas pela DTCC (registro público da CFTC), grátis e quase ao vivo.
Uso: python3 dtcc.py <pasta_saida>   (roda a cada coleta, ~5 min; estado em dtcc_estado.json na branch "dados")

- Carrega os arquivos de dia fechado dos últimos JANELA dias (em ordem, poucos por rodada) e depois os pacotes
  intradiários de hoje (um a cada ~10–30 s). Só opções simples (vanilla) de USD/JPY, EUR/USD, USD/CHF e GBP/USD.
- Cada negócio: NEWT cria; MODI/CORR substituem o original; TERM/EROR removem. Vencidos saem.
- Tipo pelo nome do produto (UPI FISN): "Call JPY USD" = call de iene = put de USD/JPY (mais consistente que os
  campos de moeda, que vêm vazios ou trocados em ~10–20% dos negócios).
- Tamanho em US$ milhões; "+" no tamanho = teto de divulgação (negócio maior que o mostrado).
Saída: mi_otc.json (por par: vencimentos próximos, perfil por strike, paredes, PCR) e mi_otc_hist.json (retrato diário)."""
import sys, os, io, csv, json, time, math, zipfile, urllib.request, datetime as dt
from zoneinfo import ZoneInfo

OUT = sys.argv[1] if len(sys.argv) > 1 else "out"
T0 = time.monotonic(); LIMITE = int(os.environ.get("DTCC_LIMITE", "100"))   # segundos para este passo
API = "https://pddata.dtcc.com/ppd/api"
JANELA = 60                                  # dias de histórico para reconstruir negócios ainda vivos
NY = ZoneInfo("America/New_York"); AGORA = dt.datetime.now(dt.timezone.utc); HOJE = AGORA.date()
PAR = {"USD/JPY": "USDJPY", "JPY/USD": "USDJPY", "EUR/USD": "EURUSD", "USD/EUR": "EURUSD",
       "USD/CHF": "USDCHF", "CHF/USD": "USDCHF", "GBP/USD": "GBPUSD", "USD/GBP": "GBPUSD"}
BASE = {"USDJPY": "USD", "EURUSD": "EUR", "USDCHF": "USD", "GBPUSD": "GBP"}
PASSO = {"USDJPY": 0.25, "EURUSD": 0.0025, "USDCHF": 0.0025, "GBPUSD": 0.0025}   # degrau para agrupar strikes
CASAS = {"USDJPY": 3, "EURUSD": 5, "USDCHF": 5, "GBPUSD": 5}
FAIXA = {"USDJPY": (50, 400), "EURUSD": (0.3, 3), "USDCHF": (0.3, 3), "GBPUSD": (0.3, 3)}   # strike plausível
LIM_MI = 3000   # negócio acima de US$ 3 bi é descartado (o teto de divulgação da DTCC é bem menor)
DESC = {"strike": 0, "tamanho": 0, "sem_tamanho": 0, "tipo_inconsistente": 0}

def baixa(u):
    cache = os.environ.get("DTCC_CACHE")   # só para testes locais: guarda os arquivos de dia fechado
    if cache and ("/cumulative/" in u or "/intraday/" in u):
        f = os.path.join(cache, u.rsplit("/", 1)[1])
        if os.path.exists(f): return open(f, "rb").read()
        b = _baixa(u); open(f, "wb").write(b); return b
    return _baixa(u)
def _baixa(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (painel)"}), timeout=40) as r: return r.read()
def csvzip(b):
    z = zipfile.ZipFile(io.BytesIO(b)); return list(csv.DictReader(io.TextIOWrapper(z.open(z.namelist()[0]), "utf-8")))
def ler(n, pad):
    try: return json.load(open(os.path.join(OUT, n)))
    except Exception: return pad
def salva(n, x): json.dump(x, open(os.path.join(OUT, n), "w"), ensure_ascii=False, separators=(",", ":"))
def num(s):
    s = str(s or "").replace(",", "").strip(); cap = s.endswith("+")
    try: return float(s.rstrip("+")), cap
    except ValueError: return None, False

est = ler("dtcc_estado.json", {})
est.setdefault("neg", {}); est.setdefault("dias", []); est.setdefault("slice", {"dia": "", "id": 0})
if "prov" not in est:   # 1ª rodada com a regra nova: os últimos 7 dias podem ter sido marcados só pelos pacotes → relê os arquivos fechados
    est["dias"] = [x for x in est["dias"] if x < (HOJE - dt.timedelta(days=7)).isoformat()]; est["prov"] = []
# P7 (26/11/2026): "erros" era um contador que nunca zerava (88 em 26/11, quase tudo conexão derrubada pela DTCC) → agora conta só esta rodada;
# o acumulado fica em "erros_total"
est["erros_total"] = est.get("erros_total", est.get("erros", 0)); est["erros"] = 0
NEG = est["neg"]

def processa(rows):
    for r in rows:
        f = r.get("UPI FISN", "")
        if not f.startswith("NA/O Van "): continue
        par = PAR.get(r.get("Strike price currency/currency pair", ""))
        if not par: continue
        did = r["Dissemination Identifier"]; oid = r.get("Original Dissemination Identifier") or did; act = r["Action type"]
        if act in ("TERM", "EROR"): NEG.pop(oid, None); NEG.pop(did, None); continue
        venc = r.get("Expiration Date", "")[:10]
        if not venc or venc < HOJE.isoformat(): NEG.pop(oid, None); continue
        k, _ = num(r.get("Strike Price"))
        if not k: continue
        # strike na convenção do par (cotada por base). O rótulo do par e o strike às vezes vêm em convenções diferentes
        # (ex.: "USD/JPY" com strike 0,006309): decide pela faixa plausível; fora das duas → descarta.
        lo, hi = FAIXA[par]
        if not lo <= k <= hi:
            if lo <= 1 / k <= hi: k = 1 / k
            else: DESC["strike"] += 1; continue
        p = f.split()   # ["NA/O", "Van", "Call", "JPY", "USD"]
        if len(p) < 5 or p[2] not in ("Call", "Put"): continue
        sobre_base = p[3] == BASE[par]
        tipo = ("C" if p[2] == "Call" else "P") if sobre_base else ("P" if p[2] == "Call" else "C")
        # tipo só é aceito quando o nome do produto e o campo "Call currency" CONCORDAM: validado pelo prêmio pago
        # (16/11/2026, negócios bem fora/dentro do dinheiro): 99,8% de acerto no iene e 99,9% no euro. Quando discordam,
        # nenhum dos dois é confiável (iene: 37%/62%) → descarta. Campo vazio → descarta.
        cc = r.get("Call currency", "")
        campo = "C" if cc == BASE[par] else "P" if cc and cc in par.replace(BASE[par], "") else None
        if campo != tipo: DESC["tipo_inconsistente"] += 1; NEG.pop(oid, None); continue
        # tamanho em US$: os rótulos de moeda às vezes vêm trocados, então usa a CONTA: as duas pontas do negócio
        # (base e cotada) obedecem cotada = base × strike. Acha qual valor é a base e converte para dólar.
        n, cap = None, False
        for qa, qb in (("Call amount", "Put amount"), ("Notional amount-Leg 1", "Notional amount-Leg 2")):
            (va, ca), (vb, cb) = num(r.get(qa)), num(r.get(qb))
            if not va or not vb: continue
            if abs(vb / va / k - 1) < 0.06: base_amt, cap = va, ca or cb
            elif abs(va / vb / k - 1) < 0.06: base_amt, cap = vb, ca or cb
            else: continue
            n = base_amt if BASE[par] == "USD" else base_amt * k; break
        if not n:   # só uma ponta informada: aceita se o rótulo de moeda for coerente com o tamanho
            v, c = num(r.get("Notional amount-Leg 1")); moeda = r.get("Notional currency-Leg 1", "")
            if v and moeda == "USD" and v <= 5e9: n, cap = v, c
        if not n: DESC["sem_tamanho"] += 1; continue
        if n / 1e6 > LIM_MI: DESC["tamanho"] += 1; continue
        chave = oid if act in ("MODI", "CORR") else did
        NEG[chave] = {"p": par, "v": venc, "k": round(k, 6), "t": tipo, "n": round(n / 1e6, 3), "c": int(cap),
                      "ts": (r.get("Execution Timestamp") or "")[:16], "pr": num(r.get("Option Premium Amount"))[0], "pm": r.get("Option Premium Currency", "")}

def dias_uteis(a, b):
    d = a
    while d <= b:
        if d.weekday() < 5: yield d
        d += dt.timedelta(days=1)

# 1) dias fechados, do mais antigo para o mais novo (até ontem), poucos por rodada
# P7: um dia só vira "coberto" com o arquivo FECHADO lido. 404 de dia recente = arquivo ainda não saiu → tenta de novo;
# 404 com mais de 4 dias = feriado sem arquivo → coberto. Dia lido só pelos pacotes intradiários fica "provisório" (prov):
# não trava os pacotes de hoje, e o arquivo fechado é relido quando sair (reprocessar é seguro: negócios têm chave única).
pend = [d for d in dias_uteis(HOJE - dt.timedelta(days=JANELA), HOJE - dt.timedelta(days=1)) if d.isoformat() not in est["dias"]]
for d in pend:
    if time.monotonic() - T0 > LIMITE * 0.6: break
    try: processa(csvzip(baixa(f"{API}/report/cumulative/cftc/CFTC_CUMULATIVE_FOREX_{d:%Y_%m_%d}.zip")))
    except urllib.error.HTTPError as e:
        if e.code != 404: est["erros"] += 1; est["ultimo_erro"] = f"{d}: HTTP {e.code}"; break
        if (HOJE - d).days <= 4: continue
    except Exception as e: est["erros"] += 1; est["ultimo_erro"] = f"{d}: {str(e)[:120]}"; break
    est["dias"].append(d.isoformat())
pronto = not [d for d in pend if d.isoformat() not in est["dias"] and d.isoformat() not in est["prov"]]

# 2) pacotes intradiários de hoje (só depois do histórico completo, para manter a ordem dos eventos)
novos = 0
if pronto:
    try:
        lista = sorted(json.loads(baixa(f"{API}/slice/CFTC/FX")), key=lambda x: x["sliceId"])
        hoje_tag = HOJE.strftime("%Y_%m_%d")
        if est["slice"]["dia"] != HOJE.isoformat():
            if est["slice"]["dia"]: est["prov"].append(est["slice"]["dia"])   # coberto pelos pacotes, à espera do arquivo fechado
            est["slice"] = {"dia": HOJE.isoformat(), "id": 0}
        for s in lista:
            if hoje_tag not in s["fileName"] or s["sliceId"] <= est["slice"]["id"]: continue
            if time.monotonic() - T0 > LIMITE: break
            processa(csvzip(baixa(f"{API}/report/intraday/cftc/{s['fileName']}"))); est["slice"]["id"] = s["sliceId"]; novos += 1
            est["slice"]["ate"] = s.get("endTs")
    except Exception as e: est["erros"] += 1; est["ultimo_erro"] = str(e)[:150]
est["dias"] = sorted(set(x for x in est["dias"] if x >= (HOJE - dt.timedelta(days=JANELA + 5)).isoformat()))
est["prov"] = sorted(set(x for x in est["prov"] if x not in est["dias"] and x >= (HOJE - dt.timedelta(days=JANELA + 5)).isoformat()))
for k in [k for k, v in NEG.items() if v["v"] < HOJE.isoformat()]: NEG.pop(k)
est["erros_total"] += est["erros"]
salva("dtcc_estado.json", est)

# volatilidade implícita de cada par pelos prêmios pagos (testes/vol_dtcc.py, 2 anos: prevê a amplitude do dia melhor que a vol.
# realizada nos 4 pares, metades estáveis). Negócios das últimas 24 h, prazo 1–30 dias, strike a ≤ 1% do preço na hora do negócio.
NDIST = __import__("statistics").NormalDist()
def _black(S, K, T, s, call):
    a = s * math.sqrt(T); d1 = (math.log(S / K) + a * a / 2) / a; d2 = d1 - a
    return S * NDIST.cdf(d1) - K * NDIST.cdf(d2) if call else K * NDIST.cdf(-d2) - S * NDIST.cdf(-d1)
def _iv(S, K, T, P, call):
    lo, hi = 0.005, 1.0
    if not (_black(S, K, T, lo, call) < P < _black(S, K, T, hi, call)): return None
    for _ in range(50):
        m = (lo + hi) / 2; lo, hi = (m, hi) if _black(S, K, T, m, call) < P else (lo, m)
    return (lo + hi) / 2
YSYM = {"USDJPY": "JPY%3DX", "EURUSD": "EURUSD%3DX", "USDCHF": "CHF%3DX", "GBPUSD": "GBPUSD%3DX"}
def vol_impl(par):
    try:
        j = json.loads(baixa(f"https://query2.finance.yahoo.com/v8/finance/chart/{YSYM[par]}?range=5d&interval=1h"))["chart"]["result"][0]
        spot = {t // 3600: c for t, c in zip(j["timestamp"], j["indicators"]["quote"][0]["close"]) if c}
    except Exception: return None
    quote = par[3:]
    # P7: mínimo de 10 negócios (testes/min_negocios_dtcc.py: com 5, o erro típico da mediana ≈ a variação normal de um dia para o
    # outro e 10% das vezes erra 12–16%; com 10, 1,5–3% e 90% ≤ 7–10%). Faltando, alarga para 48 h e 72 h; com < 5 em 72 h, sem vol.
    for horas in (24, 48, 72):
        r = _vol_jan(par, spot, quote, horas)
        if r and r["negocios"] >= 10: return r
    return r if r and r["negocios"] >= 5 else None
def _vol_jan(par, spot, quote, horas):
    ini = AGORA - dt.timedelta(hours=horas); ivs = []
    for x in NEG.values():
        if x["p"] != par or x.get("c") or not x.get("pr") or x.get("pm") not in (BASE[par], quote): continue
        try: ts = dt.datetime.fromisoformat(x["ts"]).replace(tzinfo=dt.timezone.utc)
        except Exception: continue
        if ts < ini: continue
        S = spot.get(int(ts.timestamp()) // 3600); K = x["k"]; dias = (dt.date.fromisoformat(x["v"]) - ts.date()).days
        if not S or not 1 <= dias <= 30 or abs(math.log(K / S)) > 0.01: continue
        base_amt = x["n"] * 1e6 if BASE[par] == "USD" else x["n"] * 1e6 / K
        P = (x["pr"] if x["pm"] == quote else x["pr"] * S) / base_amt
        v = _iv(S, K, (dias - 0.5) / 365, P, x["t"] == "C")
        if v and 0.02 < v < 0.40: ivs.append(v)
    if not ivs: return None
    ivs.sort(); return {"iv": round(ivs[len(ivs) // 2] * 100, 2), "negocios": len(ivs), "janela": f"{horas} h"}

# 3) resumo por par
precos = {x["ativo"]: x["preco"] for x in ler("mi_ativos.json", []) if x.get("preco")}
ny = AGORA.astimezone(NY); corte = ny.date() if ny.hour < 10 else ny.date() + dt.timedelta(days=1)   # corte de NY, 10h
saida = []
for par in BASE:
    S = precos.get(par); vs = [v for v in NEG.values() if v["p"] == par and v["v"] >= corte.isoformat()]
    if not S or not vs: continue
    passo = PASSO[par]; grade = lambda k: round(round(k / passo) * passo, 6)
    venc = []
    for v in sorted({x["v"] for x in vs})[:12]:
        lv = [x for x in vs if x["v"] == v]; perto = [x for x in lv if abs(x["k"] / S - 1) <= 0.03]
        perfil = {}
        for x in perto:
            g = perfil.setdefault(grade(x["k"]), [0.0, 0.0, 0]); g[0 if x["t"] == "C" else 1] += x["n"]; g[2] += 1
        c = {k: g[0] for k, g in perfil.items()}; p = {k: g[1] for k, g in perfil.items()}
        teto = max((k for k in c if k >= S and c[k] > 0), key=lambda k: c[k], default=None)
        piso = max((k for k in p if k <= S and p[k] > 0), key=lambda k: p[k], default=None)
        tc, tp = sum(x["n"] for x in lv if x["t"] == "C"), sum(x["n"] for x in lv if x["t"] == "P")
        venc.append({"venc": v, "negocios": len(lv), "calls_mi": round(tc, 1), "puts_mi": round(tp, 1), "teto_limite": sum(x["c"] for x in lv),
                     "teto": teto, "piso": piso,
                     "perfil": [[k, round(g[0], 1), round(g[1], 1), g[2]] for k, g in sorted(perfil.items())]})
    hoje_fluxo = [x for x in vs if x["ts"][:10] == HOJE.isoformat()]
    saida.append({"ativo": par, "preco": S, "casas": CASAS[par], "corte": corte.isoformat(), "vencimentos": venc,
                  "hoje_negocios": len(hoje_fluxo), "hoje_mi": round(sum(x["n"] for x in hoje_fluxo), 1), "vol_impl": vol_impl(par)})
meta = {"atualizado": AGORA.strftime("%Y-%m-%d %H:%M UTC"), "pacote_ate": est["slice"].get("ate"), "dias_carregados": len(est["dias"]),
        "historico_completo": pronto, "janela_dias": JANELA, "negocios_vivos": len(NEG), "pacotes_nesta_rodada": novos, "erros": est["erros"], "erros_total": est["erros_total"],
        "dias_provisorios": est["prov"], "ultimo_erro": est.get("ultimo_erro"), "descartados_rodada": DESC}
salva("mi_otc.json", [{"meta": meta, "pares": saida}])
# retrato diário (1º do dia) para testar depois se as paredes seguram o preço
h = ler("mi_otc_hist.json", [])
if pronto and not any(x.get("dia") == HOJE.isoformat() for x in h):
    h.append({"dia": HOJE.isoformat(), "pares": [{"ativo": s["ativo"], "preco": s["preco"], "v": s["vencimentos"][:3]} for s in saida]})
    salva("mi_otc_hist.json", h[-400:])
print(json.dumps(meta, ensure_ascii=False))
