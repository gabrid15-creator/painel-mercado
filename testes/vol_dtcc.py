"""Volatilidade implícita das moedas pelos prêmios de opções do balcão (DTCC, público e grátis) × vol. realizada 21 d × 1,09 (a do painel).
Para cada opção vanilla (NEWT) com prazo de 1 a 30 dias e strike a ≤ 1% do preço: vol. implícita pelo prêmio (Black, juros ≈ 0 no prazo curto),
com o preço do par na hora do negócio (Yahoo 1 h, fechamento). σ do dia D+1 = mediana das vol. implícitas dos negócios do dia D (sem olhar o futuro).
Compara com o que o dia D+1 fez no FUTURO da CME: amplitude (máx − mín) e |fechamento − abertura|. Melhor σ = correlação maior com o tamanho do dia
e calibração (% dentro de ±1σ). Metades. Uso: python3 testes/vol_dtcc.py <pasta com AAAA-MM-DD.json.gz>"""
import sys, os, gzip, json, math, statistics as st, datetime as dt, urllib.request, glob
from zoneinfo import ZoneInfo
NY = ZoneInfo("America/New_York"); N = st.NormalDist()
PASTA = sys.argv[1]
PAR = {"USD/JPY": ("USDJPY", "JPY%3DX", "6J%3DF", True), "EUR/USD": ("EURUSD", "EURUSD%3DX", "6E%3DF", False),
       "USD/CHF": ("USDCHF", "CHF%3DX", "6S%3DF", True), "GBP/USD": ("GBPUSD", "GBPUSD%3DX", "6B%3DF", False)}
INV = {"JPY/USD": "USD/JPY", "USD/EUR": "EUR/USD", "CHF/USD": "USD/CHF", "USD/GBP": "GBP/USD"}
def y(s, r, i):
    u = f"https://query2.finance.yahoo.com/v8/finance/chart/{s}?range={r}&interval={i}"
    j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read())["chart"]["result"][0]
    q = j["indicators"]["quote"][0]
    return [(t, o, h, l, c) for t, o, h, l, c in zip(j["timestamp"], q["open"], q["high"], q["low"], q["close"]) if None not in (o, h, l, c)]
num = lambda x: float(str(x).replace(",", "")) if x not in (None, "") else None
def black(S, K, T, s, call):
    a = s * math.sqrt(T); d1 = (math.log(S / K) + a * a / 2) / a; d2 = d1 - a
    return S * N.cdf(d1) - K * N.cdf(d2) if call else K * N.cdf(-d2) - S * N.cdf(-d1)
def iv(S, K, T, P, call):
    lo, hi = 0.005, 1.0
    if not (black(S, K, T, lo, call) < P < black(S, K, T, hi, call)): return None
    for _ in range(60):
        m = (lo + hi) / 2; lo, hi = (m, hi) if black(S, K, T, m, call) < P else (lo, m)
    return (lo + hi) / 2
