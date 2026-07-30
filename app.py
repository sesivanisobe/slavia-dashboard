#!/usr/bin/env python3
"""
update_players.py — aktualizace statistik hráčů + sběr historie po kolech.

Co dělá:
  1. Načte přes Playwright kumulativní hráčskou statistiku Slavie z chanceliga.cz.
  2. Zapíše data/players_2026_27.csv — AKTUÁLNÍ stav (pro stávající dashboard).
  3. Přidá snapshot do data/history_2026_27.csv — jeden řádek na hráče a KOLO
     (kumulativní hodnoty). Z historie se pak dá vykreslit:
       - náběhová křivka  = kumulativní hodnota vs. kolo (přímo, bez odečítání)
       - příspěvek za kolo = hodnota[kolo] - hodnota[kolo-1]
     Ukládáme kumulativně schválně: když zdroj zpětně opraví číslo (Provod!),
     rozdíly se dopočítají čistě a nic se nerozbije.

Spuštění:
  pip install playwright && playwright install chromium
  python3 update_players.py                 # kolo se odhadne z počtu odehraných zápasů
  python3 update_players.py --round 3       # kolo zadáš ručně (spolehlivější)

Idempotentní: opětovné spuštění pro stejné kolo řádky přepíše, nezduplikuje.
"""

import argparse, csv, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

CLUB_ID = 5
CSV_PATH = Path("data/players_2026_27.csv")
HIST_PATH = Path("data/history_2026_27.csv")

POS_MAP = {
    "B": None, "brankar": None, "GK": None,
    "O": "OBR", "obrance": "OBR",
    "Z": "ZAL", "zaloznik": "ZAL",
    "U": "UTO", "utocnik": "UTO",
}
# pozn.: hodnoty se nastaví na skutečné diakritické varianty níže
POS_MAP = {
    "B": None, "brankář": None, "brankar": None, "GK": None,
    "O": "OBR", "obránce": "OBR", "obrance": "OBR",
    "Z": "ZÁL", "záložník": "ZÁL", "zaloznik": "ZÁL",
    "U": "ÚTO", "útočník": "ÚTO", "utocnik": "ÚTO",
}
STAT_COLS = ["mins", "goals", "xG", "assists", "xA", "body"]


def num(s):
    s = (s or "").strip().replace("\xa0", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def scrape(season):
    url = (f"https://www.chanceliga.cz/statistiky?unit=1&status=0&parameter=1"
           f"&season={season}&club={CLUB_ID}&game_limit=0&nationality=&age=0"
           f"&order=5&order_dir=2&list_number=0&position=0#stats")
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page()
        pg.goto(url, wait_until="networkidle", timeout=60000)
        pg.wait_for_function(
            "() => [...document.querySelectorAll('table th')]"
            ".some(th => th.innerText.trim().toUpperCase() === 'XG')", timeout=60000)
        data = pg.evaluate("""() => {
            const t = [...document.querySelectorAll('table')].find(t =>
                [...t.querySelectorAll('th')].some(th =>
                    th.innerText.trim().toUpperCase() === 'XG'));
            if (!t) return null;
            return {
              heads: [...t.querySelectorAll('th')].map(th => th.innerText.trim().toUpperCase()),
              rows: [...t.querySelectorAll('tbody tr')].map(tr =>
                    [...tr.querySelectorAll('td')].map(td => td.innerText.trim()))
            };
        }""")
        b.close()
    if not data:
        sys.exit("CHYBA: tabulku se statistikou se nepodarilo najit.")
    return data["heads"], data["rows"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, default=2027)
    ap.add_argument("--round", type=int, default=0,
                    help="cislo kola; 0 = odhadnout z max. poctu odehranych zapasu")
    args = ap.parse_args()

    heads, rows = scrape(args.season)
    idx = {h: i for i, h in enumerate(heads)}
    need = ["HRÁČ", "PO", "Z", "MIN", "G", "XG", "A", "XA", "B"]
    miss = [h for h in need if h not in idx]
    if miss:
        sys.exit(f"CHYBA: chybi sloupce {miss}. Hlavicka: {heads}")

    scraped = {}
    for r in rows:
        name = r[idx["HRÁČ"]].strip()
        if not name:
            continue
        scraped[name] = {
            "po": r[idx["PO"]].strip(),
            "games": int(num(r[idx["Z"]])),
            "mins": int(num(r[idx["MIN"]])),
            "goals": int(num(r[idx["G"]])),
            "xG": round(num(r[idx["XG"]]), 2),
            "assists": int(num(r[idx["A"]])),
            "xA": round(num(r[idx["XA"]]), 2),
            "body": round(num(r[idx["B"]]), 1),
        }

    rnd = args.round or max((s["games"] for s in scraped.values()), default=1)

    existing, order = {}, []
    if CSV_PATH.exists():
        for row in csv.DictReader(CSV_PATH.open(encoding="utf-8")):
            existing[row["name"]] = row
            order.append(row["name"])

    out, new_players = [], []
    for name in order:
        base = existing[name]
        s = scraped.get(name)
        if s:
            base.update(goals=str(s["goals"]), xG=f"{s['xG']:.2f}",
                        assists=str(s["assists"]), xA=f"{s['xA']:.2f}",
                        mins=str(s["mins"]))
        out.append(base)
    for name, s in scraped.items():
        if name in existing:
            continue
        pos = POS_MAP.get(s["po"], POS_MAP.get(s["po"][:1], "ZÁL"))
        if pos is None:
            continue
        out.append({"name": name, "pos": pos, "goals": str(s["goals"]),
                    "xG": f"{s['xG']:.2f}", "assists": str(s["assists"]),
                    "xA": f"{s['xA']:.2f}", "mins": str(s["mins"]), "tmValue": "0"})
        new_players.append(name)

    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["name", "pos", "goals", "xG",
                                          "assists", "xA", "mins", "tmValue"])
        w.writeheader(); w.writerows(out)

    # historie: snapshot za toto kolo (idempotentne)
    hist_fields = ["round", "name", "pos"] + STAT_COLS
    hist = []
    if HIST_PATH.exists():
        for row in csv.DictReader(HIST_PATH.open(encoding="utf-8")):
            if int(row["round"]) != rnd:
                hist.append(row)
    for r in out:
        s = scraped.get(r["name"], {})
        hist.append({
            "round": rnd, "name": r["name"], "pos": r["pos"],
            "mins": r["mins"], "goals": r["goals"], "xG": r["xG"],
            "assists": r["assists"], "xA": r["xA"],
            "body": f"{s.get('body', 0):.1f}" if s else "0.0",
        })
    hist.sort(key=lambda x: (int(x["round"]), x["name"]))
    with HIST_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=hist_fields)
        w.writeheader(); w.writerows(hist)

    print(f"\n[OK] {CSV_PATH} - {len(out)} hracu (aktualni stav)")
    print(f"[OK] {HIST_PATH} - pridan snapshot pro KOLO {rnd}")
    if new_players:
        print("\nNovi hraci (dopln tmValue z Transfermarktu):")
        for n in new_players:
            print(f"  - {n}")
    print("\nZkontroluj a commitni obe CSV.")


if __name__ == "__main__":
    main()
