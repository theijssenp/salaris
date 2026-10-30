#!/bin/bash
# Live-verificatie salaris.hodc.nl na deploy (cache-buster: fin1)
echo '=== 1. Sitemap live (lastmod aanwezig?) ==='
curl -s "https://salaris.hodc.nl/sitemap.xml?v=fin1" | head -12
echo '...'
echo -n "aantal lastmod-entries: "
curl -s "https://salaris.hodc.nl/sitemap.xml?v=fin1" | grep -c lastmod

echo '=== 2. Homepage nav met badge ==='
curl -s "https://salaris.hodc.nl/?v=fin1" | grep -o 'Salaris per beroep</a><span class="badge-new">[^<]*' | head -1

echo '=== 3. Nav op 3 subpagina-samples ==='
for f in faq minimumloon-2026 belasting-schijven-2026; do
  n=$(curl -s "https://salaris.hodc.nl/$f.html?v=fin1" | grep -c 'salaris-per-beroep')
  echo "$f: link-aantal=$n"
done

echo '=== 4. Beroepen-pagina zelf ==='
curl -s -o /dev/null -w "pagina: %{http_code} (%{size_download}B)\n" "https://salaris.hodc.nl/salaris-per-beroep.html?v=fin1"
curl -s -o /dev/null -w "data.js: %{http_code} (%{size_download}B)\n" "https://salaris.hodc.nl/beroepen-data.js?v=fin1"