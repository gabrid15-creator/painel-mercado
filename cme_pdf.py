#!/usr/bin/env python3
"""Lê o PDF "Metals Option Products" (Section 64) do boletim diário da CME, enviado pela usuária, e grava
cme/opcoes_<pregão>.json no formato do painel (ouro_cadeia + ouro_boletim). Uso: python3 cme_pdf.py <pdf>
Séries de sexta (OG1–OG5 e OG mensal) vêm separadas em PUT/CALL. As semanais de seg–qui (GMW seg, GWT ter, GWW qua, GWR qui)
vêm misturadas no PDF (calls, puts e mais de um vencimento no mesmo bloco); delas só se usa a série que vence em até 2 dias úteis,
separada pelo preço: tipo pela posição do delta (ITM > 0,5) e vencimento pela vol. implícita calculada para esse prazo
(a série curta forma um grupo de vol. normal; as longas dão vol. absurda nesse prazo). Travas: vol. parecida com a da sexta e paridade."""
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
rows, cur, mes, fechado = [], None, None, set()
for l in txt.splitlines():
    h = re.match(r"^(OG\d?) (PUT|CALL)\s+(COMEX )?GOLD OPTIONS", l)
    if h:
        novo = (h.group(1), h.group(2)) if h.group(1) in usar else None
        if novo in fechado: novo = None   # já passou do 1º mês desta série: as páginas seguintes são de outros meses
        if novo != cur: mes = None   # bloco novo (a mesma série pode continuar na página seguinte com o cabeçalho repetido)
        cur = novo; continue
    if re.match(r"^[A-Z0-9]{2,4} (PUT|CALL|MON|TUE|WED|THU|FRI|OPT)\b", l): cur = None; mes = None; continue
    # o bloco mensal (OG) traz vários meses (DEC26, JAN27…): só vale o 1º mês, que é o do vencimento (19/11: misturava e a paridade quebrava)
    mm_ = re.match(r"^([A-Z]{3}\d{2})\s*$", l.strip())
    if mm_ and cur:
        if mes is None: mes = mm_.group(1)
        elif mm_.group(1) != mes: fechado.add(cur); cur = None
        continue
    r = rx.match(l) if cur else None
    if r: rows.append({"venc": VENC[cur[0]].isoformat(), "tipo": "Call" if cur[1] == "CALL" else "Put", "strike": float(r.group(1)),
                       "settle": float(r.group(2)), "delta": None if r.group(4) == "----" else float(r.group(4)), "oi": int(r.group(5))})
# ---- semanais de seg–qui: só o vencimento curto (0–2 dias úteis), separado do resto do bloco pelo preço
import math, statistics as _st
_N = _st.NormalDist()
def _b76(Fx, k, cp, prem, T):
    lo, hi = 0.005, 5.0
    for _ in range(60):
        sg = (lo + hi) / 2; d1 = (math.log(Fx / k) + sg * sg * T / 2) / (sg * math.sqrt(T)); d2 = d1 - sg * math.sqrt(T)
        pr = Fx * _N.cdf(d1) - k * _N.cdf(d2) if cp == "C" else k * _N.cdf(-d2) - Fx * _N.cdf(-d1)
        lo, hi = (sg, hi) if pr < prem else (lo, sg)
    return sg
