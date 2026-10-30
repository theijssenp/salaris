#!/bin/bash
# Deploy salaris.hodc.nl naar /var/www/salaris.hodc.nl
#
# Runnen door Pieter:  sudo bash ~/hodc/salaris-beroepen/deploy.sh
#
# Bron van waarheid: de git-repo. De workspace ~/hodc/salaris-beroepen/
# is een checkout van github.com/theijssenp/salaris (branch main).
# NIET rechtstreeks in de vhost werken - zie README.md.
set -e
BASE=/var/www/salaris.hodc.nl
SRC=/home/pieter/hodc/salaris-beroepen

# --- 0. werkboom moet schoon zijn, anders deployen we half werk ---
if [ -d "$SRC/.git" ]; then
  dirty=$(cd "$SRC" && git status --porcelain)
  if [ -n "$dirty" ]; then
    echo "ABORT: ongecommitte wijzigingen in de workspace:"
    echo "$dirty"
    echo "Commit of stash eerst."
    exit 1
  fi
fi

# --- 1. backups (eenmalig; bestaande backups blijven staan) ---
stamp=$(date +%Y%m%d-%H%M%S)
[ -f $BASE/index.html.bak.20260921 ] || cp $BASE/index.html $BASE/index.html.bak.20260921
[ -f $BASE/sitemap.xml.bak.20260921 ] || cp $BASE/sitemap.xml $BASE/sitemap.xml.bak.20260921

# --- 2. sitemap altijd opnieuw genereren (lastmod = file-mtime) ---
python3 $SRC/build_sitemap.py

# --- 3. alle pagina's (uit de repo; DGA/CAO zitten in de git-tree) ---
PAGES="index salaris-per-beroep dga-salaris dga-loonaangifte cao-salarisschalen-2026
       belasting-schijven-2026 hoe-bereken-je-netto-salaris faq minimumloon-2026
       over-ons netto-salaris-met-vakantiegeld bruto-netto-verschil privacy-policy"

for f in $PAGES; do
    [ -f "$SRC/$f.html" ] || { echo "ABORT: ontbreekt $SRC/$f.html"; exit 1; }
    install -o www-data -g www-data -m 644 "$SRC/$f.html" "$BASE/$f.html"
done

# --- 4. JS-assets en overige statische bestanden ---
for f in beroepen-data.js cao-data-2026.js loonheffing-2026.js salaris_calc.py \
         sitemap.xml ads.txt robots.txt og-image.png google2ed2522d3aa700b3.html; do
    [ -f "$SRC/$f" ] && install -o www-data -g www-data -m 644 "$SRC/$f" "$BASE/$f"
done

# --- 5. opruimen: bestanden die niet meer in de repo zitten ---
for f in "$BASE"/* "$BASE"/._*; do
    b=$(basename "$f")
    [ -f "$f" ] || continue
    case "$b" in
        *.bak*) continue;;          # oude backups bewaren
    esac
    # AppleDouble-junk (._*) van macOS: altijd opruimen
    case "$b" in
        ._*) rm -f "$f"; echo "  VERWIJDER macOS-junk: $b"; continue;;
    esac
    if [ ! -f "$SRC/$b" ]; then
        echo "  VERWIJDER uit vhost (niet in repo): $b"
        rm -f "$f"
    fi
done

echo
echo "Gedeployd. Bestanden:"
ls -la $BASE/*.html $BASE/*.js $BASE/sitemap.xml | awk '{print $1, $3, $5, $9}'

echo
echo "=== CONTROLES ==="
echo "-- DGA-link per pagina (moet >=1) --"
for f in $PAGES; do
    n=$(grep -c 'dga-salaris.html' "$BASE/$f.html" || true)
    printf "  %-40s %s\n" "$f.html" "$n"
done
echo "-- salaris-per-beroep-link per pagina (moet >=1) --"
for f in $PAGES; do
    n=$(grep -c 'salaris-per-beroep.html' "$BASE/$f.html" || true)
    printf "  %-40s %s\n" "$f.html" "$n"
done
echo "-- AdSense-script (moet >=1 op index) --"
printf "  index.html adsbygoogle: %s\n" "$(grep -c 'adsbygoogle' "$BASE/index.html" || true)"
echo "-- Sitemap-URLs --"
grep -c '<loc>' "$BASE/sitemap.xml"

echo
echo "Live-verificatie:"
bash $SRC/verify_live.sh
