import math, datetime as dt
from zoneinfo import ZoneInfo
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, matplotlib.dates as md
from yf import chart
exec(open("faixa_bt.py").read().split("ATV = {")[0])
NY = ZoneInfo("America/New_York"); BR = ZoneInfo("America/Sao_Paulo")
b = sorted(chart("GC=F", "5m", "60d")); g = {d: c for d, o, h, l, c in diario("^GVZ")}
d = dt.date(2026, 11, 13); ini = dt.datetime.combine(d - dt.timedelta(days=1), dt.time(18, 0), NY); fim = dt.datetime.combine(d, dt.time(17, 0), NY)
dia = [x for x in b if ini.timestamp() <= x[0] < fim.timestamp()]
ab = dia[0][1]; sd = g[max(k for k in g if k < d)] / 100 / math.sqrt(252)
t = [dt.datetime.fromtimestamp(x[0], BR) for x in dia]; px = [x[4] for x in dia]
fig, ax = plt.subplots(figsize=(11, 5.6), dpi=130)
ax.plot(t, px, color="#222", lw=1.3, label="ouro (GC, 5 min)")
cores = {0.5: "#c98a12", 1: "#2a9d8f", 1.5: "#8b5a2b"}
for k, c in cores.items():
    for s in (1, -1):
        L = ab * math.exp(s * k * sd); ax.axhline(L, color=c, lw=1.2, ls="--")
        ax.annotate(f"mapa {'+' if s > 0 else '−'}{k:g}σ {L:,.0f}".replace(",", "."), xy=(1.01, L), xycoords=("axes fraction", "data"), color=c, va="center", fontsize=9, fontweight="bold")
ax.axhline(ab, color="#888", lw=1); ax.annotate(f"abertura {ab:,.0f}".replace(",", "."), xy=(1.01, ab), xycoords=("axes fraction", "data"), color="#666", va="center", fontsize=9)
for L, nm in ((3837.4, "0DTE GLD faixa"), (3928.2, "0DTE GLD faixa")):
    ax.axhline(L, color="#7b5cc4", lw=1.4, ls=":"); ax.annotate(f"{nm} {L:,.0f}".replace(",", "."), xy=(1.01, L), xycoords=("axes fraction", "data"), color="#7b5cc4", va="center", fontsize=9, fontweight="bold")
# quantas vezes o preço "quicou" (tocou e voltou ≥ 0,15σ) em cada nível e em níveis intermediários
def quiques(L, lado):
    n, armado = 0, False
    for x in dia:
        if (x[3] <= L if lado < 0 else x[2] >= L): armado = True
        elif armado and (x[4] >= L * math.exp(0.15 * sd) if lado < 0 else x[4] <= L * math.exp(-0.15 * sd)): n += 1; armado = False
    return n
linhas = []
for k in (0.25, 0.5, 0.75, 1, 1.25, 1.5):
    L = ab * math.exp(-k * sd); linhas.append(f"−{k:g}σ ({L:,.0f}): {quiques(L, -1)} quique(s)".replace(",", "."))
ax.set_title("Ouro, sexta 13/11/2026 · níveis do mapa (σ do GVZ a partir da abertura 20h de Brasília)", fontsize=11)
ax.xaxis.set_major_formatter(md.DateFormatter("%H:%M", tz=BR)); ax.set_xlabel("horário de Brasília"); ax.grid(alpha=.25)
ax.text(0.01, 0.02, "Quiques (tocou e voltou ≥ 0,15σ):\n" + "\n".join(linhas), transform=ax.transAxes, fontsize=8.5, va="bottom", bbox=dict(fc="white", ec="#ccc"))
plt.subplots_adjust(right=0.80); plt.savefig("/home/user/painel-mercado/exemplo_ouro_13-11.png"); print("\n".join(linhas))
