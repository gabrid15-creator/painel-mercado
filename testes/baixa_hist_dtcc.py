import urllib.request, zipfile, io, csv, gzip, json, datetime as dt, os, time, sys
PARES = {"USD/JPY", "JPY/USD", "EUR/USD", "USD/EUR", "USD/CHF", "CHF/USD", "GBP/USD", "USD/GBP"}
d, fim = dt.date(2024, 10, 15), dt.date(2026, 11, 13)
while d <= fim:
    if d.weekday() < 5:
        f = f"hist/{d}.json.gz"
        if not os.path.exists(f):
            for t in range(3):
                try:
                    b = urllib.request.urlopen(urllib.request.Request(f"https://pddata.dtcc.com/ppd/api/report/cumulative/cftc/CFTC_CUMULATIVE_FOREX_{d:%Y_%m_%d}.zip", headers={"User-Agent": "Mozilla/5.0"}), timeout=90).read()
                    z = zipfile.ZipFile(io.BytesIO(b))
                    rows = [r for r in csv.DictReader(io.TextIOWrapper(z.open(z.namelist()[0]), "utf-8")) if r.get("UPI FISN", "").startswith("NA/O Van ") and r.get("Strike price currency/currency pair") in PARES]
                    json.dump(rows, gzip.open(f, "wt")); print(d, len(rows), flush=True); break
                except urllib.error.HTTPError as e:
                    if e.code == 404: json.dump([], gzip.open(f, "wt")); print(d, "404", flush=True); break
                    time.sleep(5)
                except Exception as e: print(d, "erro", e, flush=True); time.sleep(5)
    d += dt.timedelta(days=1)
print("FIM", flush=True)
