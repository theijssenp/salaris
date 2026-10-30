#!/bin/bash
# Verificatie van nav-patches in ~/hodc/salaris-beroepen
cd /home/pieter/hodc/salaris-beroepen
echo '=== index.html nav ==='
grep -A7 '<nav' index.html | head -9
echo
echo '=== salaris-per-beroep link aanwezig in: ==='
for f in index belasting-schijven-2026 hoe-bereken-je-netto-salaris faq minimumloon-2026 over-ons netto-salaris-met-vakantiegeld bruto-netto-verschil; do
  n=$(grep -c 'salaris-per-beroep.html' $f.html)
  b=$(grep -c 'badge-new' $f.html)
  echo "$f: link=$n badge-css=$b"
done