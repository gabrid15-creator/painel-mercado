#!/usr/bin/env python3
"""Grava candles de 1 min (futuros da CME e DXY) por dia em <pasta>/AAAA-MM-DD.csv.gz, para os testes de SMT.
Roda 1×/dia (passo do workflow ~01h UTC); pega os últimos 5 dias do Yahoo e só grava dias completos ainda não salvos.
Uso: python3 minutos.py <pasta>"""
import sys, os, gzip, json, time, datetime as dt, urllib.request, urllib.parse
PASTA = sys.argv[1] if len(sys.argv) > 1 else "min"
ATV = {"ouro": "GC=F", "prata": "SI=F", "dxy": "DX-Y.NYB", "euro": "6E=F", "iene": "6J=F", "franco": "6S=F"}
hoje = dt.datetime.now(dt.timezone.utc).date()
por_dia = {}
for nome, sym in ATV.items():
    j = None
    for _ in range(3):
        try:
            u = f"https://query2.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?range=5d&interval=1m"
            j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=20).read())["chart"]["result"][0]; break
        except Exception as e: print(nome, e); time.sleep(5)
    if not j: continue
    q = j["indicators"]["quote"][0]
    for t, o, h, l, c, v in zip(j["timestamp"], q["open"], q["high"], q["low"], q["close"], q["volume"]):
        if None in (o, h, l, c): continue
        d = dt.datetime.fromtimestamp(t, dt.timezone.utc).date()
        if d < hoje: por_dia.setdefault(d, []).append(f"{nome},{t},{o:.6g},{h:.6g},{l:.6g},{c:.6g},{v or 0}")
os.makedirs(PASTA, exist_ok=True); n = 0
for d, linhas in sorted(por_dia.items()):
    arq = os.path.join(PASTA, f"{d.isoformat()}.csv.gz")
    if os.path.exists(arq): continue
    with gzip.open(arq, "wt") as f: f.write("ativo,ts_utc,abre,max,min,fecha,volume\n" + "\n".join(linhas) + "\n")
    n += 1; print("gravado", arq, len(linhas))
print("dias novos:", n)
