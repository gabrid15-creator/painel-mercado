import json, math, glob, os, sys, gzip, datetime as dt, statistics as st, collections, bisect
from zoneinfo import ZoneInfo
from yf import chart
exec(open("faixa_bt.py").read().split("ATV = {")[0])   # diario() (histórico diário completo)
NY = ZoneInfo("America/New_York")
src = open("/home/user/painel-mercado/dtcc.py").read()
os.makedirs("bt_tmp", exist_ok=True); sys.argv = ["dtcc.py", "bt_tmp"]
g = {"__name__": "bt"}; exec(src.split("def dias_uteis")[0], g)
YH = {"USDJPY": "JPY=X", "EURUSD": "EURUSD=X", "USDCHF": "CHF=X", "GBPUSD": "GBPUSD=X"}
H, SIG = {}, {}
for par, sym in YH.items():
    b = sorted((t, h, l, c) for t, o, h, l, c in chart(sym, "1h", "730d")); H[par] = ([x[0] for x in b], b)
    dd = [(d, c) for d, o, h, l, c in diario(sym) if c > 0]; dd = [x for i, x in enumerate(dd) if i == 0 or abs(math.log(x[1] / dd[i - 1][1])) < 0.15]
    r = [(dd[i][0], math.log(dd[i][1] / dd[i - 1][1])) for i in range(1, len(dd))]
    SIG[par] = {r[i][0]: st.stdev([x[1] for x in r[i - 21:i]]) * 1.09 for i in range(22, len(r))}   # σ do dia d (usa até d−1)
def barras(par, a, b):
    ts, bb = H[par]; return bb[bisect.bisect_left(ts, a.timestamp()):bisect.bisect_left(ts, b.timestamp())]
arqs = sorted(glob.glob("dtcc/hist/*.json.gz")) + sorted(f for f in glob.glob("dtcc/cache/CFTC_CUMULATIVE_FOREX_*.zip"))
obs = []; ini = None
import zipfile, io, csv
def linhas(f):
    if f.endswith(".gz"): return json.load(gzip.open(f, "rt"))
    z = zipfile.ZipFile(f); return list(csv.DictReader(io.TextIOWrapper(z.open(z.namelist()[0]), "utf-8")))
def data_arq(f):
    b = os.path.basename(f); return dt.date.fromisoformat(b[:10]) if b.endswith(".gz") else dt.date(*map(int, b[22:32].split("_")))
vistos = set(); fila = []
for f in arqs:
    d = data_arq(f)
    if d not in vistos: vistos.add(d); fila.append((d, f))
fila.sort()
ini = fila[0][0] + dt.timedelta(days=45)   # ≥ 45 dias de negócios carregados antes do 1º teste
for d, f in fila:
    if d >= ini and d.weekday() < 5:
        for par in YH:
            sg = SIG[par].get(d)
            pre = barras(par, dt.datetime.combine(d, dt.time(6, 0), NY), dt.datetime.combine(d, dt.time(7, 0), NY))
            cut = barras(par, dt.datetime.combine(d, dt.time(9, 0), NY), dt.datetime.combine(d, dt.time(10, 0), NY))
            dia = barras(par, dt.datetime.combine(d, dt.time(0, 0), NY), dt.datetime.combine(d, dt.time(17, 0), NY))
            ab = barras(par, dt.datetime.combine(d - dt.timedelta(days=1), dt.time(16, 0), NY), dt.datetime.combine(d - dt.timedelta(days=1), dt.time(17, 0), NY))
            if not (sg and pre and cut and len(dia) >= 14 and ab): continue
            s0, sc, sab = pre[-1][3], cut[-1][3], ab[-1][3]
            hi, lo = math.log(max(x[1] for x in dia) / sab), math.log(min(x[2] for x in dia) / sab)
            vivos = [v for v in g["NEG"].values() if v["p"] == par and v["v"] == d.isoformat()]
            passo = g["PASSO"][par]; gr = lambda k: round(round(k / passo) * passo, 6)
            cal, put, tot = collections.Counter(), collections.Counter(), collections.Counter()
            for v in vivos:
                if abs(v["k"] / sab - 1) <= 0.015: (cal if v["t"] == "C" else put)[gr(v["k"])] += v["n"]; tot[gr(v["k"])] += v["n"]
            teto = max((k for k in cal if k > sab), key=lambda k: cal[k], default=None); piso = max((k for k in put if k < sab), key=lambda k: put[k], default=None)
            kstar = max(tot, key=tot.get) if tot else None
            obs.append({"par": par, "dia": d.isoformat(), "sg": sg, "hi": hi, "lo": lo, "r_cut": math.log(sc / s0), "s0": s0,
                        "b": math.log(teto / sab) if teto else None, "a": math.log(sab / piso) if piso else None,
                        "mi_teto": cal.get(teto, 0), "mi_piso": put.get(piso, 0), "passo": math.log(1 + passo / sab),
                        "k": kstar, "mi_k": tot.get(kstar, 0), "rumo": (abs(math.log(sc / kstar)) < abs(math.log(s0 / kstar))) if kstar else None,
                        "rumo_base": None})
            if kstar:
                gl = sorted({gr(s0 * (1 + i / 1000)) for i in range(-10, 11)}); outros = [k for k in gl if abs(k - kstar) > passo / 2]
                obs[-1]["rumo_base"] = st.mean((abs(math.log(sc / k)) < abs(math.log(s0 / k))) for k in outros)
    g["HOJE"] = d; g["processa"](linhas(f))
json.dump(obs, open("bt2.json", "w"))
print("observações:", len(obs), "| dias:", len({o["dia"] for o in obs}), "| de", obs[0]["dia"], "a", obs[-1]["dia"])
