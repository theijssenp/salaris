#!/bin/bash
# Deploy salaris.hodc.nl naar /var/www/salaris.hodc.nl
# Runnen door Pieter:  sudo bash ~/hodc/salaris-beroepen/deploy.sh
set -e
BASE=/var/www/salaris.hodc.nl
SRC=/home/pieter/hodc/salaris-beroepen

# backups (indien nog niet aanwezig)
[ -f $BASE/index.html.bak.20260921 ] || cp $BASE/index.html $BASE/index.html.bak.20260921
[ -f $BASE/sitemap.xml.bak.20260921 ] || cp $BASE/sitemap.xml $BASE/sitemap.xml.bak.20260921

# sitemap altijd opnieuw genereren (lastmod = file-mtime)
python3 $SRC/build_sitemap.py

# alle HTML-pagina's (incl. DGA/CAO die alleen in de vhost bestonden)
for f in index salaris-per-beroep dga-salaris dga-loonaangifte cao-salarisschalen-2026 \
         belasting-schijven-2026 hoe-bereken-je-netto-salaris faq minimumloon-2026 \
         over-ons netto-salaris-met-vakantiegeld bruto-netto-verschil privacy-policy; do
    install -o www-data -g www-data -m 644 $SRC/$f.html $BASE/$f.html
done

# JS-assets
install -o www-data -g www-data -m 644 $SRC/beroepen-data.js        $BASE/beroepen-data.js
install -o www-data -g www-data -m 644 $SRC/cao-data-2026.js         $BASE/cao-data-2026.js
install -o www-data -g www-data -m 644 $SRC/loonheffing-2026.js      $BASE/loonheffing-2026.js
install -o www-data -g www-data -m 644 $SRC/salaris_calc.py          $BASE/salaris_calc.py
install -o www-data -g www-data -m 644 $SRC/sitemap.xml             $BASE/sitemap.xml

echo "Gedeployd:"
ls -la $BASE/index.html $BASE/salaris-per-beroep.html $BASE/dga-salaris.html $BASE/beroepen-data.js
echo
echo "Nav-check (salaris-per-beroep in elke pagina?):"
for f in index belasting-schijven-2026 hoe-bereken-je-netto-salaris faq minimumloon-2026 \
         over-ons netto-salaris-met-vakantiegeld bruto-netto-verschil salaris-per-beroep \
         dga-salaris dga-loonaangifte cao-salarisschalen-2026; do
    n=$(grep -c 'salaris-per-beroep.html' $BASE/$f.html)
    echo "  $f.html: $n"
done
echo
echo "DGA-link-check (moet >=1 zijn in elke pagina):"
for f in index belasting-schijven-2026 hoe-bereken-je-netto-salaris faq minimumloon-2026 \
         over-ons netto-salaris-met-vakantiegeld bruto-netto-verschil salaris-per-beroep; do
    n=$(grep -c 'dga-salaris.html' $BASE/$f.html)
    echo "  $f.html: $n"
done
echo
echo "Sitemap-URLs:"
grep -c '<loc>' $BASE/sitemap.xml
