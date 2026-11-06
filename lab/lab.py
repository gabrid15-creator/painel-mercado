# Laboratório do ouro (separado do painel): VRP, posição CTA estimada, gatilhos, mão pela volatilidade e score.
# Score da véspera = VRP (até 60) + salto do GVZ (até 40). Gatilho CTA fica só informativo (não passou na validação 06/11/2026).
# Roda 1x por dia. Só biblioteca padrão. Saída: <pasta>/lab.json
import json, math, sys, time, urllib.request, urllib.parse, statistics as st, datetime as dt, csv, io

OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
H = {'User-Agent': 'painel-lab/1.0'}

def get(url, tries=3, hdr=None):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=H if hdr is None else hdr), timeout=30) as r:
                return r.read().decode()
        except Exception:
            if k == tries - 1: raise
            time.sleep(3 * (k + 1))

def yahoo(sym, anos=4):
    p2 = int(time.time()); p1 = p2 - anos * 365 * 86400
    j = json.loads(get(f'https://query2.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?period1={p1}&period2={p2}&interval=1d'))
    r = j['chart']['result'][0]; d = {}
    for t, c in zip(r['timestamp'], r['indicators']['quote'][0]['close']):
        if c is not None: d[dt.datetime.fromtimestamp(t, dt.timezone.utc).date().isoformat()] = c
    return sorted(d.items())

