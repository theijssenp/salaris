#!/usr/bin/env python3
"""
Watchdog voor salaris.hodc.nl/salaris-per-beroep — CBS tabel 86355NED.

Principe (watchdog-pattern, STILE output):
- Checkt alleen of de CBS-tabel een nieuw 'Modified'-timestamp heeft dan de laatste run
- GEEN wijziging → script zwijgt (exit 0, geen output) → cron-job verstuurt NIKS
- WEL wijziging → runt een volledige data-test (fetch + build-validatie) ALLEEN DAN:
  - Test slaagt  → print "wijziging gedetecteerd + test OK" → agent-runs refreshen de site
  - Test faalt   → print foutmelding → agent alarmeert
- Script zelf crasht/timeout → cron verstuurt foutalert (watchdog kan niet stilletjes doodgaan)

Gebruik:
  python3 ~/hodc/salaris-beroepen/cbs_watchdog.py            # check-modus (cron)
  python3 ~/hodc/salaris-beroepen/cbs_watchdog.py --reset    # baseline opnieuw vastleggen
  python3 ~/hodc/salaris-beroepen/cbs_watchdog.py --force    # test-fase geforceerd draaien

State: ~/hodc/salaris-beroepen/.cbs_last_modified
"""
import json
import sys
import os
import urllib.request
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, ".cbs_last_modified")
TABEL = "86355NED"
INFO_URL = f"https://opendata.cbs.nl/ODataApi/odata/{TABEL}/TableInfos"
DATA_URL = f"https://opendata.cbs.nl/ODataApi/odata/{TABEL}/TypedDataSet?$filter=Perioden%20eq%20%27{{jaar}}JJ00%27"


def fetch_json(url):
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": "salaris.hodc.nl-watchdog/1.0"})
    with urllib.request.urlopen(req, timeout=60) as f:
        return json.load(f)


def current_modified():
    d = fetch_json(INFO_URL)["value"][0]
    return d["Modified"], d["Title"]


def read_state():
    if os.path.exists(STATE):
        return open(STATE).read().strip()
    return None


def write_state(mod):
    with open(STATE, "w") as f:
        f.write(mod)


def run_data_test():
    """Volledige test: nieuwste jaar ophalen, dataset-valideren zoals build_data.py."""
    # 1. beschikbare jaartallen bepalen
    per = fetch_json(f"https://opendata.cbs.nl/ODataApi/odata/{TABEL}/Perioden")["value"]
    jaren = sorted({x["Key"][:4] for x in per if x["Key"].endswith("JJ00")}, reverse=True)
    if not jaren:
        raise RuntimeError("Geen jaartallen gevonden in Perioden-codelist")
    nieuwste = jaren[0]
    # 2. nieuwste jaar volledig ophalen + valideren
    d = fetch_json(DATA_URL.format(jaar=nieuwste))["value"]
    if len(d) < 100:
        raise RuntimeError(f"verdacht weinig rijen ({len(d)}) in {nieuwste}")
    met_loon = [r for r in d if r.get("k_50ePercentielMediaan_3") is not None]
    if not met_loon:
        raise RuntimeError(f"geen enkele mediaan in {nieuwste} — publicatie nog onvolledig")
    # 3. sanity: bedragen binnen plausibel bereik
    for r in met_loon[:20]:
        v = r["k_50ePercentielMediaan_3"]
        if not (5 <= v <= 120):
            raise RuntimeError(f"onplausibel uurloon {v} in {nieuwste}")
    return {
        "jaar": nieuwste,
        "rijen": len(d),
        "met_loon": len(met_loon),
        "voorbeeld": met_loon[0],
    }


def main():
    args = sys.argv[1:]
    force = "--force" in args
    reset = "--reset" in args

    try:
        mod, titel = current_modified()
    except Exception as e:
        print(f"ALERT: CBS-TableInfos onbereikbaar: {e}")
        sys.exit(2)

    if reset:
        write_state(mod)
        print(f"baseline gezet: {mod}")
        sys.exit(0)

    prev = read_state()

    if not force and prev and mod == prev:
        # STIL: geen wijziging, geen output, exit 0
        sys.exit(0)

    # Wijziging gedetecteerd (of eerste run): draai de echte data-test
    try:
        r = run_data_test()
    except Exception as e:
        print(f"ALERT: CBS-wijziging gedetecteerd ({mod}) maar data-test FAALT: {e}")
        print(f"Handmatig nakijken: build_data.py aanpassen en deploy.sh draaien.")
        sys.exit(3)

    if force and prev and mod == prev:
        print(f"GEFORCEERDE TEST OK — tabel {TABEL} ({titel})")
    else:
        print(f"WIJZIGING GEDTECTEERD — tabel {TABEL} ({titel})")
        print(f"  Modified: {prev or '(geen baseline)'} -> {mod}")
    print(f"  Test OK: jaar {r['jaar']}, {r['rijen']} rijen, {r['met_loon']} met loon")
    print(f"  Actie: refresh-procedure uit skill 'salaris-beroepen' draaien "
          f"(build_data.py bijwerken -> deploy.sh -> Search Console-push).")
    sys.exit(0)


if __name__ == "__main__":
    main()