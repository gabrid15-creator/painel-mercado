#!/usr/bin/env python3
"""Lê os PDFs da CME de opções de iene (Section33 calls e Section34 puts) e grava cme/iene_<pregão>.json.
Usa a parte "ADDITIONAL JAPANESE YEN ... Options", em que cada série vem separada com o código:
  1JY–5JY = sexta da semana N · MJ1–MJ5 = segunda · TJ = terça · WJ = quarta · SJ = quinta · JPU = mensal (sexta 2 semanas antes da 3ª quarta).
Preços em JPY/USD (ex.: strike 6300 = 0,006300 → USDJPY 158,73). Uso: python3 cme_pdf_iene.py <pdf calls> <pdf puts>"""
import sys, re, json, datetime as dt, calendar, pdfplumber
MES = {m: i for i, m in enumerate(["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], 1)}
DIA = {"JY": 4, "MJ": 0, "TJ": 1, "WJ": 2, "SJ": 3}   # dia da semana de cada código (segunda = 0)
def nth(a, m, wd, n):   # n-ésimo dia da semana wd do mês
    d = [x for x in calendar.Calendar().itermonthdates(a, m) if x.month == m and x.weekday() == wd]
    return d[n - 1] if n <= len(d) else None
def venc(cod, mes):
    a, m = 2000 + int(mes[3:]), MES[mes[:3]]
    if cod == "JPU":   # mensal: 2 sextas antes da 3ª quarta-feira
        return nth(a, m, 2, 3) - dt.timedelta(days=12)
    r = re.match(r"(\d)JY$|([A-Z]J)(\d)$", cod)
    if not r: return None
    if r.group(1): return nth(a, m, 4, int(r.group(1)))
    return nth(a, m, DIA[r.group(2)], int(r.group(3)))
rows, pregao, situ = [], None, "FINAL"
for arq in sys.argv[1:3]:
    txt = "\n".join((p.extract_text() or "") for p in pdfplumber.open(arq).pages)
    tipo = "Call" if "YEN CALL OPTIONS" in txt[:600] else "Put"
    m = re.search(r"(Mon|Tue|Wed|Thu|Fri), (\w{3}) (\d+), (\d{4})", txt)
    pregao = dt.datetime.strptime(f"{m.group(2)} {m.group(3)} {m.group(4)}", "%b %d %Y").date()
    if "PRELIMINARY" in txt[:2000]: situ = "PRELIMINARY"
    parte = txt[txt.index("ADDITIONAL JAPANESE YEN"):] if "ADDITIONAL JAPANESE YEN" in txt else ""
    cur = None
    for l in parte.splitlines():
        h = re.match(r"^(\w{3}\d{2}) \w+ OPT - (\w+) \(FUTURES SETT\. (\.\d+)", l)
        if h: v = venc(h.group(2), h.group(1)); cur = (v, float(h.group(3))) if v else None; continue
        if re.match(r"^[A-Z]{3} OPT - ", l) or l.startswith("TOTAL"): continue
        t = l.split()
        if not cur or len(t) < 10 or not re.fullmatch(r"\d{4,5}", t[0]): continue
        s = re.match(r"^(\.\d+|\d+\.\d+)", t[5])           # ajuste (às vezes grudado na variação: .0000030-.0000030)
        if not s: continue
        resto = t[:-2]                                      # tira máxima/mínima do contrato
        if resto[-1] == "UNCH": oi = resto[-2]
        elif resto[-2] in ("+", "-"): oi = resto[-3]
        else: oi = resto[-2]
        k = 6 if not re.fullmatch(r"[+-]?\.?\d+(\.\d+)?|UNCH|NEW", t[6] if len(t) > 6 else "") or t[6] in ("UNCH", "NEW") or t[6].startswith(("+", "-")) else 6
        dl = next((x for x in t[6:9] if re.fullmatch(r"\.\d+|1\.0+", x)), None)
        try: rows.append({"venc": cur[0].isoformat(), "tipo": tipo, "strike": int(t[0]) / 1e6, "settle": float(s.group(1)),
                          "delta": float(dl) if dl else None, "oi": int(oi), "futuro": cur[1], "data_pregao": pregao.isoformat()})
        except ValueError: pass
if len(rows) < 10: sys.exit(f"poucas linhas ({len(rows)}): confira se são os PDFs de iene (Section33 e Section34)")
nome = f"cme/iene_{pregao.isoformat()}.json"
json.dump({"iene_cadeia": rows, "iene_boletim": [{"data_pregao": pregao.isoformat(), "situacao": situ, "fonte": "CME Daily Bulletin, Sections 33/34"}]},
          open(nome, "w"), ensure_ascii=False, separators=(",", ":"))
print(nome, situ, len(rows), "linhas")
from collections import Counter
for v, n in sorted(Counter((r["venc"], r["tipo"]) for r in rows).items())[:16]: print(" ", v, n)