DIA = {"GMW": 0, "GWT": 1, "GWW": 2, "GWR": 3}
SEM = []
_vf0 = min((x["venc"] for x in rows), default=None)   # referência só com o vencimento mais próximo (misturar dois vencimentos dava futuro e vol. errados)
_cf = {x["strike"]: x["settle"] for x in rows if x["tipo"] == "Call" and x["venc"] == _vf0}; _pf = {x["strike"]: x["settle"] for x in rows if x["tipo"] == "Put" and x["venc"] == _vf0}
if _cf and _pf:
    _k = min((k for k in _cf if k in _pf), key=lambda k: abs(_cf[k] - _pf[k])); Fref = _k + _cf[_k] - _pf[_k]
    _vf = min(x["venc"] for x in rows); _Tf = max((dt.date.fromisoformat(_vf) - pregao).days, 1) / 365
    ivref = _st.median([_b76(Fref, x["strike"], "C" if x["tipo"] == "Call" else "P", x["settle"], _Tf) for x in rows if x["venc"] == _vf and abs(x["strike"] / Fref - 1) < 0.01 and x["settle"] > 0.5] or [0.2])
    for cod, wd in DIA.items():
        v = pregao + dt.timedelta(days=1)
        while v.weekday() != wd: v += dt.timedelta(days=1)
        if uteis(pregao, v) > 2: continue
        T = (v - pregao).days / 365
        bl, cur2 = [], False
        for l in txt.splitlines():
            if re.match(r"^[A-Z0-9]{2,4} (PUT|CALL|MON|TUE|WED|THU|FRI|OPT)\b", l): cur2 = l.startswith(cod + " ") and "MICRO" not in l; continue
            r = rx.match(l) if cur2 else None
            if r and r.group(4) != "----":
                k, st_, de = float(r.group(1)), float(r.group(2)), float(r.group(4))
                if abs(k / Fref - 1) > 0.05 or st_ <= 0: continue
                cp = "C" if (de > 0.5) == (k < Fref) else "P"
                bl.append({"k": k, "cp": cp, "s": st_, "oi": int(r.group(5)), "iv": _b76(Fref, k, cp, st_, T), "de": de})
        # strike colado no preço: call e put com delta quase 0,5 → o delta não separa (18/11, GWR 3865: 0,5002 × 0,4999 trocados).
        # Resolve pela paridade: a troca que deixa K + C − P igual à mediana dos outros strikes.
        _ref = []
        for k in {x["k"] for x in bl}:
            cc = [x for x in bl if x["k"] == k and x["cp"] == "C"]; pp = [x for x in bl if x["k"] == k and x["cp"] == "P"]
            if len(cc) == 1 and len(pp) == 1 and abs(k / Fref - 1) < 0.01 and abs(cc[0]["de"] - 0.5) > 0.02: _ref.append(k + cc[0]["s"] - pp[0]["s"])
        if len(_ref) >= 2:
            fm = _st.median(_ref)
            for k in {x["k"] for x in bl}:
                dup = [x for x in bl if x["k"] == k and abs(x["de"] - 0.5) <= 0.02]
                if len(dup) == 2 and {x["cp"] for x in dup} == {"C", "P"}:
                    c_, p_ = (dup[0], dup[1]) if dup[0]["cp"] == "C" else (dup[1], dup[0])
                    if abs(k + p_["s"] - c_["s"] - fm) < abs(k + c_["s"] - p_["s"] - fm):
                        c_["cp"], p_["cp"] = "P", "C"; c_["iv"] = _b76(Fref, k, "P", c_["s"], T); p_["iv"] = _b76(Fref, k, "C", p_["s"], T)
        atm = [x["iv"] for x in bl if abs(x["k"] / Fref - 1) < 0.01]
        if not atm: continue
        base = min(atm)
        if not (0.5 * ivref <= base <= 1.6 * ivref): print("semanal", cod, v, "descartada: vol.", round(base * 100, 1), "% vs sexta", round(ivref * 100, 1), "%"); continue
        perto = [x for x in bl if 0.8 * base <= x["iv"] <= 1.5 * base]
        c = {x["k"]: x["s"] for x in perto if x["cp"] == "C"}; p = {x["k"]: x["s"] for x in perto if x["cp"] == "P"}
        par = [k for k in c if k in p and abs(k / Fref - 1) < 0.01]
        if not par: continue
        k0 = min(par, key=lambda k: abs(c[k] - p[k])); Fs = round(k0 + c[k0] - p[k0], 1)
        err = max(abs((c[k] - p[k]) - (Fs - k)) for k in par)
        if err > 3: print("semanal", cod, v, "descartada: paridade não fecha (erro US$", round(err, 1), ")"); continue
        for x in perto: SEM.append({"venc": v.isoformat(), "tipo": "Call" if x["cp"] == "C" else "Put", "strike": x["k"], "settle": x["s"], "delta": None, "oi": x["oi"], "_F": Fs})
        print("semanal", cod, v, "ok:", len(perto), "linhas, vol. ATM", round(base * 100, 1), "% (sexta", round(ivref * 100, 1), "%), futuro", Fs, ", erro de paridade US$", round(err, 2))
_un = {}
for x in SEM:   # mesmo strike/tipo duas vezes (ITM fundo, vol. parecida): fica o de menor prêmio = vencimento mais curto
    ch = (x["venc"], x["tipo"], x["strike"])
    if ch not in _un or x["settle"] < _un[ch]["settle"]: _un[ch] = x
rows += [{k: x[k] for k in ("venc", "tipo", "strike", "settle", "delta", "oi")} for x in _un.values()]
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
