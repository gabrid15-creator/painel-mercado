#!/usr/bin/env python3
"""Travas das opções do ouro (só leitura; escrito pela área Estratégias em 27/11/2026). Uso: python3 confere_opcoes.py <pasta da branch dados>
Sai com código 1 se algum nível publicado não puder ser usado. A mesma trava roda dentro do coletor (travas_0dte); este é o conferente independente."""
import sys, json, os, datetime as dt

D = sys.argv[1]
# GC fev - XAUUSD Vantage: 27,6 medido em 25/11/2026. O desconto é custo de carregar: encolhe até o vencimento do contrato
# (estimativa linear, uns 0,30 por dia). Remedir 1 vez por semana e a cada troca de contrato (aqui e em REGUA no coletor.py).
BASE_MEDIDA, MEDIDO_EM, VENCE, TOL = 27.6, dt.date(2026, 11, 25), dt.date(2027, 2, 24), 3.0
ler = lambda f: json.load(open(os.path.join(D, f), encoding="utf-8"))
z = ler("mi_0dte.json")[0]; c = z.get("cme") or {}; p = z["ouro"]; erros = []
fixo = str(z.get("fixacao", "")).startswith("fixo")
niveis = ("call_wall", "put_wall", "gamma_flip", "max_pain", "faixa", "regime")

def e(cond, msg):
    if cond: erros.append(msg)

if not z.get("abertos") and not fixo:   # com nível já fixado às 10h NY, uma falha posterior da fonte não o invalida
    com = [k for k in niveis if z.get(k) is not None]
    e(com, f"GLD sem contratos em aberto, mas publica: {', '.join(com)}")
if not fixo:
    e(z.get("call_wall") is not None and z["call_wall"] < p * 0.999, f"GLD teto {z.get('call_wall')} abaixo do preço {p}")
    e(z.get("put_wall") is not None and z["put_wall"] > p * 1.001, f"GLD piso {z.get('put_wall')} acima do preço {p}")
    f = z.get("faixa"); e(f and not f[0] <= p <= f[1], f"GLD faixa {f} não contém o preço {p}")
for nome, d in (("GLD", z), ("CME", c)):
    m = d.get("max_pain"); e(m is not None and abs(m / p - 1) > 0.10, f"{nome} max pain {m} a mais de 10% do preço")
if c and not c.get("sem_dado"):
    cad = [o for o in ler("ouro_cadeia.json") if o["venc"] == z["vencimento"]]
    sp = p + c["base"]
    for tipo, campo, lado in (("C", "call_wall", lambda k: k >= sp), ("P", "put_wall", lambda k: k <= sp)):
        tem = any(o["tipo"].startswith(tipo) and o["oi"] > 0 and lado(o["strike"]) and abs(o["strike"] / sp - 1) <= 0.029 for o in cad)
        e(tem and c.get(campo) is None, f"CME {campo} vazio, mas há contratos perto do preço")
    top = max((r[0] for r in c.get("perfil", [])), default=0)
    fora = [o for o in cad if o["oi"] > 0 and o["strike"] - c["base"] > top + 1 and abs(o["strike"] / sp - 1) <= 0.029]
    e(fora, f"CME gráfico corta {len(fora)} linhas com contratos acima de {top}")
    dia = dt.date.fromisoformat(z["vencimento"])
    esperada = round(BASE_MEDIDA * (VENCE - dia).days / (VENCE - MEDIDO_EM).days, 1)
    e(abs(c["base"] - esperada) > TOL, f"régua: painel desconta {c['base']}, esperado {esperada}")
    e((dia - MEDIDO_EM).days > 7, f"régua medida há mais de 7 dias ({MEDIDO_EM}): medir de novo no MT5")
e(not z.get("preco_hora"), "preço do ouro sem horário (campo preco_hora)")

print(f"{z['vencimento']} {z['atualizado']} ouro {p}: {len(erros)} falha(s)")
for x in erros: print(" -", x)
sys.exit(1 if erros else 0)
