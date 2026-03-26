"""
Sešívaní sobě – Data Scraper
==============================
Stahuje statistiky hráčů SK Slavia Praha z chanceliga.cz
a hodnoty z Transfermarkt, výsledek uloží do data/players.csv

Použití:
  pip install playwright pandas requests beautifulsoup4
  playwright install chromium
  python scraper.py
"""

import json
import time
import pandas as pd
from datetime import datetime
from pathlib import Path

# ── Transfermarkt hodnoty (manuální záloha) ────────────────────────────────────
# Aktualizuj jednou za měsíc – hodnoty v EUR
TM_VALUES = {
    "Tomáš Chorý":     3_000_000,
    "Ivan Schranz":    4_000_000,
    "Matěj Jurásek":   5_000_000,
    "Ondřej Lingr":    3_500_000,
    "Oscar":           6_000_000,
    "Lukáš Provod":    4_500_000,
    "David Douděra":   5_000_000,
    "Jan Bořil":       1_000_000,
    "Aiham Ousou":     3_000_000,
    "Alexej Jurčenko": 2_000_000,
    "Michal Sadílek":  4_000_000,
    "Jakub Hromada":   2_500_000,
}

SLAVIA_CLUB_ID = "6"   # ID Slavie v systému chanceliga.cz (ověř a uprav pokud třeba)
STATS_URL = (
    "https://www.chanceliga.cz/statistiky-lidri"
    f"?id_unit=1&club={SLAVIA_CLUB_ID}&parameter=1&status=0"
    f"&game_limit=0&nationality=0&age=0&position=0"
    f"&order=0&order_dir=0&list_number=0"
)

def scrape_chanceliga() -> pd.DataFrame:
    """
    Stáhne statistiky z chanceliga.cz pomocí Playwright (headless Chrome).
    Vrátí DataFrame s hráči Slavie.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("⚠️  Playwright není nainstalován. Spusť: pip install playwright && playwright install chromium")
        return pd.DataFrame()

    print(f"🔄 Stahuji data z chanceliga.cz...")
    rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Slovník parametrů → název sloupce
        params = {
            "1":  "goals",    # góly
            "2":  "assists",  # asistence
            "9":  "xG",       # expected goals
            "10": "xA",       # expected assists
            "5":  "mins",     # odehrané minuty
        }

        player_data = {}  # name → {stat: value}

        for param_id, col_name in params.items():
            url = (
                f"https://www.chanceliga.cz/statistiky-lidri"
                f"?id_unit=1&club={SLAVIA_CLUB_ID}&parameter={param_id}"
                f"&status=0&game_limit=0&nationality=0&age=0"
                f"&position=0&order=0&order_dir=0&list_number=0"
            )
            print(f"  → {col_name} ({url})")
            page.goto(url, wait_until="networkidle", timeout=30000)
            time.sleep(2)

            # Zkus najít tabulku hráčů
            try:
                rows_els = page.query_selector_all("table tbody tr")
                for row in rows_els:
                    cells = row.query_selector_all("td")
                    if len(cells) < 3:
                        continue
                    name = cells[1].inner_text().strip()
                    val_text = cells[-1].inner_text().strip().replace(",", ".")
                    try:
                        val = float(val_text)
                    except ValueError:
                        continue
                    if name not in player_data:
                        player_data[name] = {}
                    player_data[name][col_name] = val
            except Exception as e:
                print(f"    ⚠️  Chyba při parsování {col_name}: {e}")

        browser.close()

    if not player_data:
        print("❌ Nepodařilo se načíst žádná data. Zkontroluj URL nebo strukturu stránky.")
        return pd.DataFrame()

    df = pd.DataFrame.from_dict(player_data, orient="index").reset_index()
    df.rename(columns={"index": "name"}, inplace=True)
    return df


def add_positions(df: pd.DataFrame) -> pd.DataFrame:
    """Přidá pozice hráčů (manuální slovník – aktualizuj podle soupisky)."""
    positions = {
        "Tomáš Chorý":     "ÚTO",
        "Ivan Schranz":    "ÚTO",
        "Alexej Jurčenko": "ÚTO",
        "Matěj Jurásek":   "ZÁL",
        "Oscar":           "ZÁL",
        "Lukáš Provod":    "ZÁL",
        "Ondřej Lingr":    "ZÁL",
        "Michal Sadílek":  "ZÁL",
        "Jakub Hromada":   "ZÁL",
        "David Douděra":   "OBR",
        "Jan Bořil":       "OBR",
        "Aiham Ousou":     "OBR",
    }
    df["pos"] = df["name"].map(positions).fillna("ZÁL")
    return df


def add_tm_values(df: pd.DataFrame) -> pd.DataFrame:
    """Přidá hodnoty z Transfermarktu."""
    df["tmValue"] = df["name"].map(TM_VALUES).fillna(0).astype(int)
    return df


def clean_and_validate(df: pd.DataFrame) -> pd.DataFrame:
    """Vyčistí a doplní chybějící hodnoty."""
    for col in ["goals", "assists", "xG", "xA", "mins"]:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["goals"]   = df["goals"].astype(int)
    df["assists"] = df["assists"].astype(int)
    df["mins"]    = df["mins"].astype(int)
    df["xG"]      = df["xG"].round(2)
    df["xA"]      = df["xA"].round(2)

    # Filtruj hráče s alespoň 1 odehranou minutou
    df = df[df["mins"] > 0].copy()

    return df


def save_csv(df: pd.DataFrame):
    """Uloží CSV do složky data/."""
    Path("data").mkdir(exist_ok=True)
    out_path = "data/players.csv"
    # Správné pořadí sloupců pro dashboard
    cols = ["name", "pos", "goals", "xG", "assists", "xA", "mins", "tmValue"]
    df = df[[c for c in cols if c in df.columns]]
    df.to_csv(out_path, index=False, encoding="utf-8")
    print(f"✅ Uloženo {len(df)} hráčů → {out_path}")
    print(f"   Aktualizováno: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(df.to_string(index=False))


def main():
    print("=" * 50)
    print("  Sešívaní sobě – Data Scraper")
    print("=" * 50)

    df = scrape_chanceliga()

    if df.empty:
        print("\n⚠️  Scraping selhal – zkontroluj připojení nebo strukturu webu.")
        print("   Tip: Otevři ručně https://www.chanceliga.cz/statistiky-lidri a ověř URL parametry.")
        return

    df = add_positions(df)
    df = add_tm_values(df)
    df = clean_and_validate(df)
    save_csv(df)


if __name__ == "__main__":
    main()
