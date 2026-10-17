#!/usr/bin/env python3
"""
Bruto-Netto Salaris Calculator 2026 - Nederland
Gebaseerd op officiële Belastingdienst parameters (Bijlage parameterwaarden 2026)
Uitgave januari 2026

Geldig voor: Inwoner Nederland, onder AOW-leeftijd, standaardsituatie (witte tabel)
"""

# ============================================================
# OFFICIËLE PARAMETERS 2026 - Belastingdienst
# Bron: Bijlage parameterwaarden, substitutiewaarden en 
#       herleidingsfactoren 2026
# ============================================================

# Schijfgrenzen
A1 = 0         # Drempel schijf 1
A2 = 38883     # Bovengrens schijf 1 / drempel schijf 2
A3 = 78426     # Bovengrens schijf 2 / drempel schijf 3

# Gecombineerde tarieven (loonbelasting + premies volksverzekeringen)
B1 = 0.3575    # Schijf 1: 35,75%
B2 = 0.3756    # Schijf 2: 37,56%
B3 = 0.4950    # Schijf 3: 49,50%

# Cumulatieve bedragen bij schijfovergangen
C2 = 13900     # Cumulatieve belasting bij a2
C3 = 28752     # Cumulatieve belasting bij a3

# Componenten gecombineerd tarief schijf 1
IB_S1 = 0.0810     # Inkomstenbelasting schijf 1
AOWANW_S1 = 0.1800 # AOW + ANW premies schijf 1
WLZ_S1 = 0.0965    # Wlz-premie schijf 1
# Controle: 8.10 + 18.00 + 9.65 = 35.75 ✓

# Algemene Heffingskorting (AHK)
AHK_MAX = 3115     # Maximum AHK bedrag
AHK_G1 = 29736     # Fase-uit start (AHK = max hierboven)
AHK_G2 = 78426     # Fase-uit eindig (AHK = 0)
AHK_RATE = 0.06398  # Fase-uit percentage

# Arbeidskorting (ARK)
ARK_G1 = 11965     # Grens band 1→2
ARK_G2 = 25845     # Grens band 2→3
ARK_G3 = 45592     # Grens band 3→max
ARK_G4 = 132920    # Arbeidskorting volledig afgebouwd
ARK_R1 = 0.08324   # Percentage band 1
ARK_R2 = 0.31009   # Percentage band 2
ARK_R3 = 0.01950   # Percentage band 3
ARK_RATE_OUT = 0.06510  # Fase-uit percentage boven ARK_G3

# Loonbelastingdeel factoren (voor credit splitsing)
FLB = 0.22657  # Loonbelastingdeel factor
FPH = 0.77343  # Premiedeel factor


def calc_loonheffing(bruto_jaar: float) -> float:
    """
    Bereken gecombineerde loonheffing (IB + premies) op jaarinkomen.
    Standaardsituatie (witte tabel), onder AOW-leeftijd.
    """
    L = bruto_jaar
    if L <= A2:
        return B1 * L
    elif L <= A3:
        return C2 + B2 * (L - A2)
    else:
        return C3 + B3 * (L - A3)


def calc_ahk(bruto_jaar: float) -> float:
    """
    Bereken Algemene Heffingskorting.
    Onder AOW-leeftijd, standaardsituatie.
    """
    L = bruto_jaar
    if L <= AHK_G1:
        return AHK_MAX
    elif L <= AHK_G2:
        return max(0, AHK_MAX - AHK_RATE * (L - AHK_G1))
    else:
        return 0


def calc_ark(bruto_jaar: float) -> float:
    """
    Bereken Arbeidskorting.
    Onder AOW-leeftijd, standaardsituatie.
    """
    L = bruto_jaar
    if L <= 0:
        return 0
    elif L <= ARK_G1:
        # Band 1: 8,324% over het hele inkomen
        return ARK_R1 * L
    elif L <= ARK_G2:
        # Band 2: opbouw van band 1 + 31,009% over deel boven ARK_G1
        return ARK_R1 * ARK_G1 + ARK_R2 * (L - ARK_G1)
    elif L <= ARK_G3:
        # Band 3: maximale ARK opgebouwd + 1,95% over deel boven ARK_G2
        return ARK_R1 * ARK_G1 + ARK_R2 * (ARK_G2 - ARK_G1) + ARK_R3 * (L - ARK_G2)
    elif L < ARK_G4:
        # Fase-uit: 6,51% van het deel boven ARK_G3, tot nul bij ARK_G4
        max_ark = ARK_R1 * ARK_G1 + ARK_R2 * (ARK_G2 - ARK_G1) + ARK_R3 * (ARK_G3 - ARK_G2)
        return max(0, max_ark - ARK_RATE_OUT * (L - ARK_G3))
    else:
        return 0


