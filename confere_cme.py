#!/usr/bin/env python3
"""Conferência independente dos arquivos lidos dos PDFs da CME. Rodar SEMPRE depois de cme_pdf.py / cme_pdf_iene.py e antes do commit.
Uso: python3 confere_cme.py --ouro <pdf Section64> cme/opcoes_<pregão>.json --iene <pdf calls> <pdf puts> cme/iene_<pregão>.json
Refaz a leitura por conta própria e para (código 1) se algo não bater:
  1. cada linha do JSON existe no PDF, no bloco/vencimento certo (strike, ajuste e contratos em aberto);
  2. paridade call − put coerente entre os strikes perto do dinheiro (vencimentos até 35 dias);
  3. nenhum ajuste abaixo do valor intrínseco (call/put trocadas ou futuro errado);
  4. futuro comparado com o do Yahoo no horário do ajuste (aviso se a régua do painel ficar longe)."""
import sys, re, json, math, calendar, datetime as dt, urllib.request
from zoneinfo import ZoneInfo
import pdfplumber

NY = ZoneInfo("America/New_York"); ERROS, AVISOS = [], []
def erro(m): ERROS.append(m); print("  ✗", m)
def aviso(m): AVISOS.append(m); print("  !", m)
def ok(m): print("  ✓", m)
def texto(pdf): return "\n".join((p.extract_text() or "") for p in pdfplumber.open(pdf).pages)
def yahoo_5m(sym, quando):
    try:
        u = f"https://query2.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?range=10d&interval=5m"
        q = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30))["chart"]["result"][0]
        px = [(t, v) for t, v in zip(q["timestamp"], q["indicators"]["quote"][0]["close"]) if v is not None and t <= quando.timestamp()]
        return px[-1][1] if px and quando.timestamp() - px[-1][0] < 3600 else None
    except Exception: return None
import urllib.parse