def fred(sid, ini):
    rows = list(csv.reader(io.StringIO(get(f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}', hdr={}))))[1:]
    return {d: float(v) for d, v in rows if v not in ('', '.') and d >= ini}

def cot():
    q = ("https://publicreporting.cftc.gov/resource/72hh-3qpy.json?$select=report_date_as_yyyy_mm_dd,open_interest_all,"
         "m_money_positions_long_all,m_money_positions_short_all&$where=cftc_contract_market_code='088691'&$order=report_date_as_yyyy_mm_dd%20DESC&$limit=160")
    rows = json.loads(get(q.replace(' ', '%20')))
    out = [(r['report_date_as_yyyy_mm_dd'][:10], (float(r['m_money_positions_long_all']) - float(r['m_money_positions_short_all'])) / float(r['open_interest_all'])) for r in rows]
    return sorted(out)

px = yahoo('GC=F')
dates = [d for d, _ in px]; c = [v for _, v in px]
lr = [math.log(c[i] / c[i - 1]) for i in range(1, len(c))]

# volatilidade (EWM span 60, anualizada) — igual ao modelo calibrado no backtest
a = 2 / 61; var = lr[0] ** 2; vol = [None]
for x in lr:
    var = (1 - a) * var + a * x * x; vol.append(math.sqrt(var * 252))
rv21 = [None] * len(c)
for i in range(22, len(c)):
    rv21[i] = st.stdev(lr[i - 21:i]) * math.sqrt(252) * 100

g = fred('GVZCLS', dates[0]); gvz = []
last = None
for d in dates:
    last = g.get(d, last); gvz.append(last)

LB = (60, 120, 250)
def cta_at(i):
    s = []
    for lb in LB:
        z = math.log(c[i] / c[i - lb]) / (vol[i] * math.sqrt(lb / 252))
        s.append(math.tanh(z))
    raw = sum(s) / len(s)
    return max(-1, min(1, raw * min(0.15 / vol[i], 2))), s

def score_at(i):
    v = gvz[i] - rv21[i] if gvz[i] and rv21[i] else None
    pts = {}
    pts['vrp'] = 0 if v is None else (60 if v < 0 else 45 if v < 3 else 20 if v < 6 else 0)
    ch = (gvz[i] / gvz[i - 5] - 1) * 100 if gvz[i] and gvz[i - 5] else 0
    pts['gvz'] = 40 if ch < 10 else 15 if ch < 20 else 0
    atr = st.mean(abs(c[j] - c[j - 1]) for j in range(i - 19, i + 1))
    trig = [c[i + 1 - lb] for lb in LB]                    # preço que zera o sinal de cada prazo amanhã
    dist = min(abs(c[i] - t) for t in trig) / atr
    return sum(pts.values()), pts, v, ch, dist, trig, atr

n = len(c) - 1
pos, sig = cta_at(n)
sc, pts, vrp, gch, dist, trig, atr = score_at(n)
# mão = GVZ normal do último ano ÷ GVZ de hoje (06/11/2026: GVZ foi o melhor previsor do range de amanhã, corr. 0,55,
# e deixou o risco diário 16% mais estável que lote fixo; a versão anterior subestimava a mão ~11% em média)
vmed = st.median(x for x in gvz[-252:] if x) / 100
vnow = (gvz[n] or vmed * 100) / 100
mult = max(0.25, min(1.5, vmed / vnow))

hist = []
for i in range(max(260, n - 120), n + 1):
    s_, _, v_, *_ = score_at(i); p_, _ = cta_at(i)
    hist.append([dates[i], s_, round(v_, 2) if v_ is not None else None, round(p_ * 100)])

# Eventos agendados (testado out/2020–out/2026): NFP (1ª sexta) = 18% de dias de tendência x 9% normal;
# FOMC = range 1,45× o médio e 42% dos dias com range > 1,5× (normal 12%), mas sem direção (chicote).
EV = json.load(open(__file__.rsplit('/', 1)[0] + '/eventos.json'))   # datas oficiais BLS/Fed
def eventos(d):
    k = d.isoformat(); return [n.upper() for n in ('fomc', 'cpi', 'nfp', 'ppi') if k in EV[n]]
def evento(d):
    e = eventos(d); return e[0] if e else None
hoje_ny = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=5)).date()
MOD = json.load(open(__file__.rsplit('/', 1)[0] + '/modelo_tendencia.json'))
def prob(h, feats):
    m = MOD['modelos'][str(h)]; z = m['b'] + sum(c * feats[k] for c, k in zip(m['coef'], m['cols']))
    return 1 / (1 + math.exp(-z))
ev_h = evento(hoje_ny)
p0 = prob(0, {'vrp': max(-10, min(15, vrp or 0)), 'gvz5': max(-30, min(60, gch)), 'nfp': 1.0 if ev_h == 'NFP' else 0.0, 'fomc': 1.0 if ev_h == 'FOMC' else 0.0})
try: ct = cot()
except Exception: ct = []
J = {
  'atualizado': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%MZ'), 'data': dates[n], 'preco': round(c[n], 1),
  'gvz': gvz[n], 'rv21': round(rv21[n], 2), 'vrp': round(vrp, 2) if vrp is not None else None, 'gvz_var5': round(gch, 1),
  'cta': {'posicao': round(pos * 100), 'sinais': {str(lb): round(s, 2) for lb, s in zip(LB, sig)},
          'gatilhos': {str(lb): round(t, 1) for lb, t in zip(LB, trig)}, 'dist_atr': round(dist, 2), 'atr_dia': round(atr, 1)},
  'cot': {'data': ct[-1][0], 'mm_liq_pct_oi': round(ct[-1][1] * 100, 1),
          'z_3a': round((ct[-1][1] - st.mean(x for _, x in ct[-156:])) / st.stdev(x for _, x in ct[-156:]), 2)} if len(ct) > 20 else None,
  'mao': {'mult': round(mult, 2), 'vol_atual': round(vnow * 100, 1), 'vol_normal': round(vmed * 100, 1)},
  'score': sc, 'pontos': pts, 'hist': hist, 'evento': ev_h, 'eventos': eventos(hoje_ny), 'p0': round(p0 * 100, 1), 'base_pct': MOD['base_pct'], 'evento_data': hoje_ny.isoformat(),
}
open(f'{OUT}/lab.json', 'w').write(json.dumps(J, ensure_ascii=False, separators=(',', ':')))
print(json.dumps({k: J[k] for k in ('data', 'preco', 'vrp', 'score', 'pontos', 'cta', 'mao')}, ensure_ascii=False))
