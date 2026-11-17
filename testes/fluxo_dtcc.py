"""Fluxo das opções de balcão (DTCC) dá a DIREÇÃO? 2 anos, 4 pares. A DTCC não diz quem comprou; medimos o que dá:
F1 desequilíbrio de tamanho calls − puts (÷ total) dos negócios novos (prazo 1–30 d, strike a ≤ 3%)   F2 o mesmo pesado pelo prêmio pago
F3 skew: vol. implícita das calls fora do dinheiro − puts fora do dinheiro (0,3–3% do preço)            F4 variação da vol. implícita (hoje − ontem)
Prazos: (A) fluxo da madrugada 17h→9h NY prevê 9h→17h NY do mesmo dia; (B) fluxo do dia inteiro prevê o dia seguinte (abertura→fechamento).
Direção no par (USDJPY, EURUSD…); preço dos futuros da CME (6J/6S invertidos). 32 testes → corte |t| ≥ 3 e metades com o mesmo sinal.
Uso: python3 testes/fluxo_dtcc.py <pasta hist DTCC>"""
import sys, os, glob, gzip, json, math, statistics as st, datetime as dt, urllib.request
from zoneinfo import ZoneInfo
NY = ZoneInfo("America/New_York"); N = st.NormalDist()
PASTA = sys.argv[1]
PAR = {"USD/JPY": ("USDJPY", "JPY%3DX", "6J%3DF", -1), "EUR/USD": ("EURUSD", "EURUSD%3DX", "6E%3DF", 1),
       "USD/CHF": ("USDCHF", "CHF%3DX", "6S%3DF", -1), "GBP/USD": ("GBPUSD", "GBPUSD%3DX", "6B%3DF", 1)}
INV = {"JPY/USD": "USD/JPY", "USD/EUR": "EUR/USD", "CHF/USD": "USD/CHF", "USD/GBP": "GBP/USD"}
num = lambda x: float(str(x).replace(",", "")) if x not in (None, "") else None
def y(s, r, i):
    u = f"https://query2.finance.yahoo.com/v8/finance/chart/{s}?range={r}&interval={i}"
    j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read())["chart"]["result"][0]
    q = j["indicators"]["quote"][0]
    return [(t, o, h, l, c) for t, o, h, l, c in zip(j["timestamp"], q["open"], q["high"], q["low"], q["close"]) if None not in (o, h, l, c)]
def black(S, K, T, s, call):
    a = s * math.sqrt(T); d1 = (math.log(S / K) + a * a / 2) / a; d2 = d1 - a
    return S * N.cdf(d1) - K * N.cdf(d2) if call else K * N.cdf(-d2) - S * N.cdf(-d1)
def iv(S, K, T, P, call):
    lo, hi = 0.005, 1.0
    if not (black(S, K, T, lo, call) < P < black(S, K, T, hi, call)): return None
    for _ in range(50):
        m = (lo + hi) / 2; lo, hi = (m, hi) if black(S, K, T, m, call) < P else (lo, m)
    return (lo + hi) / 2
def tt(x, yv):
    n = len(x)
    if n < 40: return 0, 0, 0, n
    try:
        r = st.correlation(x, yv); h = n // 2
        return r * math.sqrt((n - 2) / (1 - r * r)), st.correlation(x[:h], yv[:h]), st.correlation(x[h:], yv[h:]), n
    except Exception: return 0, 0, 0, n
