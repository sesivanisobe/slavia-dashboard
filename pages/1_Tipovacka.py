"""
Sešívaní sobě – SKS Tipovačka 2026/27
Stránka pro tipování výsledků a xG, žebříček sezóny.

Identifikace uživatele: přes URL parametry ?u=jmeno&t=token
(žádný login/heslo - token slouží jen k rozpoznání osoby, ne k zabezpečení)
"""

import streamlit as st
import pandas as pd
import random
from datetime import datetime
from zoneinfo import ZoneInfo
import gspread
from google.oauth2.service_account import Credentials

from scoring import Tip, Vysledek, spocitej_body

CASOVA_ZONA = ZoneInfo("Europe/Prague")

HLASKY_PO_ULOZENI = [
    "Díky za tip, Slávisto! ✌️",
    "Skvělý tip, ať vyjde! 💪",
    "Tip jsme uložili, ať žije Slavia! ❤️🤍",
    "To nemá kam! 👍",
]


def ted_praha() -> datetime:
    """
    Aktuální čas v pražské časové zóně - BEZ ohledu na to, v jaké časové zóně
    běží server appky (Streamlit Cloud běží v UTC). Vrací naivní datetime
    (bez tzinfo), ať se dá přímo porovnávat s deadliny zadanými ručně
    v Google Sheets (ty jsou taky bez časové zóny, v pražském čase).
    """
    return datetime.now(CASOVA_ZONA).replace(tzinfo=None)


def cz(hodnota, desetiny=2) -> str:
    """Zobrazí číslo s desetinnou čárkou (jen pro zobrazení uživateli - interně
    a v datech zůstává tečka, aby tomu rozuměly všechny knihovny/Google Sheets)."""
    return f"{hodnota:.{desetiny}f}".replace(".", ",")

