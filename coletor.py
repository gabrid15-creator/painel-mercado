#!/usr/bin/env python3
"""Coletor da aba Inteligência de mercado. Uso: python3 coletor.py <pasta_saida>
Só biblioteca padrão. Cada bloco é independente: se uma fonte falhar, os outros seguem e o erro vai para mi_status.json."""
import sys, os, json, csv, io, math, time, statistics as st, urllib.request, datetime as dt, traceback
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

OUT = sys.argv[1] if len(sys.argv) > 1 else "saida"
os.makedirs(OUT, exist_ok=True)
BRT = ZoneInfo("America/Sao_Paulo")
NOW = dt.datetime.now(BRT)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
      "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9"}
STATUS = []
TIMEOUT_REQ = 15          # segundos por requisição
LIMITE_TOTAL = 4 * 60     # segundos para a coleta inteira
FIM = time.monotonic() + LIMITE_TOTAL

class Estourou(TimeoutError): pass

def restante():
    return FIM - time.monotonic()

def get(url, headers=None, timeout=TIMEOUT_REQ):
    """Baixa a URL com no máximo `timeout` s por requisição (conexão + leitura) e sem passar do limite total."""
    if restante() <= 0: raise Estourou("limite total de 4 min atingido")
    fim = time.monotonic() + min(timeout, restante())
    h = dict(UA); h.update(headers or {})
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=max(1, fim - time.monotonic())) as r:
        partes = []
        while True:
            if time.monotonic() > fim: raise TimeoutError(f"sem resposta completa em {timeout}s: {url[:80]}")
            b = r.read1(65536)
            if not b: break
            partes.append(b)
        return b"".join(partes)

def bloco(nome):
    def deco(fn):
        def run(*a):
            if restante() <= 0:
                STATUS.append({"bloco": nome, "ok": False, "msg": "pulado: limite total de 4 min atingido (mantidos os dados anteriores)"})
                return None
            try:
                r = fn(*a)
                STATUS.append({"bloco": nome, "ok": True, "msg": ""})
                return r
            except Exception as e:
                STATUS.append({"bloco": nome, "ok": False, "msg": (type(e).__name__ + ": " + str(e))[:270] + " (mantidos os dados anteriores)"})
                traceback.print_exc()
                return None
        return run
    return deco

def ler(n):
    p = os.path.join(OUT, n); return json.load(open(p)) if os.path.exists(p) else []

def save(name, rows):
    if not rows: return
    with open(os.path.join(OUT, name), "w") as f:
        json.dump(rows, f, ensure_ascii=False, separators=(",", ":"))

def rnd(x, n=4):
    return None if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))) else round(x, n)

# ---------------------------------------------------------------- ativos
ATIVOS = {  # nome: (yahoo, casas)
    "EURUSD": ("EURUSD=X", 5), "GBPUSD": ("GBPUSD=X", 5), "USDJPY": ("JPY=X", 3), "USDCHF": ("CHF=X", 5),
    "XAUUSD": ("GC=F", 2), "NAS100": ("^NDX", 1),
}
FATORES_Y = {"DXY": "DX-Y.NYB", "WTI": "CL=F", "Brent": "BZ=F", "VIX": "^VIX", "Crédito HY (HYG)": "HYG", "Gás natural": "NG=F",
            "VIX 3 meses": "^VIX3M", "MOVE (vol. de Treasuries)": "^MOVE"}
FRED = {"US2Y": "DGS2", "US10Y": "DGS10", "Juro real 10a": "DFII10", "Curva 2s10s": "T10Y2Y", "Spread HY": "BAMLH0A0HYM2",
        "Dólar amplo Fed": "DTWEXBGS", "Fed funds": "DFF", "SOFR": "SOFR", "Infl. implícita 10a": "T10YIE",
        "Balanço Fed": "WALCL", "TGA": "WTREGEN", "RRP": "RRPONTSYD"}

def yahoo(sym, anos=21):
    p2 = int(NOW.timestamp()) + 86400; p1 = p2 - int(anos * 365.25 * 86400)
    j = json.loads(get(f"https://query2.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?period1={p1}&period2={p2}&interval=1d&includeAdjustedClose=false"))
    r = j["chart"]["result"][0]
    q = r["indicators"]["quote"][0]
    out = {}
    for t, o, h, l, c in zip(r["timestamp"], q["open"], q["high"], q["low"], q["close"]):
        if c is None: continue
        d = dt.datetime.fromtimestamp(t, ZoneInfo(r["meta"].get("exchangeTimezoneName", "UTC"))).date()
        out[d] = (o, h, l, c)
    return dict(sorted(out.items()))

def fred(ids, start):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={','.join(ids)}&cosd={start}"
    raw = get(url, {"User-Agent": "curl/8.5"}, timeout=30).decode()   # o FRED trava com User-Agent de navegador
    rd = csv.reader(io.StringIO(raw)); head = next(rd)
    res = {i: {} for i in ids}
    for row in rd:
        d = dt.date.fromisoformat(row[0])
        for i, v in zip(head[1:], row[1:]):
            if v not in ("", "."): res[i][d] = float(v)
    return res

import urllib.parse

def bund2y(start, prazo="R02XX"):
    url = (f"https://api.statistiken.bundesbank.de/rest/data/BBSIS/D.I.ZAR.ZI.EUR.S1311.B.A604.{prazo}.R.A.A._Z._Z.A"
           f"?format=csv&startPeriod={start}&lang=en")
    txt = get(url, {"Accept": "text/csv"}).decode("utf-8", "replace")
    out = {}
    for line in txt.splitlines():
        p = [x.strip().strip('"') for x in line.replace(";", ",").split(",")]
        if len(p) >= 2 and len(p[0]) == 10 and p[0][4] == "-":
            try: out[dt.date.fromisoformat(p[0])] = float(p[1])
            except ValueError: pass
    if not out: raise ValueError("Bundesbank sem dados")
    return out

# ---------------------------------------------------------------- utilidades
def closes(s): return {d: v[3] for d, v in s.items()}
def last(s, n=0):
    ks = sorted(s); return s[ks[-1 - n]] if len(ks) > n else None
def chg(s, n, pct=True):
    ks = sorted(s)
    if len(ks) <= n: return None
    a, b = s[ks[-1 - n]], s[ks[-1]]
    return (b / a - 1) * 100 if pct else b - a
def pctil(s, days=365):
    ks = sorted(s); lim = ks[-1] - dt.timedelta(days=days)
    v = [s[k] for k in ks if k >= lim]
    return 100 * sum(1 for x in v if x <= v[-1]) / len(v) if v else None
def corr(a, b):
    if len(a) < 5: return None
    try: return st.correlation(a, b)
    except Exception: return None
def rets(s, pct=True):
    ks = sorted(s); return {ks[i]: ((s[ks[i]] / s[ks[i-1]] - 1) if pct else (s[ks[i]] - s[ks[i-1]])) for i in range(1, len(ks))}

# ---------------------------------------------------------------- Goldbach (mesma regra do painel)
GB = [0,3,7,11,14,17,23,29,35,41,44,47,50,53,56,59,65,71,77,83,89,97,100]; DIAS = [1,3,7,11,14,17,23,29]
ANC = {1:8,2:7,3:6,4:5,5:4,6:3,7:2,8:1,9:9,10:8,11:7,12:6}
def _off(d): return d.weekday() >= 5 or (d.month, d.day) in ((12, 25), (1, 1))
def _info(d): return d.day in DIAS or d.month in GB or d.day + d.month in GB or abs(d.day - d.month) in GB or (d.year % 100 + d.month + d.day) in GB
def _anc(y, m):
    a = dt.date(y, m, ANC[m]); return a + dt.timedelta(2 if a.weekday() == 5 else 1 if a.weekday() == 6 else 0)
def goldbach(d):
    g = _info(d); k = d - dt.timedelta(1)
    while _off(k):
        g = g or _info(k); k -= dt.timedelta(1)
    a = _anc(d.year, d.month)
    if d < a: a = _anc(d.year - 1 if d.month == 1 else d.year, 12 if d.month == 1 else d.month - 1)
    rel = (d - a).days + 1
    return g, (rel == 1 or rel in DIAS)

# ---------------------------------------------------------------- coleta
P, F, FR, DE = {}, {}, {}, {}

@bloco("Preços (Yahoo)")
def b_precos():
    for k, (y, _) in ATIVOS.items(): P[k] = yahoo(y)
    for k, y in FATORES_Y.items():
        try: F[k] = closes(yahoo(y, 5))
        except Exception as e: STATUS.append({"bloco": "Yahoo: " + k, "ok": False, "msg": str(e)[:200]})

@bloco("Treasuries (Tesouro dos EUA)")
def b_tsy():
    for kind, cols in (("daily_treasury_yield_curve", {"2 Yr": "US2Y", "10 Yr": "US10Y"}), ("daily_treasury_real_yield_curve", {"10 YR": "Juro real 10a"})):
        for y in range(NOW.year - 4, NOW.year + 1):
            raw = get(f"https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{y}/all?type={kind}&field_tdr_date_value={y}&page&_format=csv").decode()
            for r in csv.DictReader(io.StringIO(raw)):
                d = dt.datetime.strptime(r["Date"], "%m/%d/%Y").date()
                for c, k in cols.items():
                    if r.get(c): FR.setdefault(k, {})[d] = float(r[c])
    FR["Curva 2s10s"] = {d: FR["US10Y"][d] - FR["US2Y"][d] for d in FR["US10Y"] if d in FR["US2Y"]}
    FR["Infl. implícita 10a"] = {d: FR["US10Y"][d] - FR["Juro real 10a"][d] for d in FR["Juro real 10a"] if d in FR["US10Y"]}

@bloco("Liquidez (Tesouro e Fed de NY)")
def b_liq():
    ini = (NOW.date() - dt.timedelta(days=3 * 366)).isoformat()
    js = json.loads(get("https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance"
                        f"?fields=record_date,account_type,open_today_bal&filter=record_date:gte:{ini}&page%5Bsize%5D=10000"))
    tga = {}
    for r in js["data"]:
        if "TGA" in r["account_type"] and "Opening" in r["account_type"] and r["open_today_bal"] not in (None, "null"):
            tga[dt.date.fromisoformat(r["record_date"])] = float(r["open_today_bal"]) / 1000
    FR["TGA"] = tga
    rrp = {}
    for o in json.loads(get(f"https://markets.newyorkfed.org/api/rp/reverserepo/propositions/search.json?startDate={ini}"))["repo"]["operations"]:
        d = dt.date.fromisoformat(o["operationDate"]); rrp[d] = rrp.get(d, 0) + float(o.get("totalAmtAccepted") or 0) / 1e9
    FR["RRP"] = rrp
    for k, p in (("SOFR", "secured/sofr"), ("Fed funds", "unsecured/effr")):
        FR[k] = {dt.date.fromisoformat(r["effectiveDate"]): float(r["percentRate"]) for r in json.loads(get(f"https://markets.newyorkfed.org/api/rates/{p}/search.json?startDate={ini}"))["refRates"]}

@bloco("Bund 2 anos (Bundesbank)")
def b_bund():
    DE.update(bund2y((NOW.date() - dt.timedelta(days=5 * 366)).isoformat()))

