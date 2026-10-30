# salaris.hodc.nl

Bruto-netto salariscalculator en salarisinformatie voor Nederland.
Live op https://salaris.hodc.nl

Statische site, geserveerd door Apache op herm uit `/var/www/salaris.hodc.nl`.

## Werkwijze

De **git-repo is de enige bron van waarheid**. De vhost is alleen het
deploy-doel; daar wordt nooit rechtstreeks in gewerkt.

- Repo: `github.com/theijssenp/salaris` (branch `main`)
- Workspace/checkout: `~/hodc/salaris-beroepen/`
- Deploy: `sudo bash ~/hodc/salaris-beroepen/deploy.sh` (alleen Pieter)

Het deploy-script controleert vóór deploy of de werkboom schoon is en
verwijdert daarna uit de vhost wat niet meer in de repo staat.

## Data-pipeline

De salariscijfers komen uit CBS StatLine tabel **86355NED**
("Werknemers; uurloon en beroep").

1. `cbs_watchdog.py` — detecteert wijzigingen in de CBS-tabel
   (cronjob `b6bbdf11a02f`) en ververst `cbs_2025.json`
2. `build_data.py` — bouwt `beroepen-data.js` uit de CBS-bronbestanden
   en `salaris_calc.py` (Belastingdienst-parameters 2026, witte tabel)
3. `build_sitemap.py` — genereert `sitemap.xml`; `lastmod` = file-mtime
4. `deploy.sh` — zet alles live en doet nav-/sitemap-/adscontrole
5. `smoke_test.js` / `verify_live.sh` — functionele en live-controles

**Belangrijk:** `beroepen-data.js` moet altijd uit dezelfde
`salaris_calc.py` komen als de calculator in `index.html`. De JS- en
Python-implementatie delen dezelfde parameters; bij een wijziging in
één van beide moet de andere mee.

CBS-fallbackketen per beroep: 2025 detail → 2025 groep (3-cijferig) →
2024 detail → 2024 hoofdgroep. CBS meet bruto uurloon; omrekening gaat
uit van 144 uur/maand (36 uur/week gemiddeld voltijd).

## SSH-sleutel voor GitHub

De repo `salaris` is alleen pushbaar met `id_ed25519_github`
(`id_ed25519` is een deploy key voor `bussie`):

```
git config core.sshCommand "ssh -i /home/pieter/.ssh/id_ed25519_github -o IdentitiesOnly=yes"
```
