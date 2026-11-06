#!/usr/bin/env python3
"""Baixa o arquivo de opções mais recente da pasta pública do Google Drive (gravado pela tarefa noturna do Claude)
e separa em out/<nome>.json (op_cadeia, op_paredes, op_boletim, ouro_cadeia, ouro_boletim, ouro_etf). Uso: python3 opcoes_drive.py out"""
import sys, os, re, json, html, urllib.request
OUT = sys.argv[1] if len(sys.argv) > 1 else "out"
PASTA = "1GTHAZCrqQe_LYxf8OuR3zwqncQmHUunx"
CHAVES = ("op_cadeia", "op_paredes", "op_boletim", "ouro_cadeia", "ouro_boletim", "ouro_etf")
UA = {"User-Agent": "Mozilla/5.0"}

def get(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=20) as r: return r.read()

try:
    pg = get(f"https://drive.google.com/embeddedfolderview?id={PASTA}").decode("utf-8", "replace")
except Exception as e:
    print("pasta do Drive indisponível:", e); sys.exit(0)
itens = [(html.unescape(t).strip(), i) for i, t in re.findall(r'id="entry-([\w-]+)".*?class="flip-entry-title">([^<]+)<', pg, re.S)]
itens = sorted(x for x in itens if re.match(r"opcoes_\d{4}-\d{2}-\d{2}", x[0]))
if not itens: print("nenhum arquivo de opções na pasta (ou pasta não pública)"); sys.exit(0)
nome, fid = itens[-1]
marca = os.path.join(OUT, "opcoes_fonte.json")
try: ja = json.load(open(marca)).get("arquivo")
except Exception: ja = None
if ja == nome: print("opções já carregadas:", nome); sys.exit(0)
try:
    d = json.loads(get(f"https://drive.google.com/uc?export=download&id={fid}"))
except Exception as e:
    print("não consegui baixar", nome, e); sys.exit(0)
n = 0
for k in CHAVES:
    if isinstance(d.get(k), list) and d[k]:
        json.dump(d[k], open(os.path.join(OUT, k + ".json"), "w"), ensure_ascii=False, separators=(",", ":")); n += 1
json.dump({"arquivo": nome}, open(marca, "w"))
print(f"opções de {nome}: {n} arquivos")
