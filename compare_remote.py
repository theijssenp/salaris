#!/usr/bin/env python3
"""Vergelijk lokale CBS-JSON's met verse CBS-data (86355NED) voor watchdog-refresh."""
import json, os, re, sys, urllib.request
from datetime import datetime

WS = os.path.dirname(os.path.abspath(__file__))
FIELDS = ["k_25ePercentiel_2", "k_50ePercentielMediaan_3", "k_75ePercentiel_4", "Werknemer_1"]

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "salaris.hodc.nl-watchdog/1.0"})
    with urllib.request.urlopen(req, timeout=60) as f:
        return json.load(f)

print("=== Mtimes workspace ===")
for f in sorted(os.listdir(WS)):
    p = os.path.join(WS, f)
    if os.path.isfile(p) and not f.startswith("."):
        st = os.stat(p)
        print(f"  {f:36s} {st.st_size:>9} B  {datetime.fromtimestamp(st.st_mtime):%Y-%m-%d %H:%M:%S}")
st = os.stat(os.path.join(WS, ".cbs_last_modified"))
print(f"  .cbs_last_modified: {open(os.path.join(WS, '.cbs_last_modified')).read()!r}  mtime {datetime.fromtimestamp(st.st_mtime):%Y-%m-%d %H:%M:%S}")

print("\n=== Lokale data-stats ===")
for y in (2025, 2024):
    d = json.load(open(os.path.join(WS, f"cbs_{y}.json")))["value"]
    met = sum(1 for r in d if r.get("k_50ePercentielMediaan_3") is not None)
    print(f"  {y}: {len(d)} rijen, {met} met mediaan-loon")

print("\n=== CBS actueel ===")
info = fetch("https://opendata.cbs.nl/ODataApi/odata/86355NED/TableInfos")["value"][0]
print("  Modified:", info["Modified"], "| Title:", info["Title"])

per = fetch("https://opendata.cbs.nl/ODataApi/odata/86355NED/Perioden")["value"]
jaren = sorted({x["Key"][:4] for x in per if x["Key"].endswith("JJ00")}, reverse=True)
print("  jaren in tabel:", jaren)

for y in (2025, 2024):
    if f"{y}JJ00" not in {x["Key"] for x in per}:
        print(f"  {y}: NIET in remote Perioden!")
        continue
    remote = fetch(f"https://opendata.cbs.nl/ODataApi/odata/86355NED/TypedDataSet?$filter=Perioden%20eq%20%27{y}JJ00%27")["value"]
    local = {r["Beroep"]: r for r in json.load(open(os.path.join(WS, f"cbs_{y}.json")))["value"]}
    rmap = {r["Beroep"]: r for r in remote}
    metr = sum(1 for r in remote if r.get("k_50ePercentielMediaan_3") is not None)
    metl = sum(1 for r in local.values() if r.get("k_50ePercentielMediaan_3") is not None)
    only_l = sorted(set(local) - set(rmap)); only_r = sorted(set(rmap) - set(local))
    diffs = []
    for k in sorted(set(local) & set(rmap)):
        for fn in FIELDS:
            if local[k].get(fn) != rmap[k].get(fn):
                diffs.append((k, fn, local[k].get(fn), rmap[k].get(fn)))
    print(f"  {y}: local {len(local)} ({metl} loon) | remote {len(remote)} ({metr} loon) | alleen-lokaal {len(only_l)} | alleen-remote {len(only_r)} | veld-diffs: {len(diffs)}")
    if only_l: print("    alleen-lokaal:", only_l[:10])
    if only_r: print("    alleen-remote:", only_r[:10])
    for d in diffs[:10]:
        print("    diff:", d)

cl_remote = fetch("https://opendata.cbs.nl/ODataApi/odata/86355NED/Beroep")["value"]
cl_local = json.load(open(os.path.join(WS, "cbs_beroepen_codelist.json")))["value"]
rk = {x["Key"] for x in cl_remote}; lk = {x["Key"] for x in cl_local}
print(f"\n  codelist: local {len(lk)} | remote {len(rk)} | nieuw: {sorted(rk-lk)} | verdwenen: {sorted(lk-rk)}")

# Sitemap + vhost-overzicht
print("\n=== sitemap.xml (lokaal) ===")
print(open(os.path.join(WS, "sitemap.xml")).read())
print("=== vhost /var/www/salaris.hodc.nl ===")
for f in sorted(os.listdir("/var/www/salaris.hodc.nl")):
    p = os.path.join("/var/www/salaris.hodc.nl", f)
    print(f"  {f:36s} {os.path.getsize(p):>9} B  {datetime.fromtimestamp(os.path.getmtime(p)):%Y-%m-%d %H:%M:%S}")