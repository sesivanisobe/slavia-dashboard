"""
Sešívaní sobě – SKS Tipovačka
Logika bodování. Držet odděleně od UI, ať se dá snadno testovat a upravovat.

Pravidla (sezóna 2026/27):
- Přesný výsledek (skóre domácí:hosté) = 100 bodů, jinak 0 bodů
- xG Slavie: 100 - (odchylka * 100), minimálně 0 bodů (floor)
- Maximum za zápas: 200 bodů
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Tip:
    skore_domaci: int
    skore_hoste: int
    xg: float


@dataclass
class Vysledek:
    skore_domaci: int
    skore_hoste: int
    xg: float


@dataclass
class Body:
    za_vysledek: int
    za_xg: int
    celkem: int
    odchylka_xg: float


def body_za_vysledek(tip: Tip, vysledek: Vysledek) -> int:
    """100 bodů za přesně trefené skóre, jinak 0."""
    if tip.skore_domaci == vysledek.skore_domaci and tip.skore_hoste == vysledek.skore_hoste:
        return 100
    return 0


def body_za_xg(tip_xg: float, realne_xg: float) -> tuple[int, float]:
    """
    100 - (odchylka * 100), floor na 0.
    Vrací (body, odchylka) - odchylku vracíme i pro zobrazení ve výpisu.
    """
    odchylka = abs(round(tip_xg - realne_xg, 2))
    body = round(100 - odchylka * 100)
    body = max(0, body)
    return body, odchylka


def spocitej_body(tip: Tip, vysledek: Vysledek) -> Body:
    v_body = body_za_vysledek(tip, vysledek)
    xg_body, odchylka = body_za_xg(tip.xg, vysledek.xg)
    return Body(
        za_vysledek=v_body,
        za_xg=xg_body,
        celkem=v_body + xg_body,
        odchylka_xg=odchylka,
    )


def over_pred_deadline(cas_odeslani, deadline) -> bool:
    """Ochrana proti tipování po výkopu - použito při ukládání i validaci."""
    return cas_odeslani <= deadline


# ── Rychlý sebe-test (spustit: python scoring.py) ──────────────────────────
if __name__ == "__main__":
    # Příklady přímo z konzultace s VM - zápas skončil 3:0, skutečné xG 3,5
    priklady = [
        (Tip(3, 0, 3.5), 200),
        (Tip(3, 0, 3.8), 170),
        (Tip(3, 0, 3.2), 170),
        (Tip(3, 0, 5.0), 100),
        (Tip(1, 0, 1.0), 0),
    ]
    vysledek = Vysledek(3, 0, 3.5)
    for tip, ocekavano in priklady:
        vysledne_body = spocitej_body(tip, vysledek)
        stav = "OK" if vysledne_body.celkem == ocekavano else "CHYBA"
        print(f"{stav}: tip {tip.skore_domaci}:{tip.skore_hoste} xG={tip.xg} "
              f"-> {vysledne_body.celkem} b (očekáváno {ocekavano})")
