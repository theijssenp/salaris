/*
 * Loonbelasting/premie volksverzekeringen per loontijdvak, 2026.
 * Volgens 'Rekenvoorschriften voor de geautomatiseerde loonadministratie 2026'
 * (Belastingdienst, uitgave januari 2026, versie 2): witte tabel, standaardsituatie,
 * werknemer woont in Nederland.
 *
 * Bedragen worden intern als gehele getallen gerekend (euro's, centen of 1e-5 euro)
 * zodat de afrondingsregels exact gelden en de uitkomst gelijk is aan de tijdvaktabellen.
 */
(function (root) {
    'use strict';

    var LV = 54;          // stapgrootte jaarloon in de brontabel
    var LMAX = 133110;    // hoogste tabelloon (jaar)

    // Percentages en factoren als gehele getallen: b in 1e-4, overige factoren in 1e-5
    var GROEPEN = {
        // jonger dan de AOW-leeftijd
        jong: {
            a2: 38883, a3: 78426, b: [3575, 3756, 4950], c2: 13900, c3: 28752,
            ahkm: 3115, ahkg1: 29736, ahka: 6398,
            arko1: 8324, arko2: 31009, arko3: 1950, arka: 6510,
            arkg1: 11965, arkg2: 25845, arkg3: 45592, arkg4: 132920,
            arkm1: 996, arkm2: 5300, arkm3: 5685,
            oukm: 0, oukg1: 0, oukg2: 0, ouka: 0
        },
        // AOW-leeftijd en ouder, geboren in 1945 of eerder
        aow1945: {
            a2: 41123, a3: 78426, b: [1785, 3756, 4950], c2: 7340, c3: 21351,
            ahkm: 1556, ahkg1: 29736, ahka: 3195,
            arko1: 4156, arko2: 15483, arko3: 974, arka: 3250,
            arkg1: 11965, arkg2: 25845, arkg3: 45592, arkg4: 132920,
            arkm1: 498, arkm2: 2647, arkm3: 2840,
            oukm: 2067, oukg1: 46002, oukg2: 59782, ouka: 15000
        },
        // AOW-leeftijd en ouder, geboren in 1946 of later
        aow1946: {
            a2: 38883, a3: 78426, b: [1785, 3756, 4950], c2: 6940, c3: 21792,
            ahkm: 1556, ahkg1: 29736, ahka: 3195,
            arko1: 4156, arko2: 15483, arko3: 974, arka: 3250,
            arkg1: 11965, arkg2: 25845, arkg3: 45592, arkg4: 132920,
            arkm1: 498, arkm2: 2647, arkm3: 2840,
            oukm: 2067, oukg1: 46002, oukg2: 59782, ouka: 15000
        }
    };

    // Tijdvakfactor F (tabel 1b)
    var FACTOR = { kwartaal: 4, maand: 12, vierweken: 13, week: 52, dag: 260 };

    function floorDiv(a, b) { return Math.floor(a / b); }
    function ceilDiv(a, b) { return Math.ceil(a / b); }
    // rekenkundig afronden van a/b (a, b > 0)
    function roundDiv(a, b) { return Math.floor((2 * a + b) / (2 * b)); }

    // X1: schijventarief over jaarloon L (hele euro's, naar beneden)
    function x1(L, p) {
        if (L <= 0) return 0;
        if (L <= p.a2) return floorDiv(L * p.b[0], 10000);
        if (L <= p.a3) return floorDiv((L - p.a2) * p.b[1], 10000) + p.c2;
        return floorDiv((L - p.a3) * p.b[2], 10000) + p.c3;
    }

    // Algemene heffingskorting (jaarbedrag, naar boven op hele euro's)
    function ahk(L, p) {
        if (L <= p.ahkg1) return p.ahkm;
        if (L <= p.a3) return Math.max(0, ceilDiv(p.ahkm * 100000 - (L - p.ahkg1) * p.ahka, 100000));
        return 0;
    }

    // Ouderenkorting (jaarbedrag, naar boven op hele euro's)
    function ouk(L, p) {
        if (!p.oukm) return 0;
        if (L <= p.oukg1) return p.oukm;
        if (L <= p.oukg2) return Math.max(0, ceilDiv(p.oukm * 100000 - (L - p.oukg1) * p.ouka, 100000));
        return 0;
    }

    // Arbeidskorting (jaarbedrag, naar boven op hele euro's); intern in 1e-5 euro
    function ark(L, p) {
        if (L <= 0 || L > p.arkg4) return 0;
        var s1 = Math.min(p.arko1 * L, p.arkm1 * 100000);
        var s2 = Math.min(s1 + p.arko2 * Math.max(0, L - p.arkg1), p.arkm2 * 100000);
        var s3 = Math.min(s2 + p.arko3 * Math.max(0, L - p.arkg2), p.arkm3 * 100000);
        var tot = s3 - p.arka * Math.max(0, L - p.arkg3);
        return Math.max(0, ceilDiv(tot, 100000));
    }

    /*
     * Bereken de inhouding over een tijdvakloon.
     *   tvl         loon voor de loonbelasting/volksverzekeringen in het tijdvak (euro, 2 decimalen)
     *   tijdvak     'maand' | 'vierweken' | 'kwartaal' | 'week' | 'dag'
     *   groep       'jong' | 'aow1945' | 'aow1946'
     *   lhk         loonheffingskorting toepassen (true/false)
     * Resultaat in euro's: lbph (in te houden LB/PH), ark (verrekende arbeidskorting),
     * plus jaarloon L en de jaarbedragen voor de toelichting.
     */
    function bereken(tvl, tijdvak, groep, lhk) {
        var p = GROEPEN[groep];
        var F = FACTOR[tijdvak];
        if (!p || !F) throw new Error('Onbekende groep of tijdvak');
        var tvlCent = Math.round(tvl * 100);
        var res = { tvl: tvlCent / 100, F: F, L: 0, X1: 0, AHK: 0, OUK: 0, ARK: 0, X: 0, lbph: 0, ark: 0, boven: false };
        if (tvlCent <= 0) return res;

        // Het hoogste tabelloon per tijdvak is Lmax/F, naar boven afgerond op centen
        var maxTabelCent = ceilDiv(LMAX * 100, F);
        if (tvlCent <= maxTabelCent) {
            var L = Math.min(floorDiv(tvlCent * F, LV * 100) * LV, LMAX);
            var X1 = x1(L, p);
            var A = 0, O = 0, R = 0;
            if (lhk) {
                A = ahk(L, p); O = ouk(L, p); R = ark(L, p);
                // Kortingen hoger dan X1: aftoppen in volgorde ARK, OUK, AHK
                var over = A + O + R - X1;
                if (over > 0) { var d = Math.min(R, over); R -= d; over -= d; }
                if (over > 0) { d = Math.min(O, over); O -= d; over -= d; }
                if (over > 0) { d = Math.min(A, over); A -= d; over -= d; }
            }
            var X = X1 - A - O - R;
            res.L = L; res.X1 = X1; res.AHK = A; res.OUK = O; res.ARK = R; res.X = X;
            res.lbph = roundDiv(X * 100, F) / 100;
            res.ark = roundDiv(R * 100, F) / 100;
            return res;
        }

        // Boven het maximale tabelloon (systematiek 1): inhouding bij Lmax plus toptarief over het meerdere
        var Xmax = x1(LMAX, p);   // alle kortingen zijn bij Lmax afgebouwd
        var yCent = roundDiv(Xmax * 100, F);
        var bovenCent = floorDiv((tvlCent * F - LMAX * 100) * p.b[2], F * 10000);
        res.boven = true;
        res.L = tvlCent * F / 100;
        res.X1 = res.X = (yCent + bovenCent) * F / 100;
        res.lbph = (yCent + bovenCent) / 100;
        return res;
    }

    var api = { bereken: bereken, GROEPEN: GROEPEN, FACTOR: FACTOR, LMAX: LMAX, LV: LV };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    else root.Loonheffing2026 = api;
})(this);
