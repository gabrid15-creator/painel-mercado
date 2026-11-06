# Laboratório do ouro — aviso intradiário de dia de tendência (roda de 30 em 30 min). Saída: <pasta>/intraday.json
# Regra testada em 2021–2026 (XAUUSD M1): às 10h NY, ouro já andou >= 0,6 ATR desde a meia-noite e está na ponta (>= 70% do range)
# -> pega 51% dos dias de tendência (78% se esperar até 12h); com >= 0,4 ATR pega 68%. Direção final igual à da manhã em ~100%.
import json, sys, time, urllib.request, urllib.parse, datetime as dt
from zoneinfo import ZoneInfo

OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
NY = ZoneInfo('America/New_York')

def bars(sym, rng, iv):
    u = f'https://query2.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?range={rng}&interval={iv}'
    for k in range(3):
        try:
            r = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'painel-lab/1.0'}), timeout=30).read())['chart']['result'][0]
            q = r['indicators']['quote'][0]; out = []
            for i, t in enumerate(r['timestamp']):
                if q['close'][i] is None: continue
                out.append((dt.datetime.fromtimestamp(t, NY), q['open'][i], q['high'][i], q['low'][i], q['close'][i]))
            return out
        except Exception:
            time.sleep(3 * (k + 1))
    return []

def dias(b):  # agrupa por dia de calendário de NY (dia começa à meia-noite, como no indicador dela)
    d = {}
    for t, o, h, l, c in b:
        k = t.date(); x = d.get(k)
        d[k] = [o, h, l, c] if x is None else [x[0], max(x[1], h), min(x[2], l), c]
    return d

agora = dt.datetime.now(NY)
g1h = bars('GC=F', '60d', '1h'); g5 = bars('GC=F', '1d', '5m')
D = dias(g1h); hoje = agora.date()
hist = [k for k in sorted(D) if k < hoje and k.weekday() < 5][-20:]
atr = sum(D[k][1] - D[k][2] for k in hist) / len(hist)
hj = [x for x in g5 if x[0].date() == hoje] or [x for x in g1h if x[0].date() == hoje]
J = {'atualizado': agora.strftime('%Y-%m-%dT%H:%M'), 'hora_ny': agora.strftime('%H:%M'), 'atr': round(atr, 1)}
if hj:
    o = hj[0][1]; h = max(x[2] for x in hj); l = min(x[3] for x in hj); c = hj[-1][4]
    mv = (c - o) / atr
    ponta = ((c - l) / (h - l) if mv > 0 else (h - c) / (h - l)) if h > l else 0
    hr = agora.hour + agora.minute / 60
    estado = 'cedo'
    if hr >= 8:
        lim_r = 0.6 if hr >= 10 else 0.8
        if abs(mv) >= lim_r and ponta >= 0.7: estado = 'tendencia'
        elif abs(mv) >= 0.4 and ponta >= 0.7: estado = 'atencao'
        else: estado = 'normal'
    J.update({'abertura': round(o, 1), 'preco': round(c, 1), 'max': round(h, 1), 'min': round(l, 1),
              'mov_atr': round(mv, 2), 'ponta': round(ponta, 2), 'estado': estado, 'direcao': 'alta' if mv > 0 else 'baixa'})
# probabilidade de dia de tendência (modelo logístico por horário, período todo out/2020–out/2026)
import math, os
MOD = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modelo_tendencia.json')))
try: L = json.load(open(f'{OUT}/lab.json'))
except Exception: L = {}
evt = L.get('evento') if L.get('evento_data') == hoje.isoformat() else None
f = {'vrp': max(-10, min(15, L.get('vrp') or 0)), 'gvz5': max(-30, min(60, L.get('gvz_var5') or 0)),
     'nfp': 1.0 if evt == 'NFP' else 0.0, 'fomc': 1.0 if evt == 'FOMC' else 0.0}
hr = agora.hour + agora.minute / 60
hh = 0 if (not hj or hr < 8) else min(12, int(hr))
if hh:
    mvv = min(3, abs(J['mov_atr'])); pt = max(0, min(1, J['ponta'])); f.update({'mov': mvv, 'ponta': pt, 'mov_x_ponta': mvv * pt})
m = MOD['modelos'][str(hh)]; z = m['b'] + sum(c * f[k] for c, k in zip(m['coef'], m['cols']))
J.update({'p': round(100 / (1 + math.exp(-z)), 1), 'p_hora': hh, 'evento': evt, 'base_pct': MOD['base_pct']})
open(f'{OUT}/intraday.json', 'w').write(json.dumps(J, ensure_ascii=False, separators=(',', ':')))
print(J)
