import json,urllib.request,datetime as dt,math,statistics as st
from zoneinfo import ZoneInfo
NY=ZoneInfo("America/New_York")
def y(s,r,i):
    u=f"https://query2.finance.yahoo.com/v8/finance/chart/{s}?range={r}&interval={i}"
    q=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=60))["chart"]["result"][0]
    o=q["indicators"]["quote"][0]
    return [(t,o["open"][k],o["high"][k],o["low"][k],o["close"][k]) for k,t in enumerate(q["timestamp"]) if o["close"][k]]
gc=y("GC%3DF","730d","1h"); gv=y("%5EGVZ","5y","1d")
gvz={dt.datetime.fromtimestamp(t,NY).date():c for t,_,_,_,c in gv}
dias={}
for t,o,h,l,c in gc:
    d=dt.datetime.fromtimestamp(t,NY); s=(d+dt.timedelta(hours=6)).date()  # sessão começa 18h NY
    if s.weekday()>4: continue
    dias.setdefault(s,[]).append((o,h,l,c))
rows=[]
for s,b in sorted(dias.items()):
    if len(b)<18: continue
    prev=[d for d in gvz if d<s]
    if not prev: continue
    g=gvz[max(prev)]; ab=b[0][0]; fe=b[-1][3]
    sig=ab*g/100/math.sqrt(252)
    cam=sum(abs(x[3]-x[0]) for x in b)+sum(abs(b[i][0]-b[i-1][3]) for i in range(1,len(b)))
    hi=max(x[1] for x in b); lo=min(x[2] for x in b)
    rows.append(dict(s=s,sig=sig,sigp=g,desl=abs(fe-ab),rng=hi-lo,ef=abs(fe-ab)/cam,cam=cam))
# sigma relativo à média dos 60 dias anteriores (tira a tendência do nível)
for i,r in enumerate(rows): 
    p=[x["sig"] for x in rows[max(0,i-60):i]]; r["rel"]=r["sig"]/st.mean(p) if len(p)>=20 else None
R=[r for r in rows if r["rel"]]
print("dias",len(R),R[0]["s"],R[-1]["s"])
def terc(key):
    v=sorted(r[key] for r in R); a,b=v[len(v)//3],v[2*len(v)//3]
    for nome,f in (("curto",lambda r:r[key]<=a),("medio",lambda r:a<r[key]<=b),("longo",lambda r:r[key]>b)):
        g=[r for r in R if f(r)]
        print(f" {key} {nome:6} n={len(g):3} σ$={st.mean(x['sig'] for x in g):5.1f} desloc$={st.mean(x['desl'] for x in g):5.1f} range$={st.mean(x['rng'] for x in g):5.1f} caminho$={st.mean(x['cam'] for x in g):6.1f} efic={st.mean(x['ef'] for x in g):.3f} %pingpong(ef<=.12)={100*sum(x['ef']<=.12 for x in g)/len(g):4.1f} %tend(ef>=.30)={100*sum(x['ef']>=.30 for x in g)/len(g):4.1f} desl/σ={st.mean(x['desl']/x['sig'] for x in g):.2f}")
terc("sig"); terc("rel")
# correlações e t
def corr(a,b):
    ma,mb=st.mean(a),st.mean(b); c=sum((x-ma)*(y-mb) for x,y in zip(a,b)); return c/math.sqrt(sum((x-ma)**2 for x in a)*sum((y-mb)**2 for y in b))
n=len(R)
for k in ("desl","rng","ef"):
    for s in ("sig","rel"):
        r=corr([x[s] for x in R],[x[k] for x in R]); print(f"corr {s}×{k}: r={r:.3f} t={r*math.sqrt((n-2)/(1-r*r)):.1f}")
# metades
h=n//2
for parte,G in (("1a metade",R[:h]),("2a metade",R[h:])):
    r=corr([x["rel"] for x in G],[x["ef"] for x in G]); r2=corr([x["sig"] for x in G],[x["desl"] for x in G]); print(parte,"rel×efic",round(r,3),"σ$×desloc",round(r2,3))
