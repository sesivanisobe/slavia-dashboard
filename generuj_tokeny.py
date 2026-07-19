"""
Sešívaní sobě – generátor tokenů pro SKS Tipovačku

Spustit JEDNOU na začátku sezony (a pak kdykoliv přibude nový účastník).
Vygeneruje:
  1) tabulku (CSV), kterou vložíš do listu "uzivatele" v Google Sheets
  2) hotové texty zpráv k rozeslání do WhatsApp skupiny

Použití:
  python generuj_tokeny.py "Filip Šimoník" "Roman Liebich" "Jakub Heller"
"""

import secrets
import sys
import csv
from urllib.parse import quote

STREAMLIT_URL = "https://sesivanisobe.streamlit.app/Tipovacka"  # uprav podle skutečné URL stránky


def vygeneruj_token() -> str:
    return secrets.token_hex(3)  # 6 znaků, např. "a8f3k2"


def main(jmena: list[str]):
    if not jmena:
        print("Zadej alespoň jedno jméno jako argument, např.:")
        print('  python generuj_tokeny.py "Filip Šimoník" "Roman Liebich"')
        return

    radky = []
    zpravy = []
    for jmeno in jmena:
        token = vygeneruj_token()
        radky.append({"jmeno": jmeno, "token": token})
        # POZOR: v odkazu musí být PŘESNĚ stejné jméno jako v tabulce "uzivatele" (jinak přihlášení selže)
        odkaz = f"{STREAMLIT_URL}?u={quote(jmeno)}&t={token}"
        zpravy.append(
            f"Ahoj {jmeno.split()[0]}! Tady je tvůj osobní odkaz na SKS Tipovačku pro celou sezónu "
            f"2026/27 - stačí kliknout a uložit si ho jako záložku, budeš ho používat každé kolo:\n{odkaz}"
        )

    # 1) CSV pro Google Sheets
    with open("uzivatele_novy.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["jmeno", "token"])
        writer.writeheader()
        writer.writerows(radky)
    print("Hotovo -> uzivatele_novy.csv")
    print("Otevři ho a řádky zkopíruj do listu 'uzivatele' v Google Sheets (bez přepisování hlavičky).\n")

    # 2) Texty pro WhatsApp
    with open("whatsapp_zpravy.txt", "w", encoding="utf-8") as f:
        for zprava in zpravy:
            f.write(zprava + "\n\n---\n\n")
    print("Hotovo -> whatsapp_zpravy.txt")
    print("Otevři soubor a každou zprávu pošli danému člověku (nejlépe do soukromé zprávy, ne do skupiny,")
    print("protože token je unikátní pro dané jméno).")


if __name__ == "__main__":
    main(sys.argv[1:])
