"""P7 (26/11/2026): quantos negócios a vol. implícita DTCC precisa? Nos dias com ≥ 25 negócios válidos (mesmo filtro do dtcc.py/vol_dtcc.py),
sorteia k negócios (k = 5, 8, 10, 15, 20; 1.000 sorteios) e mede o erro da mediana de k contra a mediana do dia inteiro.
Compara com a variação normal de um dia para o outro da vol. do dia inteiro (o "sinal").
Uso: python3 testes/min_negocios_dtcc.py <pasta com CFTC_CUMULATIVE_FOREX_AAAA_MM_DD.zip>"""
import sys, os, glob, zipfile, io, csv, json, math, random, statistics as st, datetime as dt, urllib.request
N = st.NormalDist(); random.seed(1)
PAR = {"USD/JPY": ("USDJPY", "JPY%3DX"), "EUR/USD": ("EURUSD", "EURUSD%3DX"), "USD/CHF": ("USDCHF", "CHF%3DX"), "GBP/USD": ("GBPUSD", "GBPUSD%3DX")}
INV = {"JPY/USD": "USD/JPY", "USD/EUR": "EUR/USD", "CHF/USD": "USD/CHF", "USD/GBP": "GBP/USD"}
num = lambda x: float(str(x).replace(",", "").rstrip("+")) if x not in (None, "") else None
def black(S, K, T, s, call):
    a = s * math.sqrt(T); d1 = (math.log(S / K) + a * a / 2) / a; d2 = d1 - a
    return S * N.cdf(d1) - K * N.cdf(d2) if call else K * N.cdf(-d2) - S * N.cdf(-d1)
def iv(S, K, T, P, call):
    lo, hi = 0.005, 1.0
    if not (black(S, K, T, lo, call) < P < black(S, K, T, hi, call)): return None
    for _ in range(50):
        m = (lo + hi) / 2; lo, hi = (m, hi) if black(S, K, T, m, call) < P else (lo, m)
    return (lo + hi) / 2
def yh(s):
    j = json.loads(urllib.request.urlopen(urllib.request.Request(f"https://query2.finance.yahoo.com/v8/finance/chart/{s}?range=3mo&interval=1h", headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read())["chart"]["result"][0]
    return {t // 3600: c for t, c in zip(j["timestamp"], j["indicators"]["quote"][0]["close"]) if c}
SPOT = {p: yh(s) for p, (_, s) in PAR.items()}
DIA = {p: {} for p in PAR}
for f in sorted(glob.glob(os.path.join(sys.argv[1], "*.zip"))):
    z = zipfile.ZipFile(f); d = f[-14:-4]
    for r in csv.DictReader(io.TextIOWrapper(z.open(z.namelist()[0]), "utf-8")):
        if not r.get("UPI FISN", "").startswith("NA/O Van ") or r.get("Action type") != "NEWT": continue
        p0 = r.get("Strike price currency/currency pair"); par = p0 if p0 in PAR else INV.get(p0)
        if not par: continue
        try:
            K = num(r["Strike Price"]); ex = dt.date.fromisoformat(r["Expiration Date"][:10]); ts = dt.datetime.fromisoformat(r["Execution Timestamp"].replace("Z", "+00:00"))
            S = SPOT[par].get(int(ts.timestamp()) // 3600)
            if not S or not K: continue
            if not (0.5 < K / S < 2): K = 1 / K
            dias = (ex - ts.date()).days
            if not (1 <= dias <= 30) or abs(math.log(K / S)) > 0.01: continue
            base, quote = par.split("/"); fis = r["UPI FISN"].split()
            if len(fis) < 5 or fis[2] != "Call" or fis[3] not in (base, quote): continue
            call = fis[3] == base; cc = r.get("Call currency", "")
            if (cc == base) != call or cc not in (base, quote): continue
            base_amt = None
            for qa, qb in (("Call amount", "Put amount"), ("Notional amount-Leg 1", "Notional amount-Leg 2")):
                va, vb = num(r.get(qa)), num(r.get(qb))
                if not va or not vb: continue
                if abs(vb / va / K - 1) < 0.06: base_amt = va; break
                if abs(va / vb / K - 1) < 0.06: base_amt = vb; break
            pr, pc = num(r.get("Option Premium Amount")), r.get("Option Premium Currency")
            if not base_amt or not pr or pc not in (base, quote): continue
            v = iv(S, K, (dias - 0.5) / 365, (pr if pc == quote else pr * S) / base_amt, call)
            if v and 0.02 < v < 0.40: DIA[par].setdefault(d, []).append(v)
        except Exception: continue
for par, (nome, _) in PAR.items():
    dd = DIA[par]; cont = sorted(len(v) for v in dd.values())
    meds = [math.log(st.median(dd[d])) for d in sorted(dd) if len(dd[d]) >= 25]
    sinal = st.median([abs(b - a) for a, b in zip(meds, meds[1:])]) if len(meds) > 3 else None
    print(f"{nome}: {len(dd)} dias, negócios por dia mediana {cont[len(cont)//2] if cont else 0} (mín {cont[0] if cont else 0}); "
          f"dias com ≥ 25: {len(meds)}; variação típica de um dia para o outro {sinal*100:.1f}%" if sinal else f"{nome}: poucos dias")
    if len(meds) < 4: continue
    for k in (5, 8, 10, 15, 20):
        er = []
        for d, v in dd.items():
            if len(v) < 25: continue
            m = st.median(v); er += [abs(math.log(st.median(random.sample(v, k)) / m)) for _ in range(1000)]
        er.sort(); print(f"   k={k:2d}: erro da mediana típico {er[len(er)//2]*100:.1f}%, 90% ≤ {er[int(.9*len(er))]*100:.1f}%")
