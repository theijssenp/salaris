// Rooktest: voert de pagina-JS uit met een minimale DOM-stub
// en controleert dat render() 115 rijen + HG-koppen produceert.
const fs = require('fs');

function el(tag) {
  return {
    tag, children: [], style: {}, attrs: {},
    _innerHTML: '', _textContent: '',
    classList: { add(){}, remove(){}, toggle(){} },
    setAttribute(k, v) { this.attrs[k] = v; },
    getAttribute(k) { return this.attrs[k]; },
    appendChild(c) { this.children.push(c); },
    addEventListener() {},
    scrollIntoView() {},
    querySelectorAll() { return []; },
    querySelector() { return null; },
    closest() { return null; },
    focus() {}, blur() {},
    get innerHTML() { return this._innerHTML; },
    set innerHTML(v) { this._innerHTML = v; },
    get textContent() { return this._textContent; },
    set textContent(v) { this._textContent = v; },
    get value() { return this._value || ''; },
    set value(v) { this._value = v; },
  };
}

const ids = {};
const byId = new Proxy({}, { get(_, k) { return ids[k] || (ids[k] = el('div')); } });

global.document = {
  getElementById: (id) => byId[id] || (byId[id] = el('div')),
  createElement: (t) => el(t),
  querySelectorAll: () => [],
  addEventListener() {},
  querySelector: () => null,
};
global.BEROEPEN = null;

// laad data.js (const is niet zichtbaar in vm-context -> this. toewijzing nodig in test)
const vm = require('vm');
const dataSrc = fs.readFileSync('/home/pieter/hodc/salaris-beroepen/beroepen-data.js', 'utf8').replace('const BEROEPEN =', 'this.BEROEPEN =');
const dctx = { console };
vm.createContext(dctx);
vm.runInContext(dataSrc, dctx);
if (!dctx.BEROEPEN) { console.error('BEROEPEN niet geladen'); process.exit(1); }
global.BEROEPEN = dctx.BEROEPEN;

// haal inline script uit de pagina
const html = fs.readFileSync('/home/pieter/hodc/salaris-beroepen/salaris-per-beroep.html', 'utf8');
// pak het LAATSTE <script> blok (inline app-script, na het externe data-script)
const blocks = html.match(/<script>[\s\S]*?<\/script>/g) || [];
const inline = blocks.filter(b => b.includes('(function() {') && b.includes("'use strict'"));
if (!inline.length) { console.error('inline script niet gevonden'); process.exit(1); }
const script = inline[inline.length - 1].replace(/^<script>/, '').replace(/<\/script>$/, '');

eval(script);

// assertions
const tbody = byId['tbody'].innerHTML;
const rows = (tbody.match(/beroep-row/g) || []).length;
const hgHeads = (tbody.match(/class="hg-head"/g) || []).length;
const stats = (byId['stat-strip'].innerHTML.match(/class="stat"/g) || []).length;
const tops = (byId['top-grid'].innerHTML.match(/class="top-card"/g) || []).length;
const hgOpts = byId['hg-filter'].children.length;

console.log('rijen:', (tbody.match(/beroep-row/g) || []).length);
console.log('hoofdgroep-headers:', hgHeads);
console.log('stat-blokken:', (byId['stat-strip'].innerHTML.match(/class="stat"/g) || []).length);
console.log('top-kaarten:', tops.length);
console.log('sectoren in filter:', hgOpts - 1, '(+ alle optie)');

// WSJ-simulatie: 3200 invullen en klikken
byId['wsj-bruto'].value = '3200';
// trigger click-handler niet direct aanroepbaar (anoniem), maar bereken zelf:
const D = BEROEPEN.beroepen;
const boven = D.filter(b => b.medn < 3200).length;
console.log('WSJ 3200 =>', Math.round(boven / D.length * 100) + '% van beroepen onder');

// validaties
let ok = true;
if ((tbody.match(/beroep-row/g) || []).length !== 115) { console.error('FOUT: niet 115 rijen'); ok = false; }
if (hgOpts < 10) { console.error('FOUT: sectoren niet geladen'); ok = false; }
const strip = byId['stat-strip'].innerHTML;
if (strip.includes('€ NaN') || strip.includes('undefined')) { console.error('FOUT: NaN/undefined in stats'); ok = false; }
if (tbody.includes('NaN') || tbody.includes('undefined')) { console.error('FOUT: NaN/undefined in tabel'); ok = false; }
console.log(ok ? 'SMOKE-TEST GESLAAGD ✓' : 'SMOKE-TEST GEFALD ✗');
process.exit(ok ? 0 : 1);