arqs = sorted(glob.glob(os.path.join(PASTA, "*.json.gz")))
for par, (nome, fx, fut, base_usd) in PAR.items():
    h1 = y(fx, "730d", "1h"); spot = {t // 3600: c for t, o, h, l, c in h1}
    base, quote = par.split("/")
    dia_iv = {}
    for f in arqs:
        d = dt.date.fromisoformat(os.path.basename(f)[:10]); vs = []
        for r in json.load(gzip.open(f, "rt")):
            p = r.get("Strike price currency/currency pair")
            if r.get("Action type") != "NEWT" or (p != par and INV.get(p) != par): continue
            try:
                K = num(r["Strike Price"]); ex = dt.date.fromisoformat(r["Expiration Date"]); ts = dt.datetime.fromisoformat(r["Execution Timestamp"].replace("Z", "+00:00"))
                if p != par: K = 1 / K
                if not (0.5 < K / (spot.get(int(ts.timestamp()) // 3600) or 1e9) < 2): K = 1 / K if K else K
                S = spot.get(int(ts.timestamp()) // 3600)
                dias = (ex - ts.date()).days
                if not S or not (1 <= dias <= 30) or abs(math.log(K / S)) > 0.01: continue
                fis = r.get("UPI FISN", "").split()   # "NA/O Van Call JPY USD": call na 1ª moeda
                if len(fis) < 5 or fis[2] != "Call" or fis[3] not in (base, quote): continue
                call = fis[3] == base
                cc = r.get("Call currency", "")   # mesmo filtro do dtcc.py: nome do produto e campo "Call currency" têm de concordar
                if (cc == base) != call or cc not in (base, quote): continue
                # quantidade na moeda base pela conta (cotada = base × strike), porque os rótulos às vezes vêm trocados
                base_amt = None
                for qa, qb in (("Call amount", "Put amount"), ("Notional amount-Leg 1", "Notional amount-Leg 2")):
                    va, vb = num(r.get(qa)), num(r.get(qb))
                    if not va or not vb: continue
                    if abs(vb / va / K - 1) < 0.06: base_amt = va; break
                    if abs(va / vb / K - 1) < 0.06: base_amt = vb; break
                pr, pc = num(r.get("Option Premium Amount")), r.get("Option Premium Currency")
                if not base_amt or not pr or pc not in (base, quote): continue
                P = (pr if pc == quote else pr * S) / base_amt   # prêmio por unidade da base, na moeda cotada
                T = (dias - 0.5) / 365
                v = iv(S, K, T, P, call)
                if v and 0.02 < v < 0.40: vs.append(v)
            except Exception: continue
        if len(vs) >= 5: dia_iv[d] = st.median(vs)
    dv = y(fut, "2y", "1d"); dd = [(dt.datetime.fromtimestamp(t, NY).date(), o, h, l, c) for t, o, h, l, c in dv]
    rows = []; DIAS = []
    for i in range(22, len(dd)):
        d, o, h, l, c = dd[i]
        ant = [x for x in dia_iv if x < d]
        if not ant or (d - max(ant)).days > 4: continue
        s_dt = dia_iv[max(ant)] / math.sqrt(252)
        rr = [math.log(dd[k][4] / dd[k - 1][4]) for k in range(i - 21, i)]; s_rv = st.stdev(rr) * 1.09
        if h <= l or math.log(h / l) > 0.05: continue
        rows.append((s_dt, s_rv, math.log(h / l), abs(math.log(c / o))))
        DIAS.append((d, s_dt, o, c))
    if len(rows) < 60: print(nome, "poucos dias", len(rows)); continue
    def cor(a, b): return st.correlation([math.log(x) for x in a], [math.log(max(x, 1e-5)) for x in b])
    sdt, srv, amp, mov = zip(*rows); m = len(rows) // 2
    print(f"{nome}: n={len(rows)} dias | vol. DTCC média {st.mean(sdt)*math.sqrt(252)*100:.1f}% × realizada {st.mean(srv)*math.sqrt(252)*100:.1f}%")
    print(f"   prevê a amplitude do dia: DTCC r={cor(sdt, amp):.2f} [{cor(sdt[:m], amp[:m]):.2f}/{cor(sdt[m:], amp[m:]):.2f}] × realizada r={cor(srv, amp):.2f} [{cor(srv[:m], amp[:m]):.2f}/{cor(srv[m:], amp[m:]):.2f}]")
    print(f"   fechou dentro de ±1σ: DTCC {sum(1 for a, b in zip(sdt, mov) if b <= a) / len(rows):.0%} × realizada {sum(1 for a, b in zip(srv, mov) if b <= a) / len(rows):.0%} (ideal 68%)")
    qt = lambda v, p: sorted(v)[int(p * len(v))]
    z = [b / a for a, b in zip(sdt, mov)]; za = [b / a for a, b in zip(sdt, amp)]
    print(f"   com σ DTCC: ±2σ {sum(1 for x in z if x <= 2) / len(z):.0%} | |fech−abert| 50%≤{qt(z,.5):.2f}σ 90%≤{qt(z,.9):.2f}σ | amplitude mediana {qt(za,.5):.2f}σ")
    sem = {}
    for d, sg, o, c in DIAS: sem.setdefault(d.isocalendar()[:2], []).append((d, sg, o, c))
    w = [(v[0][1] * math.sqrt(5), abs(math.log(v[-1][3] / v[0][2]))) for v in sem.values() if len(v) >= 4]
    print(f"   semana (σ da segunda × √5): ±1σ {sum(1 for a, b in w if b <= a) / len(w):.0%} ±2σ {sum(1 for a, b in w if b <= 2 * a) / len(w):.0%} n={len(w)}")
