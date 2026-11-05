#!/usr/bin/env python3
"""Coletor da aba Inteligência de mercado. Uso: python3 coletor.py <pasta_saida>
Só biblioteca padrão. Cada bloco é independente: se uma fonte falhar, os outros seguem e o erro vai para mi_status.json."""
import sys, os, json, csv, io, math, statistics as st, urllib.request, datetime as dt, traceback
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

OUT = sys.argv[1] if len(sys.argv) > 1 else "saida"
os.makedirs(OUT, exist_ok=True)
BRT = ZoneInfo("America/Sao_Paulo")
NOW = dt.datetime.now(BRT)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
      "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9"}
STATUS = []

def get(url, headers=None, timeout=40):
    h = dict(UA); h.update(headers or {})
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout) as r:
        return r.read()

def bloco(nome):
    def deco(fn):
        def run(*a):
            try:
                r = fn(*a)
                STATUS.append({"bloco": nome, "ok": True, "msg": ""})
                return r
            except Exception as e:
                STATUS.append({"bloco": nome, "ok": False, "msg": (type(e).__name__ + ": " + str(e))[:300]})
                traceback.print_exc()
                return None
        return run
    return deco

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
FATORES_Y = {"DXY": "DX-Y.NYB", "WTI": "CL=F", "Brent": "BZ=F", "VIX": "^VIX", "Crédito HY (HYG)": "HYG", "Gás natural": "NG=F"}
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
    raw = get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={','.join(ids)}&cosd={start}").decode()
    rd = csv.reader(io.StringIO(raw)); head = next(rd)
    res = {i: {} for i in ids}
    for row in rd:
        d = dt.date.fromisoformat(row[0])
        for i, v in zip(head[1:], row[1:]):
            if v not in ("", "."): res[i][d] = float(v)
    return res

import urllib.parse

def bund2y(start):
    url = ("https://api.statistiken.bundesbank.de/rest/data/BBSIS/D.I.ZAR.ZI.EUR.S1311.B.A604.R02XX.R.A.A._Z._Z.A"
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
    for k, y in FATORES_Y.items(): F[k] = closes(yahoo(y, 5))

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

b_precos(); b_tsy(); b_liq(); b_bund()

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
              "Dólar": ["DXY"], "Liquidez": ["TGA + RRP", "TGA", "RRP"],
              "Risco": ["VIX", "Crédito HY (HYG)"], "Energia": ["WTI", "Brent", "Gás natural"]}
    pts = {"US2Y","US10Y","Juro real 10a","Curva 2s10s","Bund 2a","Spread 2a EUA−Alemanha","Fed funds","SOFR","Infl. implícita 10a"}
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
        gbr = {"gb_extremos": rnd(100 * gbx / tot, 1) if tot else None, "gb_base": rnd(100 * base_g / nd, 1) if nd else None,
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
        grupos = ([("Fundos alavancados", "lev_money_positions_long", "lev_money_positions_short"),
                   ("Gestores de ativos", "asset_mgr_positions_long", "asset_mgr_positions_short"),
                   ("Dealers", "dealer_positions_long_all", "dealer_positions_short_all")] if kind == "tff" else
                  [("Managed money", "m_money_positions_long_all", "m_money_positions_short_all"),
                   ("Produtores", "prod_merc_positions_long", "prod_merc_positions_short"),
                   ("Swap dealers", "swap_positions_long_all", "swap__positions_short_all")])
        js = list(reversed(js))
        for g, lk, sk in grupos:
            if lk not in js[-1]: continue
            net = [n(r, lk) - n(r, sk) for r in js]
            w = net[-156:]
            idx = 100 * (net[-1] - min(w)) / (max(w) - min(w)) if max(w) > min(w) else None
            rows.append({"ativo": a, "grupo": g, "data": js[-1]["report_date_as_yyyy_mm_dd"][:10], "liquido": int(net[-1]),
                         "var_semana": int(net[-1] - net[-2]) if len(net) > 1 else None, "indice_3a": rnd(idx, 0),
                         "oi": int(n(js[-1], "open_interest_all")), "sinal_par": sg,
                         "hist": [[r["report_date_as_yyyy_mm_dd"][:10], int(v)] for r, v in zip(js[-52:], net[-52:])]})
    if not rows: raise ValueError("CFTC sem linhas")
    save("mi_cot.json", rows)
b_cot()

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
    for u in ("https://nfs.faireconomy.media/ff_calendar_thisweek.json",):
        for e in json.loads(get(u)):
            if e.get("country") not in ("USD", "EUR", "GBP", "JPY", "CHF") or e.get("impact") not in ("High", "Medium"): continue
            t = dt.datetime.fromisoformat(e["date"]).astimezone(BRT)
            rows.append({"quando": t.strftime("%Y-%m-%d %H:%M"), "data": t.date().isoformat(), "hora": t.strftime("%H:%M"), "moeda": e["country"],
                         "evento": e["title"], "impacto": "Alto" if e["impact"] == "High" else "Médio",
                         "previsao": e.get("forecast") or "", "anterior": e.get("previous") or ""})
    rows.sort(key=lambda r: r["quando"])
    save("mi_agenda.json", rows)
b_agenda()

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
    save("mi_noticias.json", uniq[:80])
b_news()

def ler(n):
    p = os.path.join(OUT, n); return json.load(open(p)) if os.path.exists(p) else []
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
            am = next((x for x in cg if x["grupo"] in ("Gestores de ativos",)), None)
            if i is not None and i >= 80: sc = -(i - 80) / 20; txt = f"{lev['grupo']} muito comprados (índice {i:.0f}): risco de reversão"
            elif i is not None and i <= 20: sc = (20 - i) / 20; txt = f"{lev['grupo']} muito vendidos (índice {i:.0f}): espaço para alta"
            else:
                ref = am or lev; dv = ref.get("var_semana") or 0; sc = 0.3 if dv > 0 else -0.3 if dv < 0 else 0
                txt = f"posição neutra (índice {i:.0f}); {ref['grupo'].lower()} {'aumentaram' if dv > 0 else 'reduziram'} compra na semana"
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
            f.write(f"\n{x['ativo']}: preço {r['preco']} (1d {r['var_1d']}%, 5d {r['var_5d']}%, 20d {r['var_20d']}%), score {x['score']} {x['vies']}\n")
            for cpt in x["componentes"]: f.write(f"  - {cpt['fator']} ({cpt['pontos']:+}): {cpt['leitura']}\n")
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