@bloco("Balanço do Fed (FRED) e condições financeiras (Fed de Chicago)")
def b_fred():
    ini = (NOW.date() - dt.timedelta(days=3 * 366)).isoformat()
    FR["Balanço Fed"] = {d: v / 1000 for d, v in fred(["WALCL"], ini)["WALCL"].items()}   # milhões -> bilhões
    try: FR["Condições financeiras (NFCI)"] = fred(["NFCI"], ini)["NFCI"]   # FRED: semanal, em dia
    except Exception:   # reserva: arquivo do Fed de Chicago (às vezes desatualizado)
        txt = get("https://www.chicagofed.org/-/media/publications/nfci/nfci-data-series-csv.csv").decode("utf-8", "replace")
        nfci = {}
        for r in csv.DictReader(io.StringIO(txt)):
            try: d = dt.datetime.strptime(r["Friday_of_Week"].strip(), "%m/%d/%Y").date()
            except Exception: continue
            if d.isoformat() >= ini and r.get("NFCI"): nfci[d] = float(r["NFCI"])
        FR["Condições financeiras (NFCI)"] = nfci

b_precos(); b_tsy(); b_liq(); b_bund(); b_fred()

# liquidez líquida do Fed = balanço − TGA − RRP (bilhões; balanço semanal, repete o último valor)
if FR.get("Balanço Fed") and FR.get("TGA"):
    bal = sorted(FR["Balanço Fed"].items()); liq = {}
    for d in sorted(FR["TGA"]):
        v = [x for k, x in bal if k <= d]
        if v: liq[d] = v[-1] - FR["TGA"][d] - FR.get("RRP", {}).get(d, 0)
    FR["Liquidez líquida Fed"] = liq
if F.get("VIX") and F.get("VIX 3 meses"):
    F["VIX ÷ VIX 3 meses"] = {d: F["VIX"][d] / F["VIX 3 meses"][d] for d in F["VIX"] if F["VIX 3 meses"].get(d)}

# drenagem de liquidez (bilhões de US$): TGA + RRP (subindo = tira liquidez do mercado)
if FR.get("TGA") and FR.get("RRP"):
    FR["TGA + RRP"] = {d: FR["TGA"][d] + FR["RRP"].get(d, 0) for d in FR["TGA"]}
if FR.get("US2Y") and DE:
    FR["Spread 2a EUA−Alemanha"] = {d: FR["US2Y"][d] - DE[d] for d in FR["US2Y"] if d in DE}
    FR["Bund 2a"] = DE

# ---------------------------------------------------------------- macro (tabela + histórico 1 ano)
@bloco("Macro")
def b_macro():
    grupos = {"Juros": ["US2Y", "US10Y", "Juro real 10a", "Curva 2s10s", "Bund 2a", "Spread 2a EUA−Alemanha", "Fed funds", "SOFR", "Infl. implícita 10a"],
              "Dólar": ["DXY"], "Liquidez": ["Liquidez líquida Fed", "Balanço Fed", "TGA + RRP", "TGA", "RRP"],
              "Risco": ["VIX", "VIX ÷ VIX 3 meses", "MOVE (vol. de Treasuries)", "Condições financeiras (NFCI)", "Crédito HY (HYG)"], "Energia": ["WTI", "Brent", "Gás natural"]}
    pts = {"Condições financeiras (NFCI)", "VIX ÷ VIX 3 meses", "US2Y","US10Y","Juro real 10a","Curva 2s10s","Bund 2a","Spread 2a EUA−Alemanha","Fed funds","SOFR","Infl. implícita 10a"}
    rows, hist = [], []
    lim = NOW.date() - dt.timedelta(days=366)
    for g, ks in grupos.items():
        for k in ks:
            s = F.get(k) or FR.get(k)
            if not s: continue
            isp = k in pts
            d0 = max(s)
            rows.append({"grupo": g, "serie": k, "data": d0.isoformat(), "valor": rnd(last(s), 3),
                         "var_1d": rnd(chg(s, 1, not isp), 3), "var_5d": rnd(chg(s, 5, not isp), 3), "var_20d": rnd(chg(s, 20, not isp), 3),
                         "unidade_var": "p.p." if isp else "%", "pctil_1a": rnd(pctil(s), 0)})
            hist += [{"serie": k, "data": d.isoformat(), "valor": rnd(v, 4)} for d, v in sorted(s.items()) if d >= lim]
    # fonte que falhou ou foi pulada: mantém a linha e o histórico anteriores dessa série
    novas = {r["serie"] for r in rows}
    rows += [r for r in ler("mi_macro.json") if r.get("serie") not in novas]
    hist += [r for r in ler("mi_hist.json") if r.get("serie") not in novas]
    save("mi_macro.json", rows); save("mi_hist.json", hist)
b_macro()

def stt(v):
    n = len(v); m = st.mean(v); ac = 100 * sum(x > 0 for x in v) / n
    t = m / (st.stdev(v) / math.sqrt(n)) if n > 2 and st.stdev(v) > 0 else 0
    sinal = "alta" if ac >= 60 and m > 0 else "baixa" if ac <= 40 and m < 0 else "inconclusivo"
    return {"media": rnd(m * 100, 3), "acerto": rnd(ac, 0), "n": n, "t": rnd(t, 2), "sinal": sinal}

