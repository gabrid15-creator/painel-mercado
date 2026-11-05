import datetime as dt, json
GB=[0,3,7,11,14,17,23,29,35,41,44,47,50,53,56,59,65,71,77,83,89,97,100]
DAYS=[1,3,7,11,14,17,23,29]
ANCH={1:8,2:7,3:6,4:5,5:4,6:3,7:2,8:1,9:9,10:8,11:7,12:6}
WD=['seg','ter','qua','qui','sex','sáb','dom']
def off(d): return d.weekday()>=5 or (d.month==12 and d.day==25) or (d.month==1 and d.day==1)
def info(d):
    t=[]
    if d.day in DAYS: t.append(f"Dia {d.day}")
    if d.month in GB: t.append(f"Mês {d.month:02d}")
    if d.day+d.month in GB: t.append(f"D+M {d.day+d.month:02d}")
    if abs(d.day-d.month) in GB: t.append(f"|D−M| {abs(d.day-d.month):02d}")
    amd=d.year%100+d.month+d.day
    if amd in GB: t.append(f"A+M+D {amd:02d}")
    return t
def anchor(y,m):
    a=dt.date(y,m,ANCH[m])
    if a.weekday()==5: a+=dt.timedelta(2)
    elif a.weekday()==6: a+=dt.timedelta(1)
    return a
def gm(d):
    a=anchor(d.year,d.month)
    if d<a: a=anchor(d.year-1 if d.month==1 else d.year, 12 if d.month==1 else d.month-1)
    rel=(d-a).days+1
    return rel, a, (rel==1 or rel in DAYS)
rows=[]
d=dt.date(2026,11,1); end=dt.date(2027,12,31)
while d<=end:
    if not off(d):
        t=info(d)
        k=d-dt.timedelta(1)
        while off(k):
            tk=info(k)
            if tk:
                nm='sáb' if k.weekday()==5 else 'dom' if k.weekday()==6 else 'feriado'
                t+= [f"{x} ({nm})" for x in tk if x not in t]
            k-=dt.timedelta(1)
        rel,a,okh=gm(d)
        gb=bool(t)
        if gb or okh:
            hop = (f"dia {rel}" + (" (abertura)" if rel==1 else "")) if okh else ""
            res = ("★ Goldbach + Hopiplaka " if gb and okh else "Goldbach" if gb else "Hopiplaka ") + hop
            rows.append({"data":d.isoformat(),"dia_semana":WD[d.weekday()],
              "tipo":"Goldbach + Hopiplaka" if gb and okh else ("Goldbach" if gb else "Hopiplaka"),
              "goldbach":" · ".join(t),"hopiplaka":hop,"resumo":res,"dia_mes_hopiplaka":rel})
    d+=dt.timedelta(1)
json.dump(rows,open('goldbach_dias.json','w'),ensure_ascii=False,indent=0)
# ICS
now=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
L=["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//Jireh Goldbach//PT-BR","CALSCALE:GREGORIAN","X-WR-CALNAME:Goldbach / Hopiplaka","X-WR-TIMEZONE:America/Sao_Paulo"]
def esc(s): return s.replace('\\','\\\\').replace(',','\\,').replace(';','\\;')
for r in rows:
    d=dt.date.fromisoformat(r['data'])
    desc="\\n".join(x for x in [("Goldbach: "+r['goldbach']) if r['goldbach'] else "", ("Hopiplaka: "+r['hopiplaka']) if r['hopiplaka'] else ""] if x)
    L+=["BEGIN:VEVENT",f"UID:gb-{r['data']}@jireh-goldbach",f"DTSTAMP:{now}",
        f"DTSTART;VALUE=DATE:{d:%Y%m%d}",f"DTEND;VALUE=DATE:{d+dt.timedelta(1):%Y%m%d}",
        "SUMMARY:"+esc(r['resumo']),
        "DESCRIPTION:"+esc(desc).replace('\\\\n','\\n'),"TRANSP:TRANSPARENT",
        "BEGIN:VALARM","ACTION:DISPLAY","DESCRIPTION:"+esc(r['resumo']),"TRIGGER:-PT3H","END:VALARM","END:VEVENT"]
L.append("END:VCALENDAR")
open('goldbach_hopiplaka.ics','w').write("\r\n".join(L)+"\r\n")
from collections import Counter
print(len(rows),Counter(r['tipo'] for r in rows))
for r in rows[:12]: print(r['data'],r['dia_semana'],'|',r['resumo'],'|',r['goldbach'])