arqs = sorted(glob.glob(os.path.join(PASTA, "*.json.gz"))); RES = []
for par, (nome, fx, fut, sn) in PAR.items():
    spot = {t // 3600: c for t, o, h, l, c in y(fx, "730d", "1h")}
    base, quote = par.split("/")
    # sessões: chave = dia de negociação (17h NY vira o dia); parte "madrugada" = antes das 9h NY
    sess = lambda t: (t + dt.timedelta(hours=7)).date()
    F = {}   # (dia, parte) -> listas
    for f in arqs:
        for r in json.load(gzip.open(f, "rt")):
            p = r.get("Strike price currency/currency pair")
            if r.get("Action type") != "NEWT" or (p != par and INV.get(p) != par): continue
            try:
                K = num(r["Strike Price"]); ts = dt.datetime.fromisoformat(r["Execution Timestamp"].replace("Z", "+00:00")); S = spot.get(int(ts.timestamp()) // 3600)
                if not S or not K: continue
                if not (0.5 < K / S < 2): K = 1 / K
                dias = (dt.date.fromisoformat(r["Expiration Date"]) - ts.date()).days
                m = math.log(K / S)
                if not (1 <= dias <= 30) or abs(m) > 0.03: continue
                fis = r.get("UPI FISN", "").split()
                if len(fis) < 5 or fis[2] not in ("Call", "Put") or fis[3] not in (base, quote): continue
                call = (fis[3] == base) == (fis[2] == "Call")   # call no par = call na base ou put na cotada
                cc = r.get("Call currency", "")   # mesmo filtro do dtcc.py: o campo tem de concordar com o nome do produto
                if cc not in (base, quote) or (cc == base) != call: continue
                ba = None
                for qa, qb in (("Call amount", "Put amount"), ("Notional amount-Leg 1", "Notional amount-Leg 2")):
                    va, vb = num(r.get(qa)), num(r.get(qb))
                    if va and vb:
                        if abs(vb / va / K - 1) < 0.06: ba = va; break
                        if abs(va / vb / K - 1) < 0.06: ba = vb; break
                if not ba: continue
                usd = ba if base == "USD" else ba * K
                pr, pc = num(r.get("Option Premium Amount")), r.get("Option Premium Currency")
                P = ((pr if pc == quote else pr * S) / ba) if pr and pc in (base, quote) else None
                v = iv(S, K, (dias - 0.5) / 365, P, call) if P else None
                tl = ts.astimezone(NY); d = sess(tl); parte = "mad" if tl.hour < 9 or tl.hour >= 17 else "dia"
                F.setdefault(d, []).append((parte, call, usd, (P * ba / S if P else 0) * (1 if base == "USD" else S), m, v))
            except Exception: continue
    def sinais(lst):
        c = sum(x[2] for x in lst if x[1]); p = sum(x[2] for x in lst if not x[1])
        pc_ = sum(x[3] for x in lst if x[1]); pp_ = sum(x[3] for x in lst if not x[1])
        oc = [x[5] for x in lst if x[5] and x[1] and 0.003 <= x[4] <= 0.03]; op = [x[5] for x in lst if x[5] and not x[1] and -0.03 <= x[4] <= -0.003]
        at = [x[5] for x in lst if x[5] and abs(x[4]) <= 0.01]
        return {"F1": (c - p) / (c + p) if c + p else None, "F2": (pc_ - pp_) / (pc_ + pp_) if pc_ + pp_ else None,
                "F3": st.median(oc) - st.median(op) if len(oc) >= 3 and len(op) >= 3 else None, "iv": st.median(at) if len(at) >= 5 else None}
    h1 = [(dt.datetime.fromtimestamp(t, NY), o, c) for t, o, h, l, c in y(fut, "730d", "1h")]
    px = {}
    for t, o, c in h1: px.setdefault(sess(t), []).append((t, o, c))
    ds = sorted(d for d in F if d in px)
    A = {k: ([], []) for k in ("F1", "F2", "F3", "F4")}; B = {k: ([], []) for k in ("F1", "F2", "F3", "F4")}
    ivant = None
    for i, d in enumerate(ds):
        mad = sinais([x for x in F[d] if x[0] == "mad"]); tudo = sinais(F[d])
        b9 = [c for t, o, c in px[d] if t.hour == 8]; b17 = [c for t, o, c in px[d] if t.hour == 16]
        if b9 and b17:
            r = sn * math.log(b17[0] / b9[0])
            for k in ("F1", "F2", "F3"):
                if mad[k] is not None: A[k][0].append(mad[k]); A[k][1].append(r)
            if mad["iv"] and ivant: A["F4"][0].append(mad["iv"] - ivant); A["F4"][1].append(r)
        if i + 1 < len(ds) and ds[i + 1] in px:
            nx = px[ds[i + 1]]; r = sn * math.log(nx[-1][2] / nx[0][1])
            for k in ("F1", "F2", "F3"):
                if tudo[k] is not None: B[k][0].append(tudo[k]); B[k][1].append(r)
            if tudo["iv"] and ivant: B["F4"][0].append(tudo["iv"] - ivant); B["F4"][1].append(r)
        if tudo["iv"]: ivant = tudo["iv"]
    for nomep, G in (("A madrugada→resto do dia", A), ("B dia→dia seguinte", B)):
        for k, (x, yv) in G.items():
            t, r1, r2, n = tt(x, yv); ok = abs(t) >= 3 and r1 * r2 > 0
            acerto = sum(1 for a, b in zip(x, yv) if a * b > 0) / max(1, sum(1 for a, b in zip(x, yv) if a * b != 0))
            RES.append((nome, nomep, k, t, ok)); print(f"{'✅' if ok else '  '} {nome} {nomep} {k}: n={n} t={t:+.1f} metades {r1:+.2f}/{r2:+.2f} acerta o lado {acerto:.0%}")
print("PASSOU:", [x[:4] for x in RES if x[4]] or "nada")
