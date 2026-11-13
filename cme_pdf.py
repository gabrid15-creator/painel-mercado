#!/usr/bin/env python3
"""Lê o PDF "Metals Option Products" (Section 64) do boletim diário da CME, enviado pela usuária, e grava
cme/opcoes_<pregão>.json no formato do painel (ouro_cadeia + ouro_boletim). Uso: python3 cme_pdf.py <pdf>
Usa só as séries de sexta (OG1–OG5 e OG mensal), que vêm separadas em PUT/CALL no PDF; as semanais de seg–qui
vêm misturadas (vários vencimentos sem separação) e são ignoradas."""
import sys, re, json, datetime as dt, pdfplumber
pdf = pdfplumber.open(sys.argv[1])
txt = "\n".join((p.extract_text() or "") for p in pdf.pages)
m = re.search(r"(Mon|Tue|Wed|Thu|Fri), (\w{3}) (\d+), (\d{4})", txt)
pregao = dt.datetime.strptime(f"{m.group(2)} {m.group(3)} {m.group(4)}", "%b %d %Y").date()
situ = "PRELIMINARY" if "PRELIMINARY" in txt[:3000] else "FINAL"
# vencimentos da tabela do topo: "OG2 CALL 11/13", "OG CALL 11/24 12/28 ..." (pega a 1ª data)
VENC = {}
for c, d in re.findall(r"^\s*(OG\d?) (?:CALL|PUT)\s+(\d\d/\d\d)", txt, re.M):
    mm, dd = map(int, d.split("/")); a = pregao.year + (mm < pregao.month)
    VENC.setdefault(c, dt.date(a, mm, dd))
def uteis(a, b): return sum(1 for i in range(1, (b - a).days + 1) if (a + dt.timedelta(i)).weekday() < 5)
curtas = {c for c, v in VENC.items() if v > pregao and uteis(pregao, v) <= 2}
semana = min((c for c, v in VENC.items() if (v - pregao).days >= 3), key=lambda c: VENC[c], default=None)
usar = curtas | ({semana} if semana else set())
rx = re.compile(r"^(\d{3,5})\s.*?\s(\d+\.\d+)\s+(UNCH|NEW|[+-]\s?\d+\.\d+)\s+(\.\d+|1\.0+|----)\s+\S+\s+\S+\s+\S+\s+\S+\s+(\d+)\s+(UNCH|[+-]\s?\d+)$")
rows, cur = [], None
for l in txt.splitlines():
    h = re.match(r"^(OG\d?) (PUT|CALL)\s+(COMEX )?GOLD OPTIONS", l)
    if h: cur = (h.group(1), h.group(2)) if h.group(1) in usar else None; continue
    if re.match(r"^[A-Z0-9]{2,4} (PUT|CALL|MON|TUE|WED|THU|FRI|OPT)\b", l): cur = None; continue
    r = rx.match(l) if cur else None
    if r: rows.append({"venc": VENC[cur[0]].isoformat(), "tipo": "Call" if cur[1] == "CALL" else "Put", "strike": float(r.group(1)),
                       "settle": float(r.group(2)), "delta": None if r.group(4) == "----" else float(r.group(4)), "oi": int(r.group(5))})
F = {}   # futuro por paridade (call − put no strike onde os dois mais se aproximam)
for v in {x["venc"] for x in rows}:
    c = {x["strike"]: x["settle"] for x in rows if x["venc"] == v and x["tipo"] == "Call"}
    p = {x["strike"]: x["settle"] for x in rows if x["venc"] == v and x["tipo"] == "Put"}
    k = min((k for k in c if k in p), key=lambda k: abs(c[k] - p[k])); F[v] = round(k + c[k] - p[k], 1)
sel = []
for v, f in F.items():
    vv = [x for x in rows if x["venc"] == v]; kk = min({x["strike"] for x in vv}, key=lambda k: abs(k - f))
    for x in vv:
        if (x["oi"] > 0 and abs(x["strike"] / f - 1) <= 0.05) or x["strike"] == kk:
            x.update({"futuro": f, "data_pregao": pregao.isoformat(), "strike": int(x["strike"]) if x["strike"] % 1 == 0 else x["strike"]}); sel.append(x)
if len(sel) < 10: sys.exit(f"poucas linhas ({len(sel)}): confira se é o PDF certo (Section 64)")
out = {"ouro_cadeia": sel, "ouro_boletim": [{"data_pregao": pregao.isoformat(), "futuro": F[min(F)], "futuro_vencimento": "",
       "situacao": situ, "fonte": "CME Daily Bulletin, Section 64 (PDF enviado pela usuária)"}]}
nome = f"cme/opcoes_{pregao.isoformat()}.json"
json.dump(out, open(nome, "w"), ensure_ascii=False, separators=(",", ":"))
print(nome, situ, "futuro", F, "linhas", len(sel))
for v in sorted(F):
    s = [x for x in sel if x["venc"] == v]
    print(" ", v, " | ".join(f"{tp}: maior OI {max((x for x in s if x['tipo'] == tp), key=lambda x: x['oi'])['strike']}" for tp in ("Call", "Put") if any(x["tipo"] == tp for x in s)))
