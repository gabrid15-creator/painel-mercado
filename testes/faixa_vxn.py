"""P11 (26/11/2026): faixa do NAS100 pelo VXN (vol. implícita de 30 dias do Nasdaq 100, Cboe), mesmo método do faixa_backtest.py:
σ do prazo = VXN do dia ÷ 100 × √(n/252), fechamento de n dias à frente dentro de ±1σ/±2σ (janelas sem sobreposição, sem olhar o futuro).
Futuro NQ=F (sessão 18h→17h NY, a do painel) e índice ^NDX. Metades. Uso: python3 testes/faixa_vxn.py (roda numa pasta de rascunho)"""
import urllib.request, urllib.parse, json, math, statistics as st, datetime as dt, time
from zoneinfo import ZoneInfo
NY = ZoneInfo("America/New_York")
def diario(sym):
    u = f"https://query2.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?period1=0&period2={int(time.time())}&interval=1d"
    j = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60))["chart"]["result"][0]; q = j["indicators"]["quote"][0]
    return [(dt.datetime.fromtimestamp(t, NY).date(), o, h, l, c) for t, o, h, l, c in zip(j["timestamp"], q["open"], q["high"], q["low"], q["close"]) if None not in (o, h, l, c) and c > 0]
g = {d: c for d, o, h, l, c in diario("^VXN")}
out = {}
for sym in ("NQ=F", "^NDX"):
    b = diario(sym); b = [x for i, x in enumerate(b) if i == 0 or abs(math.log(x[4] / b[i - 1][4])) < 0.25]
    res = {}
    for n, nome in ((1, "dia"), (5, "semana"), (21, "mês")):
        lin = []; i = 1
        while i + n < len(b):
            iv = g.get(b[i][0])
            if iv is None: i += 1; continue
            sd = iv / 100 * math.sqrt(n / 252); z = abs(math.log(b[i + n][4] / b[i][4])) / sd
            lin.append((b[i + n][0], z)); i += n
        m = len(lin) // 2; pc = lambda L, k: round(100 * sum(z <= k for _, z in L) / len(L), 1)
        res[nome] = {"n": len(lin), "desde": str(lin[0][0]), "s1": pc(lin, 1), "s2": pc(lin, 2), "metades_s1": [pc(lin[:m], 1), pc(lin[m:], 1)], "metades_s2": [pc(lin[:m], 2), pc(lin[m:], 2)],
                     "ult_5a_s1": pc([x for x in lin if x[0] >= dt.date.today() - dt.timedelta(days=5 * 365)], 1)}
        print(f"{sym:5} {nome:6} n={res[nome]['n']:5} desde {res[nome]['desde']}  ±1σ {res[nome]['s1']}% (metades {res[nome]['metades_s1']}, 5 anos {res[nome]['ult_5a_s1']}%)  ±2σ {res[nome]['s2']}% (metades {res[nome]['metades_s2']})")
    out[sym] = res
json.dump(out, open("faixa_vxn.json", "w"))