# ---------------------------------------------------------------- resumo por ativo, sazonalidade, correlações, Goldbach
@bloco("Ativos, sazonalidade e correlações")
def b_ativos():
    resumo, saz, cor = [], [], []
    hoje = NOW.date()
    fat = {"DXY": (F.get("DXY"), True), "US2Y": (FR.get("US2Y"), False), "Juro real 10a": (FR.get("Juro real 10a"), False),
           "Spread 2a EUA−Alemanha": (FR.get("Spread 2a EUA−Alemanha"), False), "WTI": (F.get("WTI"), True), "VIX": (F.get("VIX"), True)}
    for k in ATIVOS: fat[k] = (closes(P[k]) if k in P else None, True)
    R = {k: rets(s, p) for k, (s, p) in fat.items() if s}
    for a, (sym, cs) in ATIVOS.items():
        if a not in P: continue
        s = P[a]; c = closes(s); ks = sorted(c)
        c20 = {d: v for d, v in c.items() if d >= hoje - dt.timedelta(days=20 * 366)}
        # sazonalidade mensal
        mens = {}
        for d, v in c20.items(): mens[(d.year, d.month)] = v
        mk = sorted(mens); mret = {mk[i]: mens[mk[i]] / mens[mk[i-1]] - 1 for i in range(1, len(mk))}
        JAN = (5, 10, 20)
        for m in range(1, 13):
            prs = sorted(((y, x) for (y, mm), x in mret.items() if mm == m and (y, mm) != (hoje.year, hoje.month)))
            for w in JAN:
                v = [x for y, x in prs if y >= hoje.year - w]
                if v: saz.append({"ativo": a, "tipo": "mes", "janela": w, "chave": m, **stt(v)})
        dr = rets(c20)
        for w in JAN:
            drw = {d: x for d, x in dr.items() if d.year >= hoje.year - w}
            for wd in range(5):
                v = [x for d, x in drw.items() if d.weekday() == wd]
                if v: saz.append({"ativo": a, "tipo": "dia_semana", "janela": w, "chave": wd + 1, **stt(v)})
            for k in range(1, 6):
                v = [x for d, x in drw.items() if (d.day - 1) // 7 + 1 == k]
                if v: saz.append({"ativo": a, "tipo": "semana_mes", "janela": w, "chave": k, **stt(v)})
        # caminho do mês atual: média por janela + cada um dos últimos 5 anos + ano atual
        prof = {w: {} for w in JAN}; anos = sorted({y for (y, m) in mk if m == hoje.month and y < hoje.year})[-5:] + [hoje.year]
        for (y, m) in mk:
            if m != hoje.month: continue
            dd = sorted(d for d in c20 if d.year == y and d.month == m)
            prev = [d for d in c20 if d < dd[0]] if dd else []
            if not dd or not prev: continue
            base = c20[max(prev)]
            for i, d in enumerate(dd):
                v = (c20[d] / base - 1) * 100
                if y != hoje.year:
                    for w in JAN:
                        if y >= hoje.year - w: prof[w].setdefault(i + 1, []).append(v)
                if y in anos: saz.append({"ativo": a, "tipo": "perfil_ano", "chave": i + 1, "ano": y, "media": rnd(v, 3), "acerto": None, "n": 1})
        for w in JAN:
            for i, v in sorted(prof[w].items()):
                if len(v) >= max(3, w // 2): saz.append({"ativo": a, "tipo": "perfil_mes", "janela": w, "chave": i, "media": rnd(st.mean(v), 3), "acerto": None, "n": len(v)})
        # Goldbach: onde caem as máximas/mínimas semanais (últimos 10 anos)
        s10 = {d: v for d, v in s.items() if d >= hoje - dt.timedelta(days=3653) and d.weekday() < 5}
        sem = {}
        for d, v in s10.items(): sem.setdefault(d.isocalendar()[:2], []).append((d, v))
        tot = gbx = hpx = 0; base_g = base_h = 0; nd = 0
        for wk, lst in sem.items():
            if len(lst) < 4: continue
            dh = max(lst, key=lambda x: x[1][1])[0]; dl = min(lst, key=lambda x: x[1][2])[0]
            for d in (dh, dl):
                g, h = goldbach(d); tot += 1; gbx += g; hpx += h
            for d, _ in lst:
                g, h = goldbach(d); nd += 1; base_g += g; base_h += h
        # sweeps: o dia passa da máxima (mínima) dos 10 pregões anteriores e fecha de volta abaixo (acima), na metade oposta do candle
        ks10 = sorted(s10); sw = swg = swh = 0
        for i in range(10, len(ks10)):
            d = ks10[i]; _o, hi, lo, fe = s10[d]   # nomes próprios: c e h já são usados neste bloco
            if None in (hi, lo, fe) or hi <= lo: continue
            ph = max(s10[k][1] for k in ks10[i - 10:i]); pl = min(s10[k][2] for k in ks10[i - 10:i]); meio = (hi + lo) / 2
            if (hi > ph and fe < ph and fe < meio) or (lo < pl and fe > pl and fe > meio):
                g, hp = goldbach(d); sw += 1; swg += g; swh += hp
        gbr_sw = {"gb_sweep": rnd(100 * swg / sw, 1) if sw else None, "hp_sweep": rnd(100 * swh / sw, 1) if sw else None, "sweep_n": sw}
        gbr = {**gbr_sw, "gb_extremos": rnd(100 * gbx / tot, 1) if tot else None, "gb_base": rnd(100 * base_g / nd, 1) if nd else None,
               "hp_extremos": rnd(100 * hpx / tot, 1) if tot else None, "hp_base": rnd(100 * base_h / nd, 1) if nd else None}
        # correlações (retornos diários)
        ra = R.get(a, {})
        for fk, rf in R.items():
            if fk == a: continue
            for w in (20, 60, 250):
                ds = [d for d in sorted(ra) if d in rf][-w:]
                cor.append({"ativo": a, "fator": fk, "janela": w, "corr": rnd(corr([ra[d] for d in ds], [rf[d] for d in ds]), 2)})
        # valor justo por regressão (250 dias)
        vj = None
        drv = "Spread 2a EUA−Alemanha" if a == "EURUSD" else "Juro real 10a" if a == "XAUUSD" else "US2Y" if a in ("USDJPY", "USDCHF", "GBPUSD") else "Juro real 10a"
        x = fat.get(drv, (None,))[0]
        if x:
            ds = [d for d in ks if d in x][-250:]
            if len(ds) > 60:
                xs = [x[d] for d in ds]; ys = [c[d] for d in ds]
                sl, ic = st.linear_regression(xs, ys)
                res = [y - (sl * xx + ic) for xx, y in zip(xs, ys)]
                sd = st.pstdev(res); fv = sl * xs[-1] + ic
                dx20 = xs[-1] - xs[-21] if len(xs) > 21 else 0
                vj_imp = sl * dx20 / ys[-1] * 100
                vj = {"vj_imp20": rnd(vj_imp, 3), "vj_fator": drv, "vj_valor": rnd(fv, cs), "vj_desvio_pct": rnd((ys[-1] / fv - 1) * 100, 2), "vj_z": rnd(res[-1] / sd if sd else None, 2),
                      "vj_r2": rnd(st.correlation(xs, ys) ** 2, 2)}
        mes = [r for r in saz if r["ativo"] == a and r["tipo"] == "mes" and r["chave"] == hoje.month and r["janela"] == 20]
        mes10 = [r for r in saz if r["ativo"] == a and r["tipo"] == "mes" and r["chave"] == hoje.month and r["janela"] == 10]
        hi52 = max(v[1] for d, v in s.items() if d >= hoje - dt.timedelta(days=365)); lo52 = min(v[2] for d, v in s.items() if d >= hoje - dt.timedelta(days=365))
        atr = st.mean([(v[1] - v[2]) for d, v in list(s.items())[-14:] if v[1] and v[2]])
        resumo.append({"ativo": a, "data": ks[-1].isoformat(), "preco": rnd(c[ks[-1]], cs), "var_1d": rnd(chg(c, 1), 2), "var_5d": rnd(chg(c, 5), 2),
                       "var_20d": rnd(chg(c, 20), 2), "var_ano": rnd((c[ks[-1]] / c[max(d for d in ks if d.year < hoje.year)] - 1) * 100, 2),
                       "max_52s": rnd(hi52, cs), "min_52s": rnd(lo52, cs), "atr14": rnd(atr, cs),
                       "saz_mes_media": mes[0]["media"] if mes else None, "saz_mes_acerto": mes[0]["acerto"] if mes else None, "saz_mes_n": mes[0]["n"] if mes else None,
                       "saz_mes_sinal": mes[0]["sinal"] if mes else None, "saz_mes_t": mes[0]["t"] if mes else None,
                       "saz_mes10_media": mes10[0]["media"] if mes10 else None, "saz_mes10_acerto": mes10[0]["acerto"] if mes10 else None, "saz_mes10_sinal": mes10[0]["sinal"] if mes10 else None,
                       **gbr, **(vj or {})})
    save("mi_ativos.json", resumo); save("mi_sazon.json", saz); save("mi_corr.json", cor)
b_ativos()

# ---------------------------------------------------------------- COT (CFTC)
COT = {"EURUSD": ("099741", "tff", 1), "GBPUSD": ("096742", "tff", 1), "USDJPY": ("097741", "tff", -1), "USDCHF": ("092741", "tff", -1),
       "XAUUSD": ("088691", "dis", 1), "NAS100": ("209742", "tff", 1)}
@bloco("COT (CFTC)")
def b_cot():
    rows = []
    for a, (code, kind, sg) in COT.items():
        ds = "gpe5-46if" if kind == "tff" else "72hh-3qpy"
        url = (f"https://publicreporting.cftc.gov/resource/{ds}.json?cftc_contract_market_code={code}"
               "&$order=report_date_as_yyyy_mm_dd%20DESC&$limit=160")
        js = json.loads(get(url))
        if not js: continue
        def n(r, k): return float(r.get(k) or 0)
        NR = ("nonrept_positions_long_all", "nonrept_positions_short_all")
        grupos = ([("Fundos alavancados (≈ hedge funds)", "especulativo", [("lev_money_positions_long", "lev_money_positions_short")]),
                   ("Gestores de ativos (institucional)", "institucional", [("asset_mgr_positions_long", "asset_mgr_positions_short")]),
                   ("Dealers (≈ commercials)", "commercial", [("dealer_positions_long_all", "dealer_positions_short_all")]),
                   ("Varejo (não reportáveis)", "varejo", [NR])] if kind == "tff" else
                  [("Managed money (≈ hedge funds)", "especulativo", [("m_money_positions_long_all", "m_money_positions_short_all")]),
                   ("Commercials (produtores + swap dealers)", "commercial", [("prod_merc_positions_long", "prod_merc_positions_short"), ("swap_positions_long_all", "swap__positions_short_all")]),
                   ("Varejo (não reportáveis)", "varejo", [NR])])
        js = list(reversed(js))
        for g, papel, pares in grupos:
            if pares[0][0] not in js[-1]: continue
            net = [sum(n(r, lk) - n(r, sk) for lk, sk in pares) for r in js]
            w = net[-156:]
            idx = 100 * (net[-1] - min(w)) / (max(w) - min(w)) if max(w) > min(w) else None
            rows.append({"ativo": a, "grupo": g, "papel": papel, "data": js[-1]["report_date_as_yyyy_mm_dd"][:10], "liquido": int(net[-1]),
                         "var_semana": int(net[-1] - net[-2]) if len(net) > 1 else None, "indice_3a": rnd(idx, 0),
                         "oi": int(n(js[-1], "open_interest_all")), "sinal_par": sg,
                         "hist": [[r["report_date_as_yyyy_mm_dd"][:10], int(v)] for r, v in zip(js[-104:], net[-104:])]})
    if not rows: raise ValueError("CFTC sem linhas")
    save("mi_cot.json", rows)
b_cot()

# ---------------------------------------------------------------- dólar e juros (intraday) + nowcast + CTA
@bloco("Dólar e juros (Yahoo, MOF Japão, FRED)")
def b_dolar():
    rows = []
    def ponto(nome, serie, unid, bps=True):
        ks = sorted(serie); v = serie[ks[-1]]
        d1 = v - serie[ks[-2]] if len(ks) > 1 else None; d5 = v - serie[ks[-6]] if len(ks) > 5 else None
        k = 100 if bps else 1
        rows.append({"serie": nome, "data": ks[-1].isoformat(), "valor": rnd(v, 3), "unid": unid,
                     "d1": rnd(d1 * k, 1) if d1 is not None else None, "d5": rnd(d5 * k, 1) if d5 is not None else None})
    us = {}
    for nome, sym, div in (("EUA 13 semanas", "^IRX", 1), ("EUA 5 anos", "^FVX", 1), ("EUA 10 anos", "^TNX", 1)):
        try: us[nome] = closes(yahoo(sym, 1)); ponto(nome, us[nome], "%")
        except Exception as e: STATUS.append({"bloco": "Yahoo: " + sym, "ok": False, "msg": str(e)[:120]})
    try:   # Fed Funds futuro do PRÓXIMO mês, contrato fixo (o ZQ=F do Yahoo troca de contrato e cria saltos falsos): juro implícito = 100 − preço
        mm = NOW.month % 12 + 1; aa = NOW.year + (NOW.month == 12); cod = "FGHJKMNQUVXZ"[mm - 1]
        zq = closes(yahoo(f"ZQ{cod}{aa % 100:02d}.CBT", 1)); imp = {d: 100 - v for d, v in zq.items()}
        ponto("Fed Funds implícito (" + ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"][mm - 1] + f"/{aa % 100:02d})", imp, "%")
        ef = FR.get("Fed funds")
        if ef: rows[-1]["vs_efetivo_bps"] = rnd((imp[max(imp)] - ef[max(ef)]) * 100, 1)
    except Exception as e: STATUS.append({"bloco": "Yahoo: ZQ=F", "ok": False, "msg": str(e)[:120]})
    try:   # JGB 10 anos (Ministério das Finanças do Japão, diário)
        txt = get("https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/jgbcme.csv").decode("utf-8", "replace")
        lin = [l.split(",") for l in txt.splitlines() if l[:4].isdigit()]
        hd = next(l.split(",") for l in txt.splitlines() if l.lower().startswith("date"))
        i10 = [h.strip().upper() for h in hd].index("10Y")
        jgb = {}
        for l in lin[-400:]:
            try: jgb[dt.datetime.strptime(l[0].strip(), "%Y/%m/%d").date()] = float(l[i10])
            except Exception: pass
        ponto("Japão 10 anos (JGB)", jgb, "%")
        if us.get("EUA 10 anos"):
            u = us["EUA 10 anos"]; sp = {d: u[d] - jgb[d] for d in u if d in jgb}
            if sp: ponto("Diferencial 10a EUA − Japão", sp, "p.p.")
    except Exception as e: STATUS.append({"bloco": "MOF Japão (JGB)", "ok": False, "msg": str(e)[:120]})
    try:   # Bund 10 anos (Bundesbank, diário) e diferencial EUA − Alemanha (mede o euro)
        b10 = bund2y((NOW.date() - dt.timedelta(days=400)).isoformat(), "R10XX")
        ponto("Alemanha 10 anos (Bund)", b10, "%")
        if us.get("EUA 10 anos"):
            u = us["EUA 10 anos"]; sp = {d: u[d] - b10[d] for d in u if d in b10}
            if sp: ponto("Diferencial 10a EUA − Alemanha", sp, "p.p.")
    except Exception as e: STATUS.append({"bloco": "Bundesbank (Bund 10a)", "ok": False, "msg": str(e)[:120]})
    try:   # GDPNow (Fed de Atlanta): previsão do PIB do trimestre, atualizada a cada dado novo
        g = fred(["GDPNOW"], (NOW.date() - dt.timedelta(days=200)).isoformat())["GDPNOW"]
        if g: ponto("GDPNow (PIB EUA, trimestre atual)", g, "% anualizado", bps=False); rows[-1]["d1"] = rows[-1]["d5"] = None   # série por trimestre: variação diária não se aplica
    except Exception as e: STATUS.append({"bloco": "FRED: GDPNOW", "ok": False, "msg": str(e)[:120]})
    if not rows: raise ValueError("nenhuma série de dólar/juros")
    save("mi_dolar.json", rows)
b_dolar()

@bloco("CTA (modelo de tendência)")
def b_cta():
    # posição estimada de fundos de tendência: média do sinal de 4 janelas (1, 3, 6 e 12 meses);
    # gatilho = preço de referência de cada janela (cruzar ele vira o sinal daquela janela)
    rows = []
    # validação (2016+): só no ouro o modelo acompanha o COT (corr 0,59) e tem algum acerto em 20 dias (54,5%, t 2,1);
    # em iene, franco e euro não passou → fica só o ouro
    series = {k: closes(v) for k, v in P.items() if k == "XAUUSD"}
    for a, c in series.items():
        ks = sorted(c); px = c[ks[-1]]
        if len(ks) < 260: continue
        jan = [(20, "1 mês"), (60, "3 meses"), (125, "6 meses"), (250, "12 meses")]
        sin = []; gat = []
        for n, nome in jan:
            ref = c[ks[-1 - n]]; s_ = 1 if px > ref else -1; sin.append(s_)
            gat.append({"janela": nome, "nivel": rnd(ref, ATIVOS.get(a, (None, 2))[1]), "lado": s_, "dist_pct": rnd((ref / px - 1) * 100, 2)})
        pos = sum(sin) / len(sin) * 100
        prox = min(gat, key=lambda g: abs(g["dist_pct"]))
        rows.append({"ativo": a, "preco": rnd(px, 5), "posicao": rnd(pos, 0), "gatilhos": gat, "gatilho_proximo": prox})
    if not rows: raise ValueError("sem séries")
    save("mi_cta.json", rows)
b_cta()

@bloco("Regime juros x pares")
def b_regime():
    # correlação e beta semanais (26 e 52 semanas) entre cada par e dólar/juros: mostra se a ligação está valendo agora
    def semanal(s):
        w = {}
        for d in sorted(s): w[d.isocalendar()[:2]] = (d, s[d])
        return {d: v for d, v in sorted(w.values())}
    FAT = {"DXY": (F.get("DXY"), True), "EUA 2a": (FR.get("US2Y"), False), "EUA 10a": (FR.get("US10Y"), False),
           "Juro real 10a": (FR.get("Juro real 10a"), False)}
    ESP = {"XAUUSD": -1, "USDJPY": 1, "USDCHF": 1, "EURUSD": -1}   # sinal histórico esperado (2016+)
    rows = []
    for a, esp in ESP.items():
        if a not in P: continue
        pa = semanal(closes(P[a])); ra = {}
        ks = list(pa)
        for i in range(1, len(ks)): ra[ks[i].isocalendar()[:2]] = (pa[ks[i]] / pa[ks[i - 1]] - 1) * 100
        fat = []
        for nome, (serie, pct) in FAT.items():
            if not serie: continue
            pf = semanal(serie); kf = list(pf); rf = {}
            for i in range(1, len(kf)):
                rf[kf[i].isocalendar()[:2]] = (pf[kf[i]] / pf[kf[i - 1]] - 1) * 100 if pct else (pf[kf[i]] - pf[kf[i - 1]]) * 100
            sem = sorted(set(ra) & set(rf))[:-1] if len(set(ra) & set(rf)) > 1 else []   # tira a semana em curso
            def est(n):
                ss = sem[-n:]
                if len(ss) < n * 0.8: return None, None
                x = [rf[k] for k in ss]; y = [ra[k] for k in ss]
                try: c = st.correlation(x, y); b = st.linear_regression(x, y).slope
                except Exception: return None, None
                return c, b * (1 if pct else 10)
            c26, b26 = est(26); c52, _ = est(52)
            if c26 is None: continue
            forca = "forte" if abs(c26) >= 0.4 else "média" if abs(c26) >= 0.2 else "fraca"
            fat.append({"fator": nome, "corr26": rnd(c26, 2), "corr52": rnd(c52, 2), "beta": rnd(b26, 2),
                        "unid": "% por +1% no DXY" if pct else "% por +10 bps", "forca": forca,
                        "quebrou": abs(c26) >= 0.2 and (c26 > 0) != (esp > 0)})
        if fat: rows.append({"ativo": a, "fatores": fat, "principal": max(fat, key=lambda f: abs(f["corr26"]))["fator"]})
    if not rows: raise ValueError("sem dados")
    save("mi_regime.json", rows)
b_regime()

@bloco("Faixa esperada (opções)")
def b_faixa():
    # volatilidade implícita de 30 dias → faixa de ±1σ e ±2σ para dia, semana e mês
    # validação ouro (GVZ, 2016+): semana ±1σ conteve 74% dos fechamentos (teórico 68%), ±2σ 96%
    FONTE = {"XAUUSD": ("GLD", "^GVZ"), "USDJPY": ("FXY", None), "USDCHF": ("FXF", None), "EURUSD": ("FXE", None), "GBPUSD": (None, None)}
    rows = []; hist = {(h["ativo"], h["data"]): h for h in ler("mi_faixa_hist.json")}
    fx0 = ler("mapa_fixo.json"); FIXO = fx0[0] if fx0 else {}
    MH = {f"{h['ativo']}|{h['tipo']}|{h['ini']}": h for h in ler("mi_mapa_hist.json")}   # histórico do mapa (backtest diário)
    for a, (etf, idx) in FONTE.items():
        if a not in P: continue
        iv = None; fonte = ""
        if idx:
            try: iv = last(closes(yahoo(idx, 0.1))); fonte = "índice " + idx.strip("^") + " (Cboe)"
            except Exception: pass
        c = closes(P[a]); px = c[max(c)]; casas = ATIVOS[a][1]
        if iv is None:   # moedas: opções dos ETFs são pouco negociadas → vol. realizada de 21 dias × 1,09 (testado 2016+: ±1σ 72–73%, ±2σ 93–95%)
            ks_ = sorted(c)[-22:]; r_ = [math.log(c[ks_[i]] / c[ks_[i - 1]]) for i in range(1, len(ks_))]
            iv = st.stdev(r_) * math.sqrt(252) * 100 * 1.09; fonte = "vol. realizada de 21 dias + prêmio típico (testada)"
        fx = []
        for n, nome in ((1, "dia"), (5, "semana"), (21, "mês")):
            sd = iv / 100 * math.sqrt(n / 252)
            fx.append({"prazo": nome, "pct": rnd(sd * 100, 2),
                       "s1": [rnd(px * math.exp(-sd), casas), rnd(px * math.exp(sd), casas)],
                       "s2": [rnd(px * math.exp(-2 * sd), casas), rnd(px * math.exp(2 * sd), casas)]})
        row = {"ativo": a, "preco": rnd(px, casas), "iv": rnd(iv, 2), "fonte": fonte, "faixas": fx, "validado": True}
        # nível da vol.: compara com a média de 1, 3 e 5 anos (peso 50/30/20). Ouro: do próprio GVZ; moedas: vol. realizada × 1,1 (prêmio típico)
        try:
            if idx: g = closes(yahoo(idx, 5)); ref = "GVZ"
            else:
                ks_ = sorted(c); g = {}
                for i_ in range(22, len(ks_)):
                    if i_ % 5: continue
                    r_ = [math.log(c[ks_[k]] / c[ks_[k - 1]]) for k in range(i_ - 20, i_ + 1)]
                    g[ks_[i_]] = st.stdev(r_) * math.sqrt(252) * 100 * 1.1
                ref = "vol. realizada + prêmio típico"
            fim_ = max(g); med = {}
            for n_ in (1, 3, 5):
                v_ = [v for d, v in g.items() if d >= fim_ - dt.timedelta(days=365 * n_)]
                if v_: med[n_] = st.mean(v_)
            media = sum(med[n_] * w for n_, w in ((1, .5), (3, .3), (5, .2)) if n_ in med) / sum(w for n_, w in ((1, .5), (3, .3), (5, .2)) if n_ in med)
            q = iv / media
            row["nivel"] = {"media": rnd(media, 1), "m1": rnd(med.get(1), 1), "m3": rnd(med.get(3), 1), "m5": rnd(med.get(5), 1), "ref": ref, "razao": rnd(q, 2),
                            "txt": "bem acima do normal" if q >= 1.25 else "acima do normal" if q >= 1.1 else "bem abaixo do normal" if q <= 0.8 else "abaixo do normal" if q <= 0.9 else "normal"}
        except Exception: pass
        if a == "XAUUSD":   # vol. implícita da CME: straddle no dinheiro (ajuste do pregão anterior) → σ ≈ straddle ÷ (0,8 × F × √T)
            try:
                cad = [o for o in ler("ouro_cadeia.json") if o.get("settle") not in (None, "") and len(str(o.get("venc"))) == 10]
                melhor = None
                for v in sorted({o["venc"] for o in cad}):
                    ln = [o for o in cad if o["venc"] == v]; pg = dt.date.fromisoformat(ln[0]["data_pregao"]); d = (dt.date.fromisoformat(v) - pg).days
                    if d < 3: continue
                    F = float(ln[0]["futuro"]); ks = {}
                    for o in ln: ks.setdefault(float(o["strike"]), {})[str(o["tipo"])[0]] = float(o["settle"])
                    k = min((k for k in ks if "C" in ks[k] and "P" in ks[k]), key=lambda k: abs(k - F), default=None)
                    if k is not None: melhor = (v, pg, d, F, ks[k]["C"] + ks[k]["P"]); break
                if melhor:
                    v, pg, d, F, st_ = melhor; ivc = st_ / (0.798 * F * math.sqrt(d / 365)) * 100
                    row["cme"] = {"iv": rnd(ivc, 2), "pregao": pg.isoformat(), "venc": v, "faixas": [
                        {"prazo": f["prazo"], "pct": rnd(ivc / 100 * math.sqrt(n / 252) * 100, 2),
                         "s1": [rnd(px * math.exp(-ivc / 100 * math.sqrt(n / 252)), casas), rnd(px * math.exp(ivc / 100 * math.sqrt(n / 252)), casas)],
                         "s2": [rnd(px * math.exp(-2 * ivc / 100 * math.sqrt(n / 252)), casas), rnd(px * math.exp(2 * ivc / 100 * math.sqrt(n / 252)), casas)]}
                        for f, n in zip(fx, (1, 5, 21))]}
            except Exception as e: STATUS.append({"bloco": "Faixa CME (ouro)", "ok": False, "msg": str(e)[:120]})
        # aberturas do dia (17h NY) e da semana, e máxima/mínima desde então, para o mapa de probabilidades
        try:
            j = json.loads(get(f"https://query2.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(ATIVOS[a][0])}?range=10d&interval=1h"))["chart"]["result"][0]
            q = j["indicators"]["quote"][0]; NYz = ZoneInfo("America/New_York")
            bars = [(dt.datetime.fromtimestamp(t, NYz), o, h, l) for t, o, h, l in zip(j["timestamp"], q["open"], q["high"], q["low"]) if o and h and l]
            sess = lambda d: (d + dt.timedelta(hours=7)).date()   # dia de negociação começa 17h NY
            hoje_s = sess(bars[-1][0]); dia = [b for b in bars if sess(b[0]) == hoje_s]
            seg = hoje_s - dt.timedelta(days=hoje_s.weekday()); sem = [b for b in bars if sess(b[0]) >= seg]
            # σ congelado na 1ª coleta da sessão (dia) e da semana: os níveis são projetados na abertura e não mudam até a próxima
            kd, kw = f"{a}|{hoje_s}", f"{a}|{seg}"
            if kd not in FIXO: FIXO[kd] = {"sd": iv / 100 / math.sqrt(252), "em": NOW.strftime("%d/%m %H:%M")}
            if kw not in FIXO: FIXO[kw] = {"sd": iv / 100 / math.sqrt(252) * math.sqrt(5), "em": NOW.strftime("%d/%m %H:%M")}
            sd = FIXO[kd]["sd"]
            hab = 18 if a == "XAUUSD" else 17   # ouro: a CME reabre às 18h de NY; moedas viram o dia às 17h
            hb = lambda d: dt.datetime.combine(d, dt.time(hab), NYz).astimezone(BRT).strftime("%a %d/%m %Hh").replace("Mon", "seg").replace("Tue", "ter").replace("Wed", "qua").replace("Thu", "qui").replace("Fri", "sex").replace("Sat", "sáb").replace("Sun", "dom")
            row["mapa"] = {"sd_dia": rnd(sd, 6), "sd_sem": rnd(FIXO[kw]["sd"], 6), "proj_dia": FIXO[kd]["em"], "proj_sem": FIXO[kw]["em"],
                           "dia_ini": hb(hoje_s - dt.timedelta(days=3 if hoje_s.weekday() == 0 else 1)), "dia_fim": hb(hoje_s),
                           "sem_ini": hb(seg - dt.timedelta(days=1)),
                           "sem_fim": dt.datetime.combine(seg + dt.timedelta(days=4), dt.time(17), NYz).astimezone(BRT).strftime("sex %d/%m %Hh"),   # fechamento de sexta (17h NY) para todos
                           "ab_dia": rnd(dia[0][1], casas), "max_dia": rnd(max(b[2] for b in dia), casas), "min_dia": rnd(min(b[3] for b in dia), casas),
                           "ab_sem": rnd(sem[0][1], casas), "max_sem": rnd(max(b[2] for b in sem), casas), "min_sem": rnd(min(b[3] for b in sem), casas),
                           # horários (ms) de início e fim, para a chance "agora" (preço atual e tempo que falta)
                           "ts_dia_ini": int(dt.datetime.combine(hoje_s - dt.timedelta(days=3 if hoje_s.weekday() == 0 else 1), dt.time(hab), NYz).timestamp() * 1000),
                           "ts_dia_fim": int(dt.datetime.combine(hoje_s, dt.time(hab), NYz).timestamp() * 1000),
                           "ts_sem_ini": int(dt.datetime.combine(seg - dt.timedelta(days=1), dt.time(hab), NYz).timestamp() * 1000),
                           "ts_sem_fim": int(dt.datetime.combine(seg + dt.timedelta(days=4), dt.time(17), NYz).timestamp() * 1000),
                           "preco": rnd(px, casas)}
            mp = row["mapa"]
            MH[f"{a}|dia|{hoje_s}"] = {"ativo": a, "tipo": "dia", "ini": str(hoje_s), "ab": mp["ab_dia"], "sd": mp["sd_dia"], "max": mp["max_dia"], "min": mp["min_dia"]}
            MH[f"{a}|sem|{seg}"] = {"ativo": a, "tipo": "sem", "ini": str(seg), "ab": mp["ab_sem"], "sd": mp["sd_sem"], "max": mp["max_sem"], "min": mp["min_sem"]}
        except Exception as e: STATUS.append({"bloco": "Mapa " + a, "ok": False, "msg": str(e)[:120]})
        rows.append(row)
        hist[(a, NOW.date().isoformat())] = {"ativo": a, "data": NOW.date().isoformat(), "iv": rnd(iv, 2), "preco": rnd(px, casas)}
    if not rows: raise ValueError("sem volatilidade")
    save("mapa_fixo.json", [dict(sorted(FIXO.items())[-200:])])
    save("mi_mapa_hist.json", sorted(MH.values(), key=lambda h: (h["ini"], h["ativo"], h["tipo"]))[-6000:])
    save("mi_faixa.json", rows)
    save("mi_faixa_hist.json", sorted(hist.values(), key=lambda h: (h["ativo"], h["data"]))[-4000:])
b_faixa()


@bloco("0DTE ouro (GLD)")
def b_0dte():
    # opções do GLD que vencem hoje (ou no próximo pregão): faixa do dia pelo straddle, paredes, gamma flip e max pain,
    # convertidos para o preço do ouro (XAUUSD). Grava um retrato por dia para validar depois.
    NY = ZoneInfo("America/New_York"); ny = NOW.astimezone(NY)
    j = json.loads(get("https://cdn.cboe.com/api/global/delayed_quotes/options/GLD.json"))["data"]
    S = j["current_price"]; ops = []
    for x in j["options"]:
        o = x["option"]; ops.append({"venc": dt.date(2000 + int(o[3:5]), int(o[5:7]), int(o[7:9])), "tipo": o[9], "k": int(o[10:]) / 1000,
                                     "oi": x["open_interest"] or 0, "vol": x["volume"] or 0, "iv": x["iv"] or 0,
                                     "mid": ((x["bid"] or 0) + (x["ask"] or 0)) / 2, "delta": x.get("delta") or 0})
    hoje = ny.date() if ny.hour < 16 else ny.date() + dt.timedelta(days=1)
    venc = min(v for v in {o["venc"] for o in ops} if v >= hoje)
    ch = [o for o in ops if o["venc"] == venc]
    fim = dt.datetime.combine(venc, dt.time(16), NY); T = max((fim - ny).total_seconds(), 1800) / (365 * 86400)
    def gama(Sx, o):
        if o["iv"] <= 0: return 0
        d1 = (math.log(Sx / o["k"]) + o["iv"] ** 2 / 2 * T) / (o["iv"] * math.sqrt(T))
        return math.exp(-d1 * d1 / 2) / math.sqrt(2 * math.pi) / (Sx * o["iv"] * math.sqrt(T))
    def gex(Sx):   # convenção de mercado: dealers vendidos em puts e comprados em calls dos clientes → call +, put −
        return sum((1 if o["tipo"] == "C" else -1) * gama(Sx, o) * (o["oi"] + o["vol"]) * 100 * Sx * Sx * 0.01 for o in ch)
    grade = [S * (1 + i / 1000) for i in range(-40, 41)]; g = [gex(x) for x in grade]
    flip = None
    for i in range(1, len(grade)):
        if (g[i - 1] < 0) != (g[i] < 0): flip = grade[i] if flip is None or abs(grade[i] - S) < abs(flip - S) else flip
    ks = sorted({o["k"] for o in ch}); atm = min(ks, key=lambda k: abs(k - S))
    strad = sum(o["mid"] for o in ch if o["k"] == atm)
    def peso(tp): 
        m = {}
        for o in ch:
            if o["tipo"] == tp: m[o["k"]] = m.get(o["k"], 0) + o["oi"] + o["vol"]
        return m
    cw, pw = peso("C"), peso("P")
    dor = {k: sum(max(0, k - o["k"]) * o["oi"] for o in ch if o["tipo"] == "C") + sum(max(0, o["k"] - k) * o["oi"] for o in ch if o["tipo"] == "P") for k in ks}
    c = closes(P["XAUUSD"]); ouro = c[max(c)]; r = ouro / S
    conv = lambda v: rnd(v * r, 1) if v is not None else None
    lado = lambda m, f: max((k for k in m if f(k) and abs(k / S - 1) <= 0.03), key=lambda k: m[k], default=None)
    row = {"vencimento": venc.isoformat(), "atualizado": ny.strftime("%H:%M") + " NY", "gld": rnd(S, 2), "ouro": rnd(ouro, 1),
           "contratos_hoje": int(sum(o["vol"] for o in ch)), "abertos": int(sum(o["oi"] for o in ch)),
           "faixa_pct": rnd(strad / S * 100, 2), "faixa": [conv(S - strad), conv(S + strad)],
           "s1": [conv(S - 1.25 * strad), conv(S + 1.25 * strad)],   # straddle ≈ 0,8σ → 1σ ≈ 1,25 × straddle
           "call_wall": conv(lado(cw, lambda k: k >= S)), "put_wall": conv(lado(pw, lambda k: k <= S)),
           "gamma_flip": conv(flip), "max_pain": conv(min(dor, key=dor.get)) if dor else None,
           "regime": "gamma positivo (mercado tende a segurar/voltar)" if gex(S) > 0 else "gamma negativo (movimentos tendem a acelerar)",
           "perfil": [[conv(k), int(cw.get(k, 0)), int(pw.get(k, 0))] for k in ks if abs(k / S - 1) <= 0.03],
           "perfil_oi": [[conv(k), int(sum(o["oi"] for o in ch if o["k"] == k and o["tipo"] == "C")), int(sum(o["oi"] for o in ch if o["k"] == k and o["tipo"] == "P"))] for k in ks if abs(k / S - 1) <= 0.03],
           "perfil_vol": [[conv(k), int(sum(o["vol"] for o in ch if o["k"] == k and o["tipo"] == "C")),
                           int(sum(o["vol"] for o in ch if o["k"] == k and o["tipo"] == "P"))] for k in ks if abs(k / S - 1) <= 0.03]}
    # mesma análise com as opções de ouro da CME do mesmo vencimento (contratos em aberto do fechamento anterior, tarefa noturna)
    # mesma análise com as opções de ouro da CME do mesmo vencimento (ajuste e contratos em aberto do pregão anterior, PDF do boletim)
    cme = [o for o in ler("ouro_cadeia.json") if str(o.get("venc")) == venc.isoformat() and o.get("settle") not in (None, "")]
    if cme:
        try:
            fut = float(cme[0].get("futuro") or ouro); pg = dt.date.fromisoformat(cme[0]["data_pregao"])
            # strikes da CME estão no preço do futuro de dezembro: converte para o ouro à vista pelo custo de carregar até o vencimento do futuro
            try: r13 = next(x["valor"] for x in ler("mi_dolar.json") if x["serie"].startswith("EUA 13")) / 100
            except Exception: r13 = 0.04
            vf = dt.date(pg.year + (pg.month == 12), 12, 29) if pg.month < 12 or pg.day < 26 else dt.date(pg.year + 1, 2, 24)
            base = 1 / (1 + r13 * max((vf - pg).days, 1) / 365)
            cv = lambda k: rnd(k * base, 1) if k is not None else None
            cc, pp, setl = {}, {}, {}
            for o in cme:
                k = float(o["strike"]); c = str(o["tipo"]).startswith("C")
                (cc if c else pp)[k] = (cc if c else pp).get(k, 0) + (o.get("oi") or 0); setl[(k, "C" if c else "P")] = float(o["settle"])
            kk = sorted(set(cc) | set(pp))
            dor2 = {k: sum(max(0, k - x) * n for x, n in cc.items()) + sum(max(0, x - k) * n for x, n in pp.items()) for k in kk}
            sp = ouro / base   # ouro à vista levado para a escala do futuro
            perto = lambda m, f: max((k for k in m if f(k) and m[k] > 0 and abs(k / fut - 1) <= 0.03), key=lambda k: m[k], default=None)
            # faixa do dia: straddle no dinheiro do ajuste anterior (vale para o dia inteiro do vencimento)
            atm = min((k for k in kk if (k, "C") in setl and (k, "P") in setl), key=lambda k: abs(k - fut), default=None)
            strad = setl[(atm, "C")] + setl[(atm, "P")] if atm else None
            # gamma flip: vol. implícita de cada opção pelo ajuste (Black-76) e exposição dos bancos com os contratos em aberto
            fimv = dt.datetime.combine(venc, dt.time(13, 30), NY); T0 = max((fimv - dt.datetime.combine(pg, dt.time(13, 30), NY)).total_seconds(), 3600) / (365 * 86400)
            Nn = st.NormalDist()
            def b76(K, cp, prem):
                lo, hi = 0.01, 3.0
                for _ in range(50):
                    sg = (lo + hi) / 2; d1 = (math.log(fut / K) + sg * sg * T0 / 2) / (sg * math.sqrt(T0)); d2 = d1 - sg * math.sqrt(T0)
                    pr = fut * Nn.cdf(d1) - K * Nn.cdf(d2) if cp == "C" else K * Nn.cdf(-d2) - fut * Nn.cdf(-d1)
                    lo, hi = (sg, hi) if pr < prem else (lo, sg)
                return sg
            opc = [(k, cp, n, b76(k, cp, setl[(k, cp)])) for cp, m in (("C", cc), ("P", pp)) for k, n in m.items() if n > 0 and (k, cp) in setl and setl[(k, cp)] > 0.1]
            Tn = max((fimv - ny).total_seconds(), 1800) / (365 * 86400)
            def gx(S):
                tot = 0
                for k, cp, n, iv in opc:
                    d1 = (math.log(S / k) + iv * iv / 2 * Tn) / (iv * math.sqrt(Tn)); tot += (1 if cp == "C" else -1) * math.exp(-d1 * d1 / 2) / (S * iv * math.sqrt(Tn)) * n
                return tot
            gr = [sp * (1 + i / 1000) for i in range(-40, 41)]; gv = [gx(x) for x in gr]; flip2 = None
            for i in range(1, len(gr)):
                if (gv[i - 1] < 0) != (gv[i] < 0): flip2 = gr[i] if flip2 is None or abs(gr[i] - sp) < abs(flip2 - sp) else flip2
            row["cme"] = {"pregao": pg.isoformat(), "abertos": int(sum(cc.values()) + sum(pp.values())), "futuro": fut, "base": rnd(fut - fut * base, 1),
                          "call_wall": cv(perto(cc, lambda k: k >= sp)), "put_wall": cv(perto(pp, lambda k: k <= sp)),
                          "max_pain": cv(min(dor2, key=dor2.get)) if dor2 else None, "gamma_flip": cv(flip2),
                          "faixa": [cv(fut - strad), cv(fut + strad)] if strad else None, "faixa_pct": rnd(strad / fut * 100, 2) if strad else None,
                          "s1": [cv(fut - 1.25 * strad), cv(fut + 1.25 * strad)] if strad else None,
                          "regime": ("gamma positivo" if gx(sp) > 0 else "gamma negativo") if opc else None,
                          # contratos em aberto por strike (convertido para o à vista), para as barras de "em aberto" do gráfico
                          "perfil": [[cv(k), int(cc.get(k, 0)), int(pp.get(k, 0))] for k in kk if abs(k / fut - 1) <= 0.03 and (cc.get(k, 0) or pp.get(k, 0))]}
        except Exception as e: STATUS.append({"bloco": "0DTE CME", "ok": False, "msg": str(e)[:120]})
    save("mi_0dte.json", [row])
    # histórico do dia (um ponto por coleta) para o gráfico; zera quando muda o vencimento
    # só pontos do PRÓPRIO dia do vencimento (antes, depois das 16h o vencimento seguinte recebia pontos da tarde anterior)
    dia = [d for d in ler("mi_0dte_dia.json") if d.get("v") == row["vencimento"] and d.get("d", row["vencimento"]) == row["vencimento"] and (d.get("d") or d.get("t", "") < "16:00")]
    if ny.date().isoformat() == row["vencimento"] and 9 * 60 + 30 <= ny.hour * 60 + ny.minute <= 16 * 60 + 15 and ny.weekday() < 5 and not any(d.get("t") == ny.strftime("%H:%M") for d in dia):
        dia.append({"v": row["vencimento"], "d": ny.date().isoformat(), "t": ny.strftime("%H:%M"), "p": row["ouro"], "cw": row["call_wall"], "pw": row["put_wall"],
                    "gf": row["gamma_flip"], "mp": row["max_pain"], "s1": row["s1"]})
    dia.sort(key=lambda d: d.get("t", ""))
    save("mi_0dte_dia.json", dia[-200:] or [{"v": row["vencimento"]}])
    hist = {h["vencimento"]: h for h in ler("mi_0dte_hist.json")}
    h = hist.get(row["vencimento"]) or {k: row[k] for k in ("vencimento", "faixa", "faixa_pct", "call_wall", "put_wall", "gamma_flip", "max_pain", "regime")}
    h["ultimo_ouro"] = row["ouro"]   # o primeiro retrato do dia fica; o preço vai sendo atualizado até o vencimento
    if row.get("cme") and "cme" not in h:   # retrato da CME do mesmo vencimento, para comparar qual fonte acerta mais
        h["cme"] = {k: row["cme"].get(k) for k in ("faixa", "faixa_pct", "call_wall", "put_wall", "gamma_flip", "max_pain", "pregao")}
    hist[row["vencimento"]] = h
    save("mi_0dte_hist.json", sorted(hist.values(), key=lambda x: x["vencimento"])[-500:])
    # put/call diário (volume e contratos em aberto, total e de curto prazo) do GLD e da CME, para testar se antecipa direção.
    # Um registro por pregão; a última coleta do dia sobrescreve (volume do dia completo). Teste após ~6 meses.
    def pc(lst):
        f = lambda tp, k: sum(o[k] for o in lst if o["tipo"] == tp)
        cv, pv, co, po = f("C", "vol"), f("P", "vol"), f("C", "oi"), f("P", "oi")
        return {"c_vol": int(cv), "p_vol": int(pv), "c_oi": int(co), "p_oi": int(po),
                "pcr_vol": rnd(pv / cv, 3) if cv else None, "pcr_oi": rnd(po / co, 3) if co else None}
    if ny.weekday() < 5 and 9 * 60 + 30 <= ny.hour * 60 + ny.minute <= 16 * 60 + 15:   # até o fechamento: preço = fechamento
        d0 = ny.date()
        rec = {"data": d0.isoformat(), "hora": ny.strftime("%H:%M"), "gld": rnd(S, 2), "ouro": rnd(ouro, 1),
               "gld_total": pc(ops), "gld_0dte": pc([o for o in ops if o["venc"] == d0]),
               "gld_7d": pc([o for o in ops if 0 <= (o["venc"] - d0).days <= 7]),
               "gld_30d": pc([o for o in ops if 0 <= (o["venc"] - d0).days <= 30])}
        # skew 25-delta (vol. da put 25Δ − vol. da call 25Δ, em pontos) do vencimento mais perto de 30 dias
        vs = [v for v in {o["venc"] for o in ops} if (v - d0).days >= 7]
        if vs:
            v30 = min(vs, key=lambda v: abs((v - d0).days - 30)); s30 = [o for o in ops if o["venc"] == v30 and o["iv"] > 0 and o["delta"]]
            pc25 = min((o for o in s30 if o["tipo"] == "P"), key=lambda o: abs(abs(o["delta"]) - 0.25), default=None)
            cc25 = min((o for o in s30 if o["tipo"] == "C"), key=lambda o: abs(o["delta"] - 0.25), default=None)
            if pc25 and cc25: rec["gld_skew25"] = {"venc": v30.isoformat(), "skew": rnd((pc25["iv"] - cc25["iv"]) * 100, 2),
                                                   "iv_put": rnd(pc25["iv"] * 100, 2), "iv_call": rnd(cc25["iv"] * 100, 2)}
        cad = ler("ouro_cadeia.json")
        if cad:   # CME (tarefa noturna): séries de 0–2 dias úteis + 1ª semanal, pregão anterior
            cm = [{"tipo": str(o.get("tipo", ""))[:1].upper(), "oi": float(o.get("oi") or 0),
                   "vol": float(o.get("volume") or o.get("vol") or 0)} for o in cad]
            rec["cme_curto"] = pc(cm) | {"pregao": cad[0].get("data_pregao")}
            try:   # skew 25Δ da CME na 1ª semanal (≥ 3 dias): vol. implícita pelo settle (Black-76)
                pg = dt.date.fromisoformat(cad[0]["data_pregao"])
                v = min(o["venc"] for o in cad if (dt.date.fromisoformat(o["venc"]) - pg).days >= 3)
                ln = [o for o in cad if o["venc"] == v and o.get("delta") not in (None, "") and o.get("settle") not in (None, "")]
                T = (dt.date.fromisoformat(v) - pg).days / 365; F = float(ln[0]["futuro"])
                def b76(K, cp, prem):
                    lo, hi = 0.01, 3.0
                    for _ in range(60):
                        sg = (lo + hi) / 2; d1 = (math.log(F / K) + sg * sg * T / 2) / (sg * math.sqrt(T)); d2 = d1 - sg * math.sqrt(T); N = st.NormalDist().cdf
                        pr = F * N(d1) - K * N(d2) if cp == "C" else K * N(-d2) - F * N(-d1)
                        lo, hi = (sg, hi) if pr < prem else (lo, sg)
                    return sg * 100
                pp_ = min((o for o in ln if str(o["tipo"])[0].upper() == "P"), key=lambda o: abs(abs(float(o["delta"])) - 0.25))
                cc_ = min((o for o in ln if str(o["tipo"])[0].upper() == "C"), key=lambda o: abs(abs(float(o["delta"])) - 0.25))
                ip, ic = b76(float(pp_["strike"]), "P", float(pp_["settle"])), b76(float(cc_["strike"]), "C", float(cc_["settle"]))
                rec["cme_skew25"] = {"venc": v, "skew": rnd(ip - ic, 2), "iv_put": rnd(ip, 2), "iv_call": rnd(ic, 2)}
            except Exception: pass
        ph = {h["data"]: h for h in ler("mi_pcr_hist.json")}; ph[rec["data"]] = rec
        save("mi_pcr_hist.json", sorted(ph.values(), key=lambda x: x["data"])[-2000:])
b_0dte()

@bloco("Backtest diário")
def b_valid():
    # confere o que o painel projetou contra o que aconteceu: toque dos níveis do mapa, faixa das opções e 0DTE
    tb = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "data", "toque_tabela.json")))
    hoje = NOW.astimezone(ZoneInfo("America/New_York")); hs = (hoje + dt.timedelta(hours=7)).date(); seg = hs - dt.timedelta(days=hs.weekday())
    mh = ler("mi_mapa_hist.json"); out = {"atualizado": NOW.strftime("%d/%m %H:%M"), "mapa": [], "faixa": [], "zdte": None}
    for a in [x for x in tb if not x.startswith("_")]:
        for tp in ("dia", "sem"):
            fe = [h for h in mh if h["ativo"] == a and h["tipo"] == tp and h["sd"] and dt.date.fromisoformat(h["ini"]) < (hs if tp == "dia" else seg)]
            if not fe: continue
            nv = []
            for x in (0.5, 1, 1.5, 2):
                i = tb[a]["k"].index(x)
                nv.append({"k": x, "prev_cima": tb[a][tp + "_toca_cima"][i], "prev_baixo": tb[a][tp + "_toca_baixo"][i],
                           "real_cima": rnd(100 * sum(h["max"] >= h["ab"] * math.exp(x * h["sd"]) for h in fe) / len(fe), 0),
                           "real_baixo": rnd(100 * sum(h["min"] <= h["ab"] * math.exp(-x * h["sd"]) for h in fe) / len(fe), 0)})
            out["mapa"].append({"ativo": a, "tipo": tp, "n": len(fe), "desde": min(h["ini"] for h in fe), "niveis": nv})
    fh = ler("mi_faixa_hist.json")
    for a in sorted({h["ativo"] for h in fh}):
        h = [x for x in fh if x["ativo"] == a and x.get("iv")]; d1 = d2 = n = 0
        for p, q in zip(h, h[1:]):
            if (dt.date.fromisoformat(q["data"]) - dt.date.fromisoformat(p["data"])).days > 4: continue
            z = abs(math.log(q["preco"] / p["preco"])) / (p["iv"] / 100 / math.sqrt(252)); n += 1; d1 += z <= 1; d2 += z <= 2
        if n: out["faixa"].append({"ativo": a, "n": n, "dentro_1s": rnd(100 * d1 / n, 0), "dentro_2s": rnd(100 * d2 / n, 0), "teorico": [68, 95]})
    zh = [z for z in ler("mi_0dte_hist.json") if z["vencimento"] < hoje.date().isoformat() and z.get("ultimo_ouro") and z.get("faixa")]
    if zh:
        dentro = sum(z["faixa"][0] <= z["ultimo_ouro"] <= z["faixa"][1] for z in zh)
        par = [z for z in zh if z.get("put_wall") and z.get("call_wall")]
        zc = [z for z in zh if (z.get("cme") or {}).get("faixa")]
        if zc:   # mesma conferência com a faixa e as paredes da CME
            pc = [z for z in zc if z["cme"].get("put_wall") and z["cme"].get("call_wall")]
            out["zdte_cme"] = {"n": len(zc), "dentro_faixa": rnd(100 * sum(z["cme"]["faixa"][0] <= z["ultimo_ouro"] <= z["cme"]["faixa"][1] for z in zc) / len(zc), 0),
                               "entre_paredes": rnd(100 * sum(z["cme"]["put_wall"] <= z["ultimo_ouro"] <= z["cme"]["call_wall"] for z in pc) / len(pc), 0) if pc else None}
        out["zdte"] = {"n": len(zh), "dentro_faixa": rnd(100 * dentro / len(zh), 0),
                       "entre_paredes": rnd(100 * sum(z["put_wall"] <= z["ultimo_ouro"] <= z["call_wall"] for z in par) / len(par), 0) if par else None}
    save("mi_validacao.json", [out])
