"""Scalp: depois de um negócio GRANDE de opção no balcão (DTCC), o preço anda a favor nos minutos seguintes?
Ideia: banco vende call grande → compra o par para se proteger → empurra o preço para cima (put: para baixo).
Eventos: negócios novos (NEWT), prazo ≤ 7 dias, strike a ≤ 1% do preço, tamanho ≥ corte (US$ 50 mi e US$ 200 mi).
Sinal: +1 call no par, −1 put. Resultado: retorno do FUTURO (5 min, 60 dias) do minuto do negócio até +5/15/30/60 min, no sentido do sinal.
Também a partir da hora em que a DTCC PUBLICA (Event timestamp; é quando o painel veria). Placebo: mesmo horário, sinal embaralhado.
Uso: python3 testes/scalp_dtcc.py <pasta hist DTCC>"""
import sys, os, glob, gzip, json, math, random, statistics as st, datetime as dt, urllib.request
PASTA = sys.argv[1]; random.seed(1)
PAR = {"USD/JPY": ("6J%3DF", -1), "EUR/USD": ("6E%3DF", 1), "USD/CHF": ("6S%3DF", -1), "GBP/USD": ("6B%3DF", 1)}
INV = {"JPY/USD": "USD/JPY", "USD/EUR": "EUR/USD", "CHF/USD": "USD/CHF", "USD/GBP": "GBP/USD"}
num = lambda x: float(str(x).replace(",", "").rstrip("+")) if x not in (None, "") else None   # "+" = tamanho acima do teto divulgado
BAR = int(os.environ.get("BAR", "300")); RANGE = {3600: "730d", 60: "8d"}.get(BAR, "60d")
def y(s):
    u = f"https://query2.finance.yahoo.com/v8/finance/chart/{s}?range={RANGE}&interval={ {3600: '1h', 60: '1m'}.get(BAR, '5m') }"
    j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read())["chart"]["result"][0]
    return {t: c for t, c in zip(j["timestamp"], j["indicators"]["quote"][0]["close"]) if c}
HZ = {"3600": [60, 120], "60": [1, 2, 3, 5, 10]}.get(os.environ.get("BAR", ""), [5, 15, 30, 60])
for par, (fut, sn) in PAR.items():
    px = y(fut); ts_ = sorted(px); ini = dt.datetime.fromtimestamp(ts_[0], dt.timezone.utc).date()
    base, quote = par.split("/")
    def preco(t):   # fechamento do candle de 5 min que contém t (t em segundos)
        k = int(t // BAR * BAR); return px.get(k)
    ev = []
    for f in sorted(glob.glob(os.path.join(PASTA, "*.json.gz"))):
        if dt.date.fromisoformat(os.path.basename(f)[:10]) < ini: continue
        for r in json.load(gzip.open(f, "rt")):
            p = r.get("Strike price currency/currency pair")
            if r.get("Action type") != "NEWT" or (p != par and INV.get(p) != par): continue
            try:
                fis = r.get("UPI FISN", "").split()
                if len(fis) < 5 or fis[2] not in ("Call", "Put") or fis[3] not in (base, quote): continue
                call = (fis[3] == base) == (fis[2] == "Call"); cc = r.get("Call currency", "")
                if cc not in (base, quote) or (cc == base) != call: continue
                te = dt.datetime.fromisoformat(r["Execution Timestamp"].replace("Z", "+00:00")).timestamp()
                tp = dt.datetime.fromisoformat((r.get("Event timestamp") or r["Execution Timestamp"]).replace("Z", "+00:00")).timestamp()
                K = num(r["Strike Price"]); S0 = preco(te)
                if not S0 or not K: continue
                S0p = S0 ** sn   # futuro → par
                if not (0.5 < K / S0p < 2): K = 1 / K
                if abs(math.log(K / S0p)) > 0.01: continue
                if (dt.date.fromisoformat(r["Expiration Date"]) - dt.date.fromtimestamp(te)).days > 7: continue
                ba = None
                for qa, qb in (("Call amount", "Put amount"), ("Notional amount-Leg 1", "Notional amount-Leg 2")):
                    va, vb = num(r.get(qa)), num(r.get(qb))
                    if va and vb:
                        if abs(vb / va / K - 1) < 0.06: ba = va; break
                        if abs(va / vb / K - 1) < 0.06: ba = vb; break
                if not ba: continue
                usd = ba if base == "USD" else ba * K
                ev.append((te, tp, 1 if call else -1, usd / 1e6))
            except Exception: continue
    for corte in (50, 200):
        E = [e for e in ev if e[3] >= corte]
        for orig, idx in (("negócio", 0), ("publicação", 1)):
            linha = []
            for h in HZ:
                x = []; plc = []
                for e in E:
                    a, b = preco(e[idx]), preco(e[idx] + h * 60)
                    if a and b:
                        r_ = sn * math.log(b / a) * 1e4 * e[2]; x.append(r_); plc.append(r_ * random.choice((1, -1)))
                if len(x) < 20: linha.append(f"{h}min n={len(x)}"); continue
                m = st.mean(x); t = m / (st.stdev(x) / math.sqrt(len(x))); hh = len(x) // 2
                ac = sum(1 for v in x if v > 0) / max(1, sum(1 for v in x if v != 0))
                linha.append(f"{h}min {m:+.2f}pb t={t:+.1f} [{st.mean(x[:hh]):+.2f}/{st.mean(x[hh:]):+.2f}] acerto {ac:.0%} n={len(x)}")
            print(f"{par} ≥US${corte}mi, a partir do {orig}: " + " | ".join(linha))

    # SEQUÊNCIA / AGRESSÃO: janela de 15 min com vários negócios do MESMO lado (≥ 3 negócios, ≥ 80% do tamanho num lado, total ≥ corte).
    # Dispara no fim da janela; depois espera 60 min (sem sobreposição). Resultado a partir do disparo e a partir da última publicação.
    ev.sort()
    for corte in (100, 300):
        disp = []; ult = 0
        for i, e in enumerate(ev):
            if e[0] < ult + 3600: continue
            jan = [x for x in ev[max(0, i - 200):i + 1] if e[0] - 900 <= x[0] <= e[0]]
            c = sum(x[3] for x in jan if x[2] > 0); p_ = sum(x[3] for x in jan if x[2] < 0)
            if len(jan) >= 3 and c + p_ >= corte and max(c, p_) / (c + p_) >= 0.8:
                disp.append((e[0], max(x[1] for x in jan), 1 if c > p_ else -1)); ult = e[0]
        for orig, idx in (("disparo", 0), ("publicação", 1)):
            linha = []
            for h in HZ:
                x = []
                for d_ in disp:
                    a, b = preco(d_[idx]), preco(d_[idx] + h * 60)
                    if a and b: x.append(sn * math.log(b / a) * 1e4 * d_[2])
                if len(x) < 20: linha.append(f"{h}min n={len(x)}"); continue
                m = st.mean(x); t = m / (st.stdev(x) / math.sqrt(len(x))); hh = len(x) // 2
                ac = sum(1 for v in x if v > 0) / max(1, sum(1 for v in x if v != 0))
                linha.append(f"{h}min {m:+.2f}pb t={t:+.1f} [{st.mean(x[:hh]):+.2f}/{st.mean(x[hh:]):+.2f}] acerto {ac:.0%} n={len(x)}")
            print(f"{par} SEQUÊNCIA ≥US${corte}mi em 15 min, a partir do {orig}: " + " | ".join(linha))
