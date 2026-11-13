#!/usr/bin/env python3
"""Carrega o arquivo mais recente de cme/opcoes_<pregão>.json (lido do PDF da CME por cme_pdf.py) em out/ouro_cadeia.json
e out/ouro_boletim.json, se for mais novo que o que já está em out/. Uso: python3 cme_local.py out"""
import sys, os, glob, json
OUT = sys.argv[1] if len(sys.argv) > 1 else "out"
arqs = sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cme", "opcoes_*.json")))
if not arqs: print("sem arquivo da CME em cme/"); sys.exit(0)
d = json.load(open(arqs[-1])); novo = d["ouro_boletim"][0]["data_pregao"]
try: atual = json.load(open(os.path.join(OUT, "ouro_boletim.json")))[0]["data_pregao"]
except Exception: atual = ""
if novo < atual: print("CME em out/ já é mais nova:", atual); sys.exit(0)
for k in ("ouro_cadeia", "ouro_boletim"): json.dump(d[k], open(os.path.join(OUT, k + ".json"), "w"), ensure_ascii=False, separators=(",", ":"))
print("CME carregada:", os.path.basename(arqs[-1]))