b_valid()

# ---------------------------------------------------------------- Fear & Greed (CNN)
@bloco("Fear & Greed (CNN)")
def b_fg():
    j = json.loads(get("https://production.dataviz.cnn.io/index/fearandgreed/graphdata", {"Referer": "https://edition.cnn.com/", "Origin": "https://edition.cnn.com"}))
    f = j["fear_and_greed"]
    FG.update({"fg": rnd(f["score"], 0), "fg_txt": f.get("rating"), "fg_ontem": rnd(f.get("previous_close"), 0),
               "fg_semana": rnd(f.get("previous_1_week"), 0), "fg_mes": rnd(f.get("previous_1_month"), 0), "fg_ano": rnd(f.get("previous_1_year"), 0)})
FG = {}
b_fg()

# ---------------------------------------------------------------- agenda red folder
@bloco("Agenda econômica (Forex Factory)")
def b_agenda():
    rows = []
    urls = {}
    try:
        for ev in ET.fromstring(get("https://nfs.faireconomy.media/ff_calendar_thisweek.xml")).iter("event"):
            urls[(ev.findtext("title"), ev.findtext("country"), ev.findtext("date"))] = (ev.findtext("url") or "").strip()
    except Exception: pass
    for u in ("https://nfs.faireconomy.media/ff_calendar_thisweek.json",):
        for e in json.loads(get(u)):
            d0 = dt.datetime.fromisoformat(e["date"]); e["url"] = urls.get((e.get("title"), e.get("country"), d0.strftime("%m-%d-%Y")), "")
            if e.get("country") not in ("USD", "EUR", "GBP", "JPY", "CHF") or e.get("impact") not in ("High", "Medium"): continue
            t = dt.datetime.fromisoformat(e["date"]).astimezone(BRT)
            rows.append({"quando": t.strftime("%Y-%m-%d %H:%M"), "data": t.date().isoformat(), "hora": t.strftime("%H:%M"), "moeda": e["country"],
                         "evento": e["title"], "impacto": "Alto" if e["impact"] == "High" else "Médio",
                         "previsao": e.get("forecast") or "", "anterior": e.get("previous") or "", "url": e.get("url") or ""})
    rows.sort(key=lambda r: r["quando"])
    save("mi_agenda.json", rows)
