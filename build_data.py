#!/usr/bin/env python3
"""
Genereert beroepen-data.js voor salaris.hodc.nl/salaris-per-beroep.html

Bron: CBS StatLine tabel 86355NED "Werknemers; uurloon en beroep" (BRC 2014, ed. 2025)
- 2025 cijfers (voorlopig), aangevuld met 2024 (definitief) waar 2025 onderdrukt is
- Fallback-keten per beroep: 2025 detail → 2025 groep (3-cijfer) → 2024 detail → 2024 hoofdgroep
- Netto: berekend met salaris_calc.py (Belastingdienst 2026 parameters, witte tabel, <AOW)

Omrekening: CBS meet bruto UURLOON. We gaan uit van een gemiddelde
parttimefactor. NL-voltijd = 36 uur/week (144 uur/maand, gemiddeld voltijdcontract).
"""
import json
import re
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from salaris_calc import calc_bruto_netto

UUR_PER_MAAND = 144  # 36 uur/week voltijd-gemiddelde

codelist = json.load(open(os.path.join(HERE, "cbs_beroepen_codelist.json")))["value"]
d25 = {r["Beroep"]: r for r in json.load(open(os.path.join(HERE, "cbs_2025.json")))["value"]}
d24 = {r["Beroep"]: r for r in json.load(open(os.path.join(HERE, "cbs_2024.json")))["value"]}

# naam-reparatie: Description bevat volledige naam vóór de dubbele punt
def full_name(item):
    t = item["Title"]
    if "..." not in t:
        return t
    m = re.match(r"^(\d+) ", t)
    prefix = m.group(1) + " " if m else ""
    desc = item.get("Description") or ""
    head = desc.split(":")[0].strip()
    if head:
        return prefix + head
    return t.rstrip(". ")

# codelist indexeren
by_key = {x["Key"]: x for x in codelist}
midden_by_code, hoofd_by_code = {}, {}
for x in codelist:
    t = x["Title"]
    m3 = re.match(r"^(\d{3}) ", t)
    m2 = re.match(r"^(\d{2}) ", t)
    if m3: midden_by_code[m3.group(1)] = x["Key"]
    if m2: hoofd_by_code[m2.group(1)] = x["Key"]

HG_NAAM = {
    "01": "Pedagogisch & onderwijs", "02": "Creatief & taal", "03": "Commercieel & verkoop",
    "04": "Economisch & administratief", "05": "Management", "06": "Bestuur, veiligheid & justitie",
    "07": "Techniek & bouw", "08": "ICT", "09": "Landbouw & natuur",
    "10": "Zorg & welzijn", "11": "Dienstverlening & horeca", "12": "Transport & logistiek",
    "13": "Overig",
}

def val(r):
    if not r: return None
    p25, med, p75 = r.get("k_25ePercentiel_2"), r.get("k_50ePercentielMediaan_3"), r.get("k_75ePercentiel_4")
    if med is None: return None
    return p25, med, p75

def netto(bruto_uur):
    """Bruto uurloon → netto per maand, via calc 2026 op bruto jaar."""
    r = calc_bruto_netto(round(bruto_uur * UUR_PER_MAAND * 12, 2))
    return round(r["netto_maand"])

def netto_all(bruto_uur):
    """Netto voor p25, mediaan en p75."""
    p25, med, p75 = bruto_uur
    return netto(p25), netto(med), netto(p75)

rows = []
for x in codelist:
    t = x["Title"]
    m4 = re.match(r"^(\d{4}) ", t)
    if not m4:
        continue  # alleen detailberoepen (4-cijferig) als tabelrijen
    code4 = m4.group(1)
    key = x["Key"]
    k3, k2 = code4[:3], code4[:2]

    r25 = d25.get(key)
    if val(r25):
        p25, med, p75 = val(r25); jaar, niveau = 2025, "beroep"
    else:
        pr = d25.get(midden_by_code.get(k3, ""))
        if val(pr):
            p25, med, p75 = val(pr); jaar, niveau = 2025, "beroepsgroep"
        else:
            r24 = d24.get(key)
            if val(r24):
                p25, med, p75 = val(r24); jaar, niveau = 2024, "beroep"
            else:
                h = d24.get(hoofd_by_code.get(k2, ""))
                if val(h):
                    p25, med, p75 = val(h); jaar, niveau = 2024, "hoofdgroep"
                else:
                    continue

    n25 = d25.get(key) or d24.get(key) or {}
    werknemers = n25.get("Werknemer_1") or 0
    nm = netto_all((p25, med, p75))
    hg_code = k2
    rows.append({
        "naam": full_name(x),
        "code": code4,
        "hg": HG_NAAM.get(k2, "Overig"),
        "p25": p25, "med": med, "p75": p75,
        "p25n": nm[0], "medn": nm[1], "p75n": nm[2],
        "werknemers": werknemers,
        "jaar": jaar, "niveau": niveau,
    })

def hg_code2naam(c):
    return HG_NAAM.get(c, "Overig")

# sorteren op mediaan netto, aflopend
rows.sort(key=lambda r: -r["medn"])

out = {"updated": "2025 (voorlopig; aangevuld met definitieve 2024-cijfers)",
       "uur_per_maand": UUR_PER_MAAND, "beroepen": rows}
path = os.path.join(HERE, "beroepen-data.js")
with open(path, "w") as f:
    f.write("// Gegenereerd door build_data.py — bron: CBS StatLine 86355NED (BRC 2014)\n")
    f.write("// Omrekening: %d uur/maand; netto via Belastingdienst-parameters 2026 (witte tabel)\n" % UUR_PER_MAAND)
    f.write("const BEROEPEN = ")
    json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    f.write(";\n")
print(f"OK: {len(rows)} beroepen -> {path}")
# top/laagste voor controle
print("\nTop 5 (netto mediaan/maand):")
for r in rows[:5]:
    print(f"  {r['naam'][:52]:54s} bruto med {r['med']:5.1f}/u -> netto {r['medn']}/m")
print("\nLaagste 5:")
for r in rows[-5:]:
    print(f"  {r['naam'][:52]:54s} bruto med {r['med']:5.1f}/u -> netto {r['medn']}/m")
print("\nNiveaus:", {n: sum(1 for r in rows if r['niveau']==n) for n in ('beroep','beroepsgroep','hoofdgroep')},
      "| jaren:", {j: sum(1 for r in rows if r['jaar']==j) for j in (2025,2024)})