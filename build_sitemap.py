#!/usr/bin/env python3
"""
Genereert sitemap.xml voor salaris.hodc.nl.

Beleid: lastmod = file-mtime van de bronpagina in deze workspace.
Alleen pagina's die ook echt in de vhost staan komen in de sitemap.
Google gebruikt alleen lastmod (priority/changefreq worden genegeerd).
"""
import os
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "https://salaris.hodc.nl"

# (bestandsnaam, prioriteit, changefreq)
PAGES = [
    ("index.html", "1.0", "monthly"),
    ("salaris-per-beroep.html", "0.9", "weekly"),
    ("dga-salaris.html", "0.9", "weekly"),
    ("dga-loonaangifte.html", "0.8", "yearly"),
    ("cao-salarisschalen-2026.html", "0.8", "yearly"),
    ("belasting-schijven-2026.html", "0.8", "yearly"),
    ("hoe-bereken-je-netto-salaris.html", "0.8", "yearly"),
    ("bruto-netto-verschil.html", "0.8", "yearly"),
    ("netto-salaris-met-vakantiegeld.html", "0.7", "yearly"),
    ("minimumloon-2026.html", "0.7", "monthly"),
    ("faq.html", "0.7", "yearly"),
    ("over-ons.html", "0.5", "yearly"),
    ("privacy-policy.html", "0.3", "yearly"),
]


def lastmod(fname):
    p = os.path.join(HERE, fname)
    if not os.path.exists(p):
        return None
    return datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d")


def main():
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    skipped = []
    for fname, prio, freq in PAGES:
        lm = lastmod(fname)
        if lm is None:
            skipped.append(fname)
            continue
        loc = BASE + "/" if fname == "index.html" else f"{BASE}/{fname}"
        out.append("  <url>")
        out.append(f"    <loc>{loc}</loc>")
        out.append(f"    <lastmod>{lm}</lastmod>")
        out.append(f"    <changefreq>{freq}</changefreq>")
        out.append(f"    <priority>{prio}</priority>")
        out.append("  </url>")
    out.append("</urlset>")
    path = os.path.join(HERE, "sitemap.xml")
    with open(path, "w") as f:
        f.write("\n".join(out) + "\n")
    print(f"OK: {len(PAGES) - len(skipped)} urls -> {path}")
    if skipped:
        print("  OVERGESLAAN (bestand ontbreekt):", ", ".join(skipped))


if __name__ == "__main__":
    main()