b_agenda()

# ---------------------------------------------------------------- "Atual" oficial dos EUA (reserva do biquote)
# BLS (payroll, desemprego, salário-hora, CPI, PPI) e FRED (seguro-desemprego, varejo, PCE, JOLTS, PIB).
# A API do BLS sem chave aceita 25 consultas/dia: só consulta perto de divulgações americanas.
EUA_BLS = {  # evento do Forex Factory: (série, cálculo, unidade, casas)
    "Non-Farm Employment Change": ("CES0000000001", "diff", "K", 0), "Unemployment Rate": ("LNS14000000", "lvl", "%", 1),
    "Average Hourly Earnings m/m": ("CES0500000003", "pct", "%", 1), "CPI m/m": ("CUSR0000SA0", "pct", "%", 1),
    "Core CPI m/m": ("CUSR0000SA0L1E", "pct", "%", 1), "CPI y/y": ("CUUR0000SA0", "yoy", "%", 1),
    "PPI m/m": ("WPSFD4", "pct", "%", 1), "Core PPI m/m": ("WPSFD49104", "pct", "%", 1)}
EUA_FRED = {
    "Unemployment Claims": ("ICSA", "lvl", "K", 0, 1e-3), "Retail Sales m/m": ("RSAFS", "pct", "%", 1, 1),
    "Core Retail Sales m/m": ("RSFSXMV", "pct", "%", 1, 1), "Core PCE Price Index m/m": ("PCEPILFE", "pct", "%", 1, 1),
    "JOLTS Job Openings": ("JTSJOL", "lvl", "M", 2, 1e-3), "Advance GDP q/q": ("A191RL1Q225SBEA", "lvl", "%", 1, 1)}
