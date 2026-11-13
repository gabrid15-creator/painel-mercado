#!/usr/bin/env python3
"""Carrega os arquivos mais recentes lidos dos PDFs da CME (cme_pdf.py e cme_pdf_iene.py) em out/:
cme/opcoes_<pregão>.json → ouro_cadeia/ouro_boletim · cme/iene_<pregão>.json → iene_cadeia/iene_boletim.
Só substitui se o pregão for igual ou mais novo que o já carregado. Uso: python3 cme_local.py out"""
import sys, os, glob, json
OUT = sys.argv[1] if len(sys.argv) > 1 else "out"
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cme")
for padrao, pre in (("opcoes_*.json", "ouro"), ("iene_*.json", "iene")):
    arqs = sorted(glob.glob(os.path.join(BASE, padrao)))
    if not arqs: print("sem arquivo", padrao); continue
    d = json.load(open(arqs[-1])); novo = d[pre + "_boletim"][0]["data_pregao"]
    try: atual = json.load(open(os.path.join(OUT, pre + "_boletim.json")))[0]["data_pregao"]
    except Exception: atual = ""
    if novo < atual: print(pre, "em out/ já é mais nova:", atual); continue
    for k in (pre + "_cadeia", pre + "_boletim"): json.dump(d[k], open(os.path.join(OUT, k + ".json"), "w"), ensure_ascii=False, separators=(",", ":"))
    print("CME carregada:", os.path.basename(arqs[-1]))