st.set_page_config(
    page_title="SKS Tipovačka | Sešívaní sobě",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── STYL (sjednocený s hlavním dashboardem) ─────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  html, body, [class*="css"], .stApp {
    background-color: #060C08 !important;
    color: #F5F5F0 !important;
    font-family: 'Inter', sans-serif !important;
  }
  .main { background-color: #060C08 !important; }
  .block-container {
    background-color: #060C08 !important;
    padding: 0 2rem 4rem !important;
    max-width: 1000px !important;
    margin: 0 auto !important;
  }
  h1,h2,h3 { font-family: 'Bebas Neue', sans-serif !important; letter-spacing: 2px !important; color: #F5F5F0 !important; }
  div[data-testid="metric-container"] {
    background: #0D1A12 !important; border: 1px solid #1A3025 !important;
    border-radius: 12px !important; padding: 20px !important;
  }
  div[data-testid="metric-container"] label {
    font-family: 'JetBrains Mono', monospace !important; font-size: 10px !important;
    letter-spacing: 3px !important; color: #4A7A60 !important; text-transform: uppercase !important;
  }
  .stTabs [data-baseweb="tab"] {
    font-family: 'JetBrains Mono', monospace !important; font-size: 12px !important;
    letter-spacing: 2px !important;
  }
  .stNumberInput label {
    color: #4A7A60 !important; font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important; letter-spacing: 2px !important;
  }
  footer, #MainMenu, header { display: none !important; }
  .stDeployButton { display: none !important; }
</style>
""", unsafe_allow_html=True)


# ── PŘIPOJENÍ NA GOOGLE SHEETS ───────────────────────────────────────────────
@st.cache_resource
def ziskej_klienta():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    return gspread.authorize(creds)


@st.cache_resource
def ziskej_sheet():
    klient = ziskej_klienta()
    return klient.open_by_url(st.secrets["tipovacka"]["sheet_url"])


@st.cache_data(ttl=30)
def nacti_list(nazev_listu: str) -> pd.DataFrame:
    sheet = ziskej_sheet()
    ws = sheet.worksheet(nazev_listu)
    # value_render_option="UNFORMATTED_VALUE" - bereme skutečnou hodnotu buňky,
    # ne tu zobrazenou podle lokalizace sheetu (jinak gspread plete českou desetinnou
    # čárku s americkým oddělovačem tisíců, např. "4,25" -> 425)
    data = ws.get_all_records(value_render_option="UNFORMATTED_VALUE")
    return pd.DataFrame(data)


def uloz_tip(zapas_id, jmeno, skore_domaci, skore_hoste, tip_xg):
    sheet = ziskej_sheet()
    ws = sheet.worksheet("tipy")
    ws.append_row([
        str(zapas_id), jmeno, int(skore_domaci), int(skore_hoste), float(tip_xg),
        ted_praha().strftime("%Y-%m-%d %H:%M:%S"),
    ])


# ── OVĚŘENÍ UŽIVATELE Z URL ──────────────────────────────────────────────────
query_params = st.query_params
jmeno = query_params.get("u", "")
token = query_params.get("t", "")

st.markdown(
    '<div style="font-family:monospace;font-size:10px;letter-spacing:5px;'
    'color:rgba(255,255,255,0.4);margin:24px 0 4px;">SEŠÍVANÍ SOBĚ · SK SLAVIA PRAHA</div>'
    '<div style="font-size:36px;font-weight:800;color:white;line-height:1.1;'
    'letter-spacing:2px;margin-bottom:24px;">SKS Tipovačka 2026/27</div>',
    unsafe_allow_html=True,
)

if not jmeno or not token:
    st.error(
        "Chybí odkaz s tvým jménem. Tipovat můžeš jen přes svůj osobní odkaz, "
        "který ti přišel do WhatsApp skupiny. Pokud ho nemůžeš najít, ozvi se administrátorovi."
    )
    st.stop()

try:
    uzivatele_df = nacti_list("uzivatele")
except Exception as e:
    st.error(f"Nepodařilo se načíst data z Google Sheets. Zkus to prosím za chvíli znovu. ({e})")
    st.stop()

shoda = uzivatele_df[
    (uzivatele_df["jmeno"].str.lower() == jmeno.lower())
    & (uzivatele_df["token"].astype(str) == token)
]

if shoda.empty:
    st.error("Odkaz není platný. Zkontroluj, jestli jsi ho zkopíroval celý, nebo se ozvi administrátorovi.")
    st.stop()

zobrazovane_jmeno = shoda.iloc[0]["jmeno"]
st.success(f"Ahoj, {zobrazovane_jmeno}! 👋")

# ── NAČTENÍ ZÁPASŮ, TIPŮ A VÝSLEDKŮ ──────────────────────────────────────────
zapasy_df = nacti_list("zapasy")
tipy_df = nacti_list("tipy")
vysledky_df = nacti_list("vysledky")

if zapasy_df.empty or "deadline" not in zapasy_df.columns:
    st.warning(
        "V listu 'zapasy' zatím nejsou žádné zápasy k tipování (nebo chybí sloupec "
        "'deadline'). Přidej zápasy do Google Sheets a stránku obnov."
    )
    st.stop()

ted = ted_praha()


def over_datum(hodnota):
    """
    Zvládne datum zadané jako text ('2026-07-25 17:00') i jako syrové sériové
    číslo Google Sheets (pokud si Sheets text sám převedl na interní datum).
    """
    if isinstance(hodnota, (int, float)):
        return pd.to_datetime("1899-12-30") + pd.to_timedelta(hodnota, unit="D")
    return pd.to_datetime(hodnota)


zapasy_df["deadline_dt"] = zapasy_df["deadline"].apply(over_datum)
otevrene = zapasy_df[zapasy_df["deadline_dt"] > ted].copy()

moje_tipy = tipy_df[tipy_df["jmeno"] == zobrazovane_jmeno] if not tipy_df.empty else pd.DataFrame()
jiz_tipovane_id = set(moje_tipy["zapas_id"].astype(str)) if not moje_tipy.empty else set()

tab_tip, tab_moje, tab_zebricek = st.tabs(["📝 TIPNOUT", "📋 MOJE TIPY", "🏆 ŽEBŘÍČEK"])

# ── TAB: TIPNOUT ──────────────────────────────────────────────────────────
with tab_tip:
    k_tipovani = otevrene[~otevrene["zapas_id"].astype(str).isin(jiz_tipovane_id)]

    if k_tipovani.empty:
        st.info("Momentálně nejsou otevřené žádné zápasy k tipování. Zkus to znovu blíž k dalšímu kolu.")
    else:
        for _, zapas in k_tipovani.sort_values("deadline_dt").iterrows():
            with st.container(border=True):
                st.markdown(
                    f"**Kolo {zapas['kolo']} · {zapas['domaci_tym']} – {zapas['hoste_tym']}**  \n"
                    f"<span style='font-family:monospace;font-size:11px;color:#4A7A60;'>"
                    f"Uzávěrka tipů: {zapas['deadline_dt'].strftime('%d.%m. %H:%M')}</span>",
                    unsafe_allow_html=True,
                )
                c1, c2, c3 = st.columns(3)
                with c1:
                    skore_d = st.number_input(
                        f"Skóre {zapas['domaci_tym']}", min_value=0, max_value=15, step=1,
                        key=f"d_{zapas['zapas_id']}",
                    )
                with c2:
                    skore_h = st.number_input(
                        f"Skóre {zapas['hoste_tym']}", min_value=0, max_value=15, step=1,
                        key=f"h_{zapas['zapas_id']}",
                    )
                with c3:
                    tip_xg = st.number_input(
                        "xG Slavie", min_value=0.0, max_value=10.0, step=0.1, format="%.2f",
                        key=f"xg_{zapas['zapas_id']}",
                    )

                if st.button("Odeslat tip", key=f"submit_{zapas['zapas_id']}", type="primary"):
                    uloz_tip(zapas["zapas_id"], zobrazovane_jmeno, skore_d, skore_h, tip_xg)
                    st.cache_data.clear()
                    st.toast(random.choice(HLASKY_PO_ULOZENI), icon="✅")
                    st.rerun()

# ── TAB: MOJE TIPY ────────────────────────────────────────────────────────
with tab_moje:
    if moje_tipy.empty:
        st.info("Zatím jsi netipoval žádný zápas.")
    else:
        zobrazit = moje_tipy.merge(zapasy_df, on="zapas_id", how="left")
        if not vysledky_df.empty:
            zobrazit = zobrazit.merge(vysledky_df, on="zapas_id", how="left", suffixes=("", "_real"))

        for _, r in zobrazit.sort_values("kolo", ascending=False).iterrows():
            with st.container(border=True):
                popis = f"**Kolo {r['kolo']} · {r['domaci_tym']} – {r['hoste_tym']}**"
                tip_txt = f"Tvůj tip: {int(r['skore_domaci'])}:{int(r['skore_hoste'])}, xG {cz(r['tip_xg'])}"
                if pd.notna(r.get("skore_domaci_real", pd.NA)):
                    tip = Tip(int(r["skore_domaci"]), int(r["skore_hoste"]), float(r["tip_xg"]))
                    vysledek = Vysledek(int(r["skore_domaci_real"]), int(r["skore_hoste_real"]), float(r["xg_slavia"]))
                    body = spocitej_body(tip, vysledek)
                    st.markdown(f"{popis}  \n{tip_txt}  \nSkutečnost: {int(r['skore_domaci_real'])}:{int(r['skore_hoste_real'])}, xG {cz(r['xg_slavia'])}")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Za výsledek", f"{body.za_vysledek} b")
                    m2.metric("Za xG", f"{body.za_xg} b", f"odchylka {cz(body.odchylka_xg)}")
                    m3.metric("Celkem", f"{body.celkem} b")
                else:
                    st.markdown(f"{popis}  \n{tip_txt}  \n*Zápas ještě neproběhl / výsledek nezadán.*")

# ── TAB: ŽEBŘÍČEK ─────────────────────────────────────────────────────────
with tab_zebricek:
    if tipy_df.empty or vysledky_df.empty:
        st.info("Zatím nejsou k dispozici žádné vyhodnocené zápasy.")
    else:
        spojene = tipy_df.merge(vysledky_df, on="zapas_id", how="inner", suffixes=("", "_real"))
        vysledky_body = []
        for _, r in spojene.iterrows():
            tip = Tip(int(r["skore_domaci"]), int(r["skore_hoste"]), float(r["tip_xg"]))
            vysledek = Vysledek(int(r["skore_domaci_real"]), int(r["skore_hoste_real"]), float(r["xg_slavia"]))
            body = spocitej_body(tip, vysledek)
            vysledky_body.append({"jmeno": r["jmeno"], "body": body.celkem, "presny_vysledek": body.za_vysledek == 100})

        body_df = pd.DataFrame(vysledky_body)
        souhrn = body_df.groupby("jmeno").agg(
            celkem_bodu=("body", "sum"),
            odehrano=("body", "count"),
            presnych_vysledku=("presny_vysledek", "sum"),
        ).reset_index()
        souhrn["prumer_na_zapas"] = (souhrn["celkem_bodu"] / souhrn["odehrano"]).round(1).apply(lambda x: cz(x, 1))
        souhrn = souhrn.sort_values(
            ["celkem_bodu", "presnych_vysledku"], ascending=[False, False]
        ).reset_index(drop=True)
        souhrn.index = souhrn.index + 1

        st.dataframe(
            souhrn.rename(columns={
                "jmeno": "Jméno", "celkem_bodu": "Body celkem", "odehrano": "Odehráno zápasů",
                "presnych_vysledku": "Přesných výsledků", "prumer_na_zapas": "Průměr / zápas",
            }),
            use_container_width=True,
        )

st.markdown(
    "<div style='text-align:center;margin-top:48px;padding:20px 0;border-top:1px solid #1A3025;'>"
    "<div style='font-family:monospace;font-size:9px;letter-spacing:4px;color:#1A3025;'>"
    "SEŠÍVANÍ SOBĚ · SKS TIPOVAČKA 2026/27"
    "</div></div>",
    unsafe_allow_html=True,
)