def _calc(serie, modo):   # serie: [(periodo, valor)] em ordem
    (p1, v1) = serie[-1]
    if modo == "lvl": return p1, v1
    if modo == "diff": return p1, v1 - serie[-2][1]
    if modo == "pct": return p1, (v1 / serie[-2][1] - 1) * 100
    if modo == "yoy": return p1, (v1 / serie[-13][1] - 1) * 100

@bloco("Atual oficial EUA (BLS/FRED)")
def b_eua():
    ant = ler("mi_eua.json")
    perto = any(r["moeda"] == "USD" and -15 <= (NOW - dt.datetime.fromisoformat(r["quando"] + ":00-03:00")).total_seconds() / 60 <= 240
                for r in ler("mi_agenda.json"))
    if ant and not perto: return   # fora da janela: mantém o arquivo anterior
    rows = {r["evento"]: r for r in ant}
    try:
        req = urllib.request.Request("https://api.bls.gov/publicAPI/v1/timeseries/data/", data=json.dumps({"seriesid": sorted({v[0] for v in EUA_BLS.values()})}).encode(),
                                     headers={"Content-Type": "application/json", "User-Agent": "painel-mercado"})
        with urllib.request.urlopen(req, timeout=TIMEOUT_REQ) as r: js = json.loads(r.read())
        if js.get("status") != "REQUEST_SUCCEEDED": raise ValueError("; ".join(js.get("message", []))[:200])
        por = {}
        for sr in js.get("Results", {}).get("series", []):
            pts = sorted((f"{d['year']}-{d['period'][1:]}", float(d["value"])) for d in sr["data"] if d["period"].startswith("M") and d["period"] != "M13" and d["value"] not in ("-", ""))
            por[sr["seriesID"]] = pts
        for ev, (sid, modo, un, cs) in EUA_BLS.items():
            if len(por.get(sid, [])) >= 14:
                p1, v = _calc(por[sid], modo); rows[ev] = {"evento": ev, "periodo": p1, "valor": round(v, 3), "unidade": un, "casas": cs, "fonte": "BLS"}
    except Exception as e:
        STATUS.append({"bloco": "BLS", "ok": False, "msg": str(e)[:200]})
    ini = (NOW.date() - dt.timedelta(days=500)).isoformat()
    for ev, (sid, modo, un, cs, esc) in EUA_FRED.items():
        try:
            pts = sorted(fred([sid], ini)[sid].items())
            p1, v = _calc([(d.isoformat()[:7] if modo != "lvl" or un != "K" else d.isoformat(), x) for d, x in pts], modo)
            if modo == "lvl": v = v * esc
            rows[ev] = {"evento": ev, "periodo": p1, "valor": round(v, 3), "unidade": un, "casas": cs, "fonte": "FRED"}
        except Exception as e:
            STATUS.append({"bloco": "FRED: " + sid, "ok": False, "msg": str(e)[:120]})
    save("mi_eua.json", list(rows.values()))
