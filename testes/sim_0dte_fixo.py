import sys, re, json, math, random, datetime as dt, os, subprocess, statistics as st
S = sys.argv[1]; out = f"{S}/sim_out"; os.makedirs(out, exist_ok=True)
src = open("/home/user/painel-mercado/coletor.py").read()
# só b_precos (preços/SPOT) e b_0dte
src = re.sub(r"^(b_tsy\(\); b_liq\(\); b_bund\(\); b_fred\(\))$", "", src, flags=re.M)
src = src.replace("b_precos(); b_tsy(); b_liq(); b_bund(); b_fred()", "b_precos()")
for n in ("b_macro","b_ativos","b_cot","b_dolar","b_cta","b_regime","b_faixa","b_0dte_iene","b_valid","b_fg","b_agenda","b_eua","b_surpresa","b_news","b_score"):
    src = re.sub(rf"^{n}\(\)$", "pass", src, flags=re.M)
# horário forçado (UTC) e Cboe sintético
src = src.replace("NOW = dt.datetime.now(BRT)", f"NOW = dt.datetime.fromisoformat(os.environ['SIM_UTC']).replace(tzinfo=dt.timezone.utc).astimezone(BRT)")
src = src.replace("https://cdn.cboe.com/api/global/delayed_quotes/options/GLD.json", "file://" + S + "/gld_fake.json")
open(f"{S}/coletor_sim.py", "w").write(src)
def fake(seed, hora_ny):
    rnd = random.Random(seed); base = random.Random(7)   # OI fixo (seed 7), volume/cotação mudam a cada coleta
    P = 334.9 + rnd.uniform(-1, 1); opts = []
    for k in range(320, 350):
        for cp in "CP":
            oi = int(base.expovariate(1 / 150)) + (1500 if k in (335, 345, 325) else 0) + (800 if (cp == "P" and k == 328) else 0)
            vol = int(rnd.expovariate(1 / (40 + 200 * hora_ny)))
            iv = 0.22 + rnd.uniform(-0.04, 0.04) + abs(k - 335) * 0.004
            m = max(0.05, (max(0, P - k) if cp == "C" else max(0, k - P)) + 0.55 * P * iv * math.sqrt(1.0 / 252) * math.exp(-((k - P) ** 2) / (2 * 1.2)) )
            m *= 1 + rnd.uniform(-0.08, 0.08)
            opts.append({"option": f"GLD261124{cp}00{k:03d}000", "open_interest": oi, "volume": vol, "iv": iv, "bid": round(m * .95, 2), "ask": round(m * 1.05, 2), "last_trade_price": round(m, 2), "delta": 0.5})
    return {"data": {"current_price": round(P, 2), "close": 334.0, "last_trade_time": None, "options": opts}}
runs = ["13:35", "13:40", "13:45", "13:50", "13:55", "14:00", "14:05", "14:30", "15:30", "19:45"]   # UTC (NY = UTC−5): 08:35 … 14:45
for i, h in enumerate(runs):
    ny = dt.datetime.fromisoformat(f"2026-11-24T{h}:00") - dt.timedelta(hours=5)
    d = fake(100 + i, (ny.hour + ny.minute / 60 - 9.5) / 6.5)
    d["data"]["last_trade_time"] = ny.strftime("%Y-%m-%dT%H:%M:%S")
    json.dump(d, open(f"{S}/gld_fake.json", "w"))
    r = subprocess.run([sys.executable, f"{S}/coletor_sim.py", out], env={**os.environ, "SIM_UTC": f"2026-11-24T{h}:00"}, capture_output=True, text=True, timeout=280)
    try:
        z = json.load(open(f"{out}/mi_0dte.json"))[0]
        print(ny.strftime("%H:%M NY"), z["fixacao"], "| teto", z["call_wall"], "piso", z["put_wall"], "flip", z["gamma_flip"], "mp", z["max_pain"], "faixa", z["faixa"], "| vivo teto/piso/flip", z["vivo"]["call_wall"], z["vivo"]["put_wall"], z["vivo"]["gamma_flip"])
    except Exception as e: print(h, "erro", e, r.stderr[-300:])
