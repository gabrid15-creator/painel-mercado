#!/usr/bin/env python3
"""Leitura da IA: lê out/digest.txt e grava out/mi_ia.json usando a API da Anthropic.
Roda só se a chave ANTHROPIC_API_KEY existir. Uso: python3 ia.py out"""
import os, sys, json, urllib.request, datetime as dt
from zoneinfo import ZoneInfo

OUT = sys.argv[1] if len(sys.argv) > 1 else "out"
KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
MODEL = os.environ.get("IA_MODELO", "").strip() or "claude-sonnet-4-5"
if not KEY:
    print("sem ANTHROPIC_API_KEY: leitura da IA não gerada"); sys.exit(0)
dig = open(os.path.join(OUT, "digest.txt"), encoding="utf-8").read()
agora = dt.datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M")
prompt = (
    "Você é analista de uma mesa institucional de câmbio, ouro e índices. Abaixo estão os dados do painel (score 0-100 por ativo com os fatores, "
    "agenda red folder e manchetes). Escreva em português do Brasil, direto ao ponto, 2 a 3 frases por item: o viés e o score, os 2 ou 3 fatores que "
    "mais pesam, o principal risco (evento red folder próximo ou notícia relevante) e o que esperar. Use só o que está nos dados; não invente números. "
    "Responda APENAS com um JSON: lista de 7 objetos {\"ativo\": ..., \"texto\": ...} com os ativos GERAL, EURUSD, GBPUSD, USDJPY, USDCHF, XAUUSD, NAS100 "
    "(GERAL = clima do mercado no dia e eventos-chave).\n\nDADOS:\n" + dig)
req = urllib.request.Request("https://api.anthropic.com/v1/messages", method="POST",
    headers={"x-api-key": KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
    data=json.dumps({"model": MODEL, "max_tokens": 2000, "messages": [{"role": "user", "content": prompt}]}).encode())
with urllib.request.urlopen(req, timeout=120) as r:
    txt = "".join(c.get("text", "") for c in json.loads(r.read())["content"])
txt = txt[txt.index("["): txt.rindex("]") + 1]
rows = [{"ativo": x["ativo"], "texto": x["texto"].strip(), "gerado_em": agora} for x in json.loads(txt)]
json.dump(rows, open(os.path.join(OUT, "mi_ia.json"), "w"), ensure_ascii=False)
print("leitura da IA gerada:", len(rows))