b_eua()

@bloco("Histórico de surpresas (EUA)")
def b_surpresa():
    # grava previsão, anterior e resultado de cada dado americano de alto impacto, para testar depois se dá para
    # prever o lado da surpresa (acima/abaixo da previsão). Não aparece no painel.
    h = {(r["data"], r["evento"]): r for r in ler("mi_surpresa_hist.json")}
    eua = {r["evento"]: r for r in ler("mi_eua.json")}
    for r in ler("mi_agenda.json"):
        if r["moeda"] != "USD" or r["impacto"] != "Alto": continue
        k = (r["data"], r["evento"]); x = h.setdefault(k, {"data": r["data"], "hora": r["hora"], "evento": r["evento"]})
        if r.get("previsao"): x["previsao"] = r["previsao"]
        if r.get("anterior"): x["anterior"] = r["anterior"]
        quando = dt.datetime.fromisoformat(r["quando"] + ":00-03:00")
        if "atual" not in x and NOW >= quando + dt.timedelta(minutes=10) and r["evento"] in eua:   # resultado oficial (BLS/FRED)
            e = eua[r["evento"]]; x.update({"atual": e.get("valor"), "periodo": e.get("periodo"), "fonte": e.get("fonte"), "gravado": NOW.strftime("%Y-%m-%d %H:%M")})
    # nowcast de inflação do Fed de Cleveland (CPI/PCE): guarda o bruto 1× por dia para os eventos de inflação
    cl = ler("cleveland_nowcast.json"); hoje = NOW.date().isoformat()
    if not cl or cl[-1].get("data") != hoje:
        for u in ("https://www.clevelandfed.org/-/media/files/webcharts/inflationnowcasting/nowcast_month.json",
                  "https://www.clevelandfed.org/-/media/files/webcharts/inflationnowcasting/nowcast_quarter.json"):
            try: cl.append({"data": hoje, "url": u, "bruto": json.loads(get(u))}); break
            except Exception as e: erro = (u[-25:] + " " + str(e))[:120]
        else: cl.append({"data": hoje, "erro": erro}); STATUS.append({"bloco": "Nowcast Cleveland", "ok": False, "msg": erro})   # tenta de novo só amanhã
        save("cleveland_nowcast.json", cl[-30:])   # bruto: só 30 dias até definir o formato
    save("mi_surpresa_hist.json", sorted(h.values(), key=lambda x: (x["data"], x["hora"]))[-3000:])
b_surpresa()

