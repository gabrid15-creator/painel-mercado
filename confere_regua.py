#!/usr/bin/env python3
"""Conferente independente da régua do MT5 (mi_regua_mt5.json). Uso: python3 confere_regua.py <pasta dados>. Só leitura."""
import sys, os, json, datetime as dt
p = os.path.join(sys.argv[1], "mi_regua_mt5.json")
if not os.path.exists(p): print("régua MT5: sem arquivo ainda"); sys.exit(0)
falhas, ant, vistos = [], None, []
for d in json.load(open(p)):
    k = d["dia"]; dia = dt.date.fromisoformat(k); vistos.append(k)
    f = lambda m: falhas.append(f"{k}: {m}")
    if dia.weekday() >= 5: f("fim de semana")
    datada = 27.6 * (dt.date(2027, 2, 24) - dia).days / (dt.date(2027, 2, 24) - dt.date(2026, 11, 25)).days
    if abs(d["regua_datada"] - datada) > 0.06: f(f"régua datada {d['regua_datada']} difere de {datada:.2f}")
    if abs(d["mediana_menos_regua"] - (d["mediana"] - d["regua_datada"])) > 0.02: f("diferença errada")
    if not 0 < d["n"] <= 1440: f(f"quantidade de minutos {d['n']}")
    if d["ate"] < d["de"] or d["ate"] - d["de"] > 86400: f("janela maior que um dia")
    travada = ant is not None and abs(d["mediana"] - ant) > 3
    if d["travada"] != travada: f("trava errada")
    valido = d["n"] >= 60 and d["desvio"] <= 1.0 and not travada
    if d["valido"] != valido: f("validade errada")
    if valido: ant = d["mediana"]
if vistos != sorted(set(vistos)): falhas.append("datas repetidas ou fora de ordem")
for x in falhas: print("FALHA", x)
print(f"régua MT5: {len(falhas)} falha(s)"); sys.exit(1 if falhas else 0)