def paridade(rows, chave_tipo, tol_rel, pregao, nome):
    for v in sorted({r["venc"] for r in rows}):
        if (dt.date.fromisoformat(v) - pregao).days > 35: continue
        C = {float(r["strike"]): float(r["settle"]) for r in rows if r["venc"] == v and chave_tipo(r) == "C"}
        P = {float(r["strike"]): float(r["settle"]) for r in rows if r["venc"] == v and chave_tipo(r) == "P"}
        ks = sorted((k for k in C if k in P), key=lambda k: abs(C[k] - P[k]))[:3]
        if len(ks) < 2: print(f"    {nome} {v}: série fina, sem 2 pares call/put (futuro herdado: {next(r['futuro'] for r in rows if r['venc'] == v)})"); continue
        fs = [k + C[k] - P[k] for k in ks]; F = sorted(fs)[len(fs) // 2]
        gravado = float(next(r["futuro"] for r in rows if r["venc"] == v))
        if max(fs) - min(fs) > F * tol_rel: erro(f"{nome} {v}: paridade não fecha entre strikes {[round(x, 7) for x in fs]}")
        elif abs(gravado / F - 1) > tol_rel: erro(f"{nome} {v}: futuro gravado {gravado} ≠ paridade {round(F, 7)}")
        else: ok(f"{nome} {v}: paridade fecha (futuro {round(F, 7)}, {len(ks)} strikes)")
        ruins = [(k, "C", s) for k, s in C.items() if s < max(0, F - k) - F * 0.001] + [(k, "P", s) for k, s in P.items() if s < max(0, k - F) - F * 0.001]
        if ruins: erro(f"{nome} {v}: {len(ruins)} ajuste(s) abaixo do intrínseco, ex.: {ruins[:3]}")

# ---------------------------------------------------------------- ouro
def confere_ouro(pdf, arq):
    print("\n== OURO", arq)
    d = json.load(open(arq)); rows = d["ouro_cadeia"]; txt = texto(pdf).splitlines()
    pregao = dt.date.fromisoformat(rows[0]["data_pregao"])
    rx = re.compile(r"^(\d{3,5})\s.*?\s(\d+\.\d+)\s+(UNCH|NEW|[+-]\s?\d+\.\d+)\s+(\.\d+|1\.0+|----)\s+\S+\s+\S+\s+\S+\s+\S+\s+(\d+)\s+(UNCH|[+-]\s?\d+)$")
    venc_tab = {}
    for c, tp, dd in re.findall(r"^\s*(OG\d?) (CALL|PUT)\s+(\d\d/\d\d)", "\n".join(txt), re.M):
        mm, di = map(int, dd.split("/")); venc_tab.setdefault(c, dt.date(pregao.year + (mm < pregao.month), mm, di).isoformat())
    blocos, cur = {}, None
    for l in txt:
        if re.match(r"^[A-Z0-9]{2,4} (PUT|CALL|MON|TUE|WED|THU|FRI|OPT)\b", l):
            p = l.split(); cur = (p[0], p[1]) if "MICRO" not in l else None; continue
        r = rx.match(l) if cur else None
        if r: blocos.setdefault(cur, set()).add((float(r.group(1)), float(r.group(2)), int(r.group(5))))
    sem = {"0": "GMW", "1": "GWT", "2": "GWW", "3": "GWR"}
    faltam = []
    for o in rows:
        v = dt.date.fromisoformat(o["venc"]); t = "CALL" if o["tipo"] == "Call" else "PUT"
        cods = [c for c, vv in venc_tab.items() if vv == o["venc"]]
        chaves = [(c, t) for c in cods] + ([(sem[str(v.weekday())], ["MON", "TUE", "WED", "THU"][v.weekday()])] if v.weekday() < 4 else [])
        if not any((float(o["strike"]), float(o["settle"]), int(o["oi"])) in blocos.get(k, ()) for k in chaves): faltam.append(o)
    (erro if faltam else ok)(f"{len(rows) - len(faltam)}/{len(rows)} linhas encontradas no PDF no bloco certo" + (f"; sem par: {faltam[:3]}" if faltam else ""))
    paridade(rows, lambda r: r["tipo"][0], 0.0004, pregao, "ouro")
    from collections import Counter
    for (v, t), n in sorted(Counter((r["venc"], r["tipo"]) for r in rows).items()): print(f"    {v} {t}: {n} strikes, {sum(r['oi'] for r in rows if r['venc'] == v and r['tipo'] == t)} contratos em aberto")
    gc = yahoo_5m("GC=F", dt.datetime.combine(pregao, dt.time(13, 30), NY))
    F = float(rows[0]["futuro"])
    if gc: (ok if abs(gc - F) < 5 else aviso)(f"futuro pela paridade {F} × GC=F às 13h30 NY {round(gc, 1)} (dif. US$ {round(gc - F, 1)}); o painel converte pela razão GC=F ÷ futuro")
    else: aviso("não consegui o GC=F do horário do ajuste para comparar")

# ---------------------------------------------------------------- iene
MES = {m: i for i, m in enumerate(["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], 1)}
def nth(a, m, wd, n):
    d = [x for x in calendar.Calendar().itermonthdates(a, m) if x.month == m and x.weekday() == wd]; return d[n - 1] if n <= len(d) else None
def venc_iene(cod, mes):
    a, m = 2000 + int(mes[3:]), MES[mes[:3]]
    if cod == "JPU": return nth(a, m, 2, 3) - dt.timedelta(days=12)
    r = re.match(r"(\d)JY$|([A-Z]J)(\d)$", cod)
    if not r: return None
    return nth(a, m, 4, int(r.group(1))) if r.group(1) else nth(a, m, {"MJ": 0, "TJ": 1, "WJ": 2, "SJ": 3}[r.group(2)], int(r.group(3)))
def confere_iene(pdf_c, pdf_p, arq):
    print("\n== IENE", arq)
    d = json.load(open(arq)); rows = d["iene_cadeia"]; pregao = dt.date.fromisoformat(rows[0]["data_pregao"])
    linhas = {}
    for pdf in (pdf_c, pdf_p):
        txt = texto(pdf); tipo = "Call" if "YEN CALL OPTIONS" in txt[:600] else "Put"
        parte = txt[txt.index("ADDITIONAL JAPANESE YEN"):] if "ADDITIONAL JAPANESE YEN" in txt else ""; cur = None
        for l in parte.splitlines():
            h = re.match(r"^(\w{3}\d{2}) \w+ OPT - (\w+) \(FUTURES SETT", l)
            if h: cur = venc_iene(h.group(2), h.group(1)); continue
            t = l.split()
            if cur and t and re.fullmatch(r"\d{4,5}", t[0]):
                nums = {float(x) for x in re.findall(r"\.\d+|\d+\.\d+", " ".join(t[1:]))}
                ints = {int(x) for x in t[1:] if x.isdigit()}
                linhas.setdefault((tipo, cur.isoformat(), int(t[0])), []).append((nums, ints))
    faltam = []
    for o in rows:
        cand = linhas.get((o["tipo"], o["venc"], round(o["strike"] * 1e6)), [])
        if not any(any(abs(n - o["settle"]) < 1e-9 for n in nums) and o["oi"] in ints for nums, ints in cand): faltam.append(o)
    (erro if faltam else ok)(f"{len(rows) - len(faltam)}/{len(rows)} linhas encontradas no PDF no vencimento certo" + (f"; sem par: {faltam[:3]}" if faltam else ""))
    paridade(rows, lambda r: r["tipo"][0], 0.0005, pregao, "iene")
    usd = yahoo_5m("JPY=X", dt.datetime.combine(pregao, dt.time(15, 0), NY)); fj = yahoo_5m("6J=F", dt.datetime.combine(pregao, dt.time(15, 0), NY))
    prox = min((r for r in rows if r["venc"] > pregao.isoformat()), key=lambda r: r["venc"])
    if fj: (ok if abs(fj / prox["futuro"] - 1) < 0.0006 else aviso)(f"futuro de {prox['venc']} pela paridade {prox['futuro']} (USDJPY {round(1 / prox['futuro'], 3)}) × 6J=F às 15h NY {fj} (USDJPY {round(1 / fj, 3)})")
    if usd: ok(f"USDJPY à vista às 15h NY: {round(usd, 3)} (régua futuro → à vista do painel)")
    else: aviso("não consegui o USDJPY do horário do ajuste")

a = sys.argv[1:]
if "--ouro" in a: i = a.index("--ouro"); confere_ouro(a[i + 1], a[i + 2])
if "--iene" in a: i = a.index("--iene"); confere_iene(a[i + 1], a[i + 2], a[i + 3])
print(f"\nResultado: {len(ERROS)} erro(s), {len(AVISOS)} aviso(s)")
sys.exit(1 if ERROS else 0)