# ---------------------------------------------------------------- notícias
@bloco("Notícias (RSS)")
def b_news():
    rows = []
    GN = "https://news.google.com/rss/search?q=" + urllib.parse.quote('forex OR "federal reserve" OR ECB OR "Bank of England" OR "Bank of Japan" OR "treasury yields" OR "gold price" OR nasdaq when:1d') + "&hl=en-US&gl=US&ceid=US:en"
    for fonte, u in (("MarketWatch", "https://feeds.content.dowjones.io/public/rss/mw_marketpulse"), ("FT", "https://www.ft.com/markets?format=rss"), ("Google News", GN),
                     ("Fed", "https://www.federalreserve.gov/feeds/press_all.xml"), ("BCE", "https://www.ecb.europa.eu/rss/press.html")):
        try:
            root = ET.fromstring(get(u))
            for it in root.iter("item"):
                tt = (it.findtext("title") or "").strip(); ln = (it.findtext("link") or "").strip(); pd = it.findtext("pubDate") or ""
                try: when = dt.datetime.strptime(pd.strip()[:25].strip(), "%a, %d %b %Y %H:%M:%S").replace(tzinfo=dt.timezone.utc).astimezone(BRT)
                except Exception: when = None
                if when and when < NOW - dt.timedelta(days=10 if fonte in ("Fed", "BCE") else 2): continue
                fo = fonte
                if fonte == "Google News" and " - " in tt: tt, fo = tt.rsplit(" - ", 1)
                rows.append({"fonte": fo, "titulo": tt, "link": ln, "quando": when.strftime("%Y-%m-%d %H:%M") if when else ""})
        except Exception as e:
            STATUS.append({"bloco": "Notícias: " + fonte, "ok": False, "msg": str(e)[:200]})
    rows.sort(key=lambda r: r["quando"], reverse=True)
    if not rows: raise ValueError("nenhum feed respondeu")
    seen = set(); uniq = []
    for r in rows:
        k = r["titulo"].lower()[:60]
        if k not in seen: seen.add(k); uniq.append(r)
    TAGS = {"Fed": ["fed ", "federal reserve", "powell", "fomc"], "BCE": ["ecb", "lagarde", "euro zone", "eurozone"], "BoE": ["bank of england", "boe", "bailey"],
            "BoJ": ["bank of japan", "boj", "ueda", "yen"], "SNB": ["snb", "swiss"], "Ouro": ["gold"], "Nasdaq": ["nasdaq", "tech stock", "chip", "nvidia", "ai stock"],
            "Juros": ["yield", "treasur", "bond"], "Dólar": ["dollar", "dxy"], "Euro": ["euro "], "Libra": ["pound", "sterling"], "Petróleo": ["oil", "crude", "opec", "brent"],
            "Dados": ["payroll", "cpi", "inflation", "jobs", "gdp", "pmi", "jobless", "retail sales"]}
    for r in uniq:
        t = " " + r["titulo"].lower() + " "
        r["tags"] = [k for k, ws in TAGS.items() if any(w in t for w in ws)]
    save("mi_noticias.json", uniq[:80])
b_news()

# ---------------------------------------------------------------- score 0-100 por ativo (regras transparentes)
PESOS = {"Tendência": 20, "Movimento de hoje": 10, "Juros (macro)": 20, "Dólar (DXY)": 15, "COT": 15, "Risco (VIX/F&G)": 10, "Sazonalidade": 5, "Valor justo": 5}
DOLAR = {"EURUSD": -1, "GBPUSD": -1, "XAUUSD": -1, "NAS100": -1, "USDJPY": 1, "USDCHF": 1}
RISCO = {"NAS100": -1, "USDJPY": -0.7, "USDCHF": -0.5, "GBPUSD": -0.3, "EURUSD": -0.2, "XAUUSD": 0.3}
ESC = {"XAUUSD": 3, "NAS100": 4}
def clamp(x): return max(-1.0, min(1.0, x))
@bloco("Score")
def b_score():
    at = {r["ativo"]: r for r in ler("mi_ativos.json")}; cot = ler("mi_cot.json"); mac = {r["serie"]: r for r in ler("mi_macro.json")}
    vixp = (mac.get("VIX") or {}).get("pctil_1a"); fg = FG.get("fg")
    ro = []
    if vixp is not None: ro.append((vixp - 50) / 50)
    if fg is not None: ro.append((50 - fg) / 50)
    risk_off = clamp(sum(ro) / len(ro)) if ro else 0
    dxy20 = (mac.get("DXY") or {}).get("var_20d")
    rows = []
    for a, r in at.items():
        c = closes(P[a]); ks = sorted(c); px = c[ks[-1]]
        ma = lambda n: st.mean(c[k] for k in ks[-n:])
        m20, m50, m200 = ma(20), ma(50), ma(200)
        comp = []
        t = (( 1 if px > m20 else -1) + (1 if m20 > m50 else -1) + (1 if px > m200 else -1)) / 3
        comp.append(("Tendência", t, f"preço {'acima' if px > m20 else 'abaixo'} da média de 20, {'acima' if px > m200 else 'abaixo'} da de 200 dias; média 20 {'acima' if m20 > m50 else 'abaixo'} da 50"))
        atrp = (r.get("atr14") or 0) / px * 100; v1 = r.get("var_1d") or 0
        comp.append(("Movimento de hoje", clamp(v1 / (1.5 * atrp)) if atrp else 0, f"{v1:+.2f}% hoje = {abs(v1) / atrp if atrp else 0:.1f}x a oscilação média diária".replace('.', ',')))
        imp = r.get("vj_imp20")
        comp.append(("Juros (macro)", clamp((imp or 0) / ESC.get(a, 1)), f"{r.get('vj_fator','—')} nos últimos 20 dias empurra o preço {imp:+.2f}%".replace('.', ',') if imp is not None else "sem dado"))
        comp.append(("Dólar (DXY)", clamp((dxy20 or 0) / 2 * DOLAR[a]), f"DXY {dxy20:+.2f}% em 20 dias".replace('.', ',') if dxy20 is not None else "sem dado"))
        cg = [x for x in cot if x["ativo"] == a]
        sc = 0; txt = "sem dado"
        if cg:
            lev = cg[0]; i = lev.get("indice_3a"); sgn = lev.get("sinal_par", 1)
            am = next((x for x in cg if x.get("papel") == "institucional"), None)
            if i is not None and i >= 80: sc = -(i - 80) / 20; txt = f"{lev['grupo'].split(' (')[0]} muito comprados (índice {i:.0f}): risco de reversão"
            elif i is not None and i <= 20: sc = (20 - i) / 20; txt = f"{lev['grupo'].split(' (')[0]} muito vendidos (índice {i:.0f}): espaço para alta"
            else:
                ref = am or lev; dv = ref.get("var_semana") or 0; sc = 0.3 if dv > 0 else -0.3 if dv < 0 else 0
                txt = f"posição neutra (índice {i:.0f}); {ref['grupo'].split(' (')[0].lower()} {'aumentaram' if dv > 0 else 'reduziram'} compra na semana"
            sc *= sgn
            if sgn < 0: txt += " (futuro da moeda: sinal invertido para o par)"
        comp.append(("COT", clamp(sc), txt))
        comp.append(("Risco (VIX/F&G)", clamp(RISCO[a] * risk_off), f"ambiente {'de aversão a risco' if risk_off > 0.2 else 'de apetite a risco' if risk_off < -0.2 else 'neutro'} (VIX percentil {vixp:.0f}, F&G {fg:.0f})" if vixp is not None and fg is not None else "sem dado"))
        sn = r.get("saz_mes10_sinal"); ac = r.get("saz_mes10_acerto")
        comp.append(("Sazonalidade", (1 if sn == "alta" else -1 if sn == "baixa" else 0) * (abs(ac - 50) / 50 if ac is not None else 0) * 2 if sn != "inconclusivo" else 0,
                     f"mês atual nos últimos 10 anos: subiu {ac:.0f}% ({'viés de ' + sn if sn != 'inconclusivo' else 'inconclusivo'})" if ac is not None else "sem dado"))
        z = r.get("vj_z"); r2 = r.get("vj_r2") or 0
        comp.append(("Valor justo", clamp(-(z or 0) / 2) if r2 >= 0.3 else 0, (f"preço {'abaixo' if (z or 0) < 0 else 'acima'} do justo (z {z:+.1f}, R² {r2:.2f})" + ("" if r2 >= 0.3 else ": relação fraca, peso zero")).replace('.', ',') if z is not None else "sem dado"))
        tot = sum(PESOS[n] * clamp(v) for n, v, _ in comp)
        score = round(50 + tot / 2)
        rows.append({"ativo": a, "score": score, "vies": "Altista" if score >= 60 else "Baixista" if score <= 40 else "Neutro",
                     "componentes": [{"fator": n, "peso": PESOS[n], "sinal": rnd(clamp(v), 2), "pontos": rnd(PESOS[n] * clamp(v) / 2, 1), "leitura": l} for n, v, l in comp]})
    save("mi_score.json", rows)
    # resumo compacto para a IA da tarefa
    ag = [x for x in ler("mi_agenda.json") if x["impacto"] == "Alto"][:15]; nw = ler("mi_noticias.json")[:30]
    with open(os.path.join(OUT, "digest.txt"), "w") as f:
        f.write(f"Data {NOW:%d/%m/%Y %H:%M} BRT. F&G {fg}, VIX pctil {vixp}, DXY 20d {dxy20}%\n")
        for x in rows:
            r = at[x["ativo"]]
            f.write(f"\n{x['ativo']}: preço {r['preco']} (1d {r['var_1d']}%, 5d {r['var_5d']}%, 20d {r['var_20d']}%)\n")
            fx_ = next((y for y in ler("mi_faixa.json") if y["ativo"] == x["ativo"]), None)
            if fx_:
                f.write(f"  vol. implícita/esperada {fx_['iv']}% ({(fx_.get('nivel') or {}).get('txt', '')}); " + "; ".join(f"{y['prazo']} ±1σ {y['s1'][0]}–{y['s1'][1]}, ±2σ {y['s2'][0]}–{y['s2'][1]}" for y in fx_["faixas"]) + "\n")
            rg_ = next((y for y in ler("mi_regime.json") if y["ativo"] == x["ativo"]), None)
            if rg_: f.write("  regime 26 semanas: " + "; ".join(f"{y['fator']} corr {y['corr26']}{' (quebrou)' if y['quebrou'] else ''}" for y in rg_["fatores"]) + "\n")
            if x["ativo"] == "XAUUSD":
                z_ = (ler("mi_0dte.json") or [{}])[0]
                if z_: f.write(f"  0DTE GLD ({z_.get('vencimento')}): teto {z_.get('call_wall')}, piso {z_.get('put_wall')}, gamma flip {z_.get('gamma_flip')}, faixa do dia {z_.get('faixa')}, {z_.get('regime')}\n")
        rd = {k: mac.get(k) for k in ("Liquidez líquida Fed", "VIX ÷ VIX 3 meses", "MOVE (vol. de Treasuries)", "Condições financeiras (NFCI)", "US2Y", "US10Y", "Juro real 10a", "Spread 2a EUA−Alemanha")}
        f.write("\nRadar institucional e juros: " + "; ".join(f"{k} {v['valor']} (20d {v['var_20d']}{v['unidade_var']}, pctil 1a {v['pctil_1a']})" for k, v in rd.items() if v) + "\n")
        eu = ler("mi_eua.json")
        if eu: f.write("Últimos dados oficiais dos EUA (período de referência): " + "; ".join(f"{x['evento']} {x['periodo']} = {x['valor']}{x['unidade']}" for x in eu) + "\n")
        f.write("\nRed folder da semana (BRT):\n" + "\n".join(f"  {x['quando']} {x['moeda']} {x['evento']} prev {x['previsao']} ant {x['anterior']}" for x in ag))
        f.write("\nManchetes:\n" + "\n".join(f"  [{x['fonte']}] {x['titulo']}" for x in nw) + "\n")
b_score()

# ---------------------------------------------------------------- painel geral (uma linha) + status
ag = [r for r in ler("mi_agenda.json") if r["impacto"] == "Alto" and r["data"] == NOW.date().isoformat()]
g, h = goldbach(NOW.date())
geral = {"gerado_em": NOW.strftime("%Y-%m-%d %H:%M"), "red_hoje": len(ag),
         "red_hoje_txt": " · ".join(f'{r["hora"]} {r["moeda"]} {r["evento"]}' for r in ag[:6]),
         "goldbach_hoje": ("★ Goldbach + Hopiplaka" if g and h else "Goldbach" if g else "Hopiplaka" if h else "nenhum"), **FG}
save("mi_geral.json", [geral])
save("mi_status.json", STATUS)
print(json.dumps(STATUS, ensure_ascii=False, indent=1))
