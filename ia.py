#!/usr/bin/env python3
"""Leitura da IA: lê out/digest.txt e grava out/mi_ia.json (texto geral + um por ativo) com a API da Anthropic.
Roda a cada coleta; chama a API de hora em hora das 6h às 18h (Brasília), à noite só às 20h e à 0h, e sempre depois de um red folder.
Sem a chave ANTHROPIC_API_KEY, não faz nada. Uso: python3 ia.py out"""
import os, sys, json, datetime as dt
from zoneinfo import ZoneInfo
import anthropic

OUT = sys.argv[1] if len(sys.argv) > 1 else "out"
MODEL = os.environ.get("IA_MODELO", "").strip() or "claude-haiku-5-5"
ATIVOS = ["GERAL", "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "XAUUSD", "NAS100"]
BRT = ZoneInfo("America/Sao_Paulo"); agora = dt.datetime.now(BRT)
if not os.environ.get("ANTHROPIC_API_KEY", "").strip():
    print("sem ANTHROPIC_API_KEY: leitura da IA não gerada"); sys.exit(0)

def ler(n):
    p = os.path.join(OUT, n)
    try: return json.load(open(p, encoding="utf-8"))
    except Exception: return []

# ---- precisa reescrever?
ant = ler("mi_ia.json")
ultima = max((dt.datetime.strptime(x["gerado_em"], "%Y-%m-%d %H:%M").replace(tzinfo=BRT) for x in ant if x.get("gerado_em")), default=None)
red_depois = ultima and any(
    x.get("impacto") == "Alto" and ultima < dt.datetime.strptime(x["quando"], "%Y-%m-%d %H:%M").replace(tzinfo=BRT) <= agora - dt.timedelta(minutes=10)
    for x in ler("mi_agenda.json"))
# frequência (horário de Brasília): 6h–18h = de hora em hora; à noite só às 20h e à 0h; red folder = sempre;
# fim de semana parado de sexta 18h a domingo 18h (mercado fechado)
fim_de_semana = (agora.weekday() == 4 and agora.hour >= 18) or agora.weekday() == 5 or (agora.weekday() == 6 and agora.hour < 18)
if 6 <= agora.hour < 18:
    vencida = not ultima or agora - ultima >= dt.timedelta(minutes=55)
else:   # último horário noturno (20h ou 0h) que já passou
    hoje0 = agora.replace(hour=0, minute=0, second=0, microsecond=0)
    marcos = [m for m in (hoje0 - dt.timedelta(hours=4), hoje0, hoje0 + dt.timedelta(hours=20)) if m <= agora]
    vencida = not ultima or ultima < max(marcos)
formato_velho = bool(ant) and ant[0].get("formato") != 2   # formato novo (sem viés): refaz uma vez
if ultima and not red_depois and not formato_velho and (not vencida or fim_de_semana):
    print(f"leitura de {ultima:%d/%m %H:%M} ainda vale"); sys.exit(0)

dig = open(os.path.join(OUT, "digest.txt"), encoding="utf-8").read()
prompt = (
    "Você é o estrategista-chefe de uma mesa institucional de câmbio, ouro e índices. Abaixo estão os dados do painel agora "
    f"({agora:%d/%m/%Y %H:%M}, horário de Brasília): preço e variação de cada ativo, faixas esperadas pela volatilidade (±1σ e ±2σ do dia, semana e mês), "
    "regime de correlação com dólar e juros, 0DTE do ouro, radar institucional (liquidez do Fed, curva do VIX, MOVE, NFCI, juros), últimos dados oficiais dos EUA, red folder da semana e manchetes.\n"
    "REGRA: testes estatísticos mostraram que NENHUM dado disponível prevê a direção do preço; só o TAMANHO do movimento é previsível. "
    "Portanto NÃO dê viés de alta ou de baixa, não diga que o preço tende a subir ou cair e não use palavras como bullish/bearish/altista/baixista.\n"
    "Escreva em português do Brasil, direto ao ponto, 2 a 3 frases por item:\n"
    "- GERAL: o ambiente agora (volatilidade alta ou baixa, estresse no radar institucional) e o próximo evento que pode aumentar o movimento.\n"
    "- Cada ativo: quanto ele deve andar hoje e na semana (faixa ±1σ com os preços), se a volatilidade está acima ou abaixo do normal, o que o move agora (regime com DXY/juros) "
    "e o evento de risco mais próximo. No ouro, cite teto, piso e gamma flip do 0DTE se houver.\n"
    "Use só o que está nos dados; não invente números nem eventos. Trate eventos que já passaram como passados e os futuros como futuros, comparando com a data e hora acima.\n"
    'Responda APENAS com um JSON: uma lista de 7 objetos {"ativo": ..., "texto": ...}, na ordem ' + ", ".join(ATIVOS) + ".\n\nDADOS:\n" + dig)

client = anthropic.Anthropic()
try:
    resp = client.messages.create(model=MODEL, max_tokens=8000, output_config={"effort": "medium"},
                                  messages=[{"role": "user", "content": prompt}])
except anthropic.APIStatusError as e:
    print(f"API recusou ({e.status_code}): {e.message}"); sys.exit(0)
except anthropic.APIConnectionError:
    print("sem conexão com a API"); sys.exit(0)
if resp.stop_reason == "refusal":
    print("a IA recusou; leitura anterior mantida"); sys.exit(0)
txt = "".join(b.text for b in resp.content if b.type == "text")
try:
    itens = json.loads(txt[txt.index("["): txt.rindex("]") + 1])
    rows = [{"ativo": x["ativo"], "formato": 2, "texto": x["texto"].strip(), "gerado_em": f"{agora:%Y-%m-%d %H:%M}"} for x in itens if x.get("ativo") in ATIVOS and x.get("texto")]
except Exception as e:
    print("resposta fora do formato; leitura anterior mantida:", e); sys.exit(0)
if len(rows) < 5:
    print("resposta incompleta; leitura anterior mantida"); sys.exit(0)
json.dump(rows, open(os.path.join(OUT, "mi_ia.json"), "w", encoding="utf-8"), ensure_ascii=False)
print(f"leitura da IA gerada: {len(rows)} textos · tokens {resp.usage.input_tokens} entrada / {resp.usage.output_tokens} saída")