def calc_bruto_netto(bruto_jaar: float) -> dict:
    """
    Volledige bruto-netto berekening 2026.
    Onder AOW-leeftijd, standaardsituatie (witte tabel).
    
    Retourneert dict met alle tussenresultaten.
    """
    L = bruto_jaar
    
    # 1. Gecombineerde loonheffing
    gross_tax = calc_loonheffing(L)
    
    # 2. Algemene heffingskorting
    ahk = calc_ahk(L)
    
    # 3. Arbeidskorting
    ark = calc_ark(L)
    
    # 4. Netto loonheffing (minimum 0)
    net_tax = max(0, gross_tax - ahk - ark)
    
    # 5. Netto inkomen
    netto = L - net_tax
    
    # 6. Effectief tarief
    eff_tarief = (net_tax / L * 100) if L > 0 else 0
    
    return {
        'bruto_jaar': L,
        'loonheffing_bruto_jaar': round(gross_tax, 2),
        'ahk_jaar': round(ahk, 2),
        'ark_jaar': round(ark, 2),
        'loonheffing_netto_jaar': round(net_tax, 2),
        'netto_jaar': round(netto, 2),
        'effectief_tarief': round(eff_tarief, 2),
        # Maandelijks
        'bruto_maand': round(L / 12, 2),
        'loonheffing_netto_maand': round(net_tax / 12, 2),
        'ahk_maand': round(ahk / 12, 2),
        'ark_maand': round(ark / 12, 2),
        'netto_maand': round(netto / 12, 2),
    }


def format_currency(amount: float) -> str:
    """Format bedrag als Euro met 2 decimalen."""
    return f"€{amount:,.2f}".replace(",", "_TEMP_").replace(".", ",").replace("_TEMP_", ".")


def print_berekening(bruto_maand: float):
    """Print een overzichtelijke berekening voor maandelijkse brutoloon."""
    L = bruto_maand * 12
    r = calc_bruto_netto(L)
    
    print(f"\n{'='*55}")
    print(f"  BRUTO-NETTO BEREKENING 2026")
    print(f"  (Inwoner NL, < AOW-leeftijd, standaard)")
    print(f"{'='*55}")
    print(f"  Brutoloon:        {format_currency(r['bruto_maand']):>14} per maand")
    print(f"                   {format_currency(r['bruto_jaar']):>14} per jaar")
    print(f"  ─────────────────────────────────────")
    print(f"  Loonheffing:      {format_currency(r['loonheffing_bruto_jaar']):>14} per jaar")
    print(f"  - AHK:           -{format_currency(r['ahk_jaar']):>13} per jaar")
    print(f"  - ARK:           -{format_currency(r['ark_jaar']):>13} per jaar")
    print(f"  = Netto LH:       {format_currency(r['loonheffing_netto_jaar']):>14} per jaar")
    print(f"  ─────────────────────────────────────")
    print(f"  NETTO:            {format_currency(r['netto_jaar']):>14} per jaar")
    print(f"                   {format_currency(r['netto_maand']):>14} per maand")
    print(f"  Effectief tarief: {r['effectief_tarief']:>13}%")
    print(f"{'='*55}")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        try:
            bruto = float(sys.argv[1])
            print_berekening(bruto)
        except ValueError:
            print("Gebruik: python salaris_calc.py <bruto_maand_bedrag>")
            print("Voorbeeld: python salaris_calc.py 3000")
    else:
        # Demo met standaard bedragen
        for bm in [1000, 2000, 3000, 4000, 5000, 7000]:
            print_berekening(bm)