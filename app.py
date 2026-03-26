"""
Sešívaní sobě – SK Slavia Praha Dashboard
==========================================
Streamlit app pro zobrazení statistik hráčů:
xG vs góly, xA vs asistence, hodnota z Transfermarktu

Spuštění lokálně:
  pip install streamlit pandas plotly
  streamlit run app.py
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
from datetime import datetime

# ── Konfigurace stránky ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sešívaní sobě | Slavia Dashboard",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Vlastní CSS – barvy Slavie ─────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800&family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600&display=swap');

  html, body, [class*="css"] {
    background-color: #080808 !important;
    color: #ede8e0 !important;
    font-family: 'DM Sans', sans-serif;
  }
  .main { background-color: #080808; }
  .block-container { padding: 2rem 2rem 4rem; max-width: 1200px; }

  h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: #ede8e0 !important; }

  .stMetric {
    background: #111 !important;
    border: 1px solid #1f1f1f;
    border-radius: 12px;
    padding: 16px !important;
  }
  .stMetric label { 
    font-family: 'DM Mono', monospace !important; 
    font-size: 10px !important; 
    letter-spacing: 3px !important;
    color: #555 !important;
    text-transform: uppercase;
  }
  .stMetric [data-testid="metric-container"] > div:nth-child(2) {
    font-size: 28px !important;
    font-weight: 800 !important;
    color: #e8003d !important;
  }

  div[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }

  .stSelectbox > div, .stMultiSelect > div {
    background: #111 !important;
    border-color: #222 !important;
    border-radius: 8px !important;
  }

  .header-label {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 4px;
    color: #e8003d;
    text-transform: uppercase;
    margin-bottom: 4px;
  }
  .player-card {
    background: linear-gradient(135deg, #1c0009, #130006);
    border: 1px solid rgba(232,0,61,0.3);
    border-radius: 16px;
    padding: 20px 24px;
  }
  .player-name {
    font-family: 'Playfair Display', serif;
    font-size: 24px;
    font-weight: 800;
    margin-bottom: 4px;
  }
  .pos-badge {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 3px;
    color: #e8003d;
  }
  .stat-val {
    font-size: 28px;
    font-weight: 800;
    color: #e8003d;
    line-height: 1;
  }
  .stat-label {
    font-family: 'DM Mono', monospace;
    font-size: 9px;
    letter-spacing: 2px;
    color: #444;
    margin-top: 4px;
  }
  .diff-pos { color: #4ade80; font-weight: 700; font-size: 13px; }
  .diff-neg { color: #f87171; font-weight: 700; font-size: 13px; }
  .divider {
    border: none;
    border-top: 1px solid #1a1a1a;
    margin: 24px 0;
  }
  footer { display: none; }
  #MainMenu { display: none; }
  header { display: none; }
</style>
""", unsafe_allow_html=True)

# ── Načtení dat ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_data():
    csv_path = Path("data/players.csv")
    if csv_path.exists():
        df = pd.read_csv(csv_path)
    else:
        # Ilustrační data jako záloha
        df = pd.DataFrame([
            {"name": "Tomáš Chorý",     "pos": "ÚTO", "goals": 14, "xG": 10.8, "assists": 4,  "xA": 3.2,  "mins": 1980, "tmValue": 3000000},
            {"name": "Ivan Schranz",    "pos": "ÚTO", "goals": 11, "xG": 12.1, "assists": 5,  "xA": 4.8,  "mins": 2100, "tmValue": 4000000},
            {"name": "Matěj Jurásek",   "pos": "ZÁL", "goals": 9,  "xG": 7.4,  "assists": 7,  "xA": 6.1,  "mins": 2210, "tmValue": 5000000},
            {"name": "Ondřej Lingr",    "pos": "ZÁL", "goals": 7,  "xG": 5.9,  "assists": 6,  "xA": 7.3,  "mins": 1650, "tmValue": 3500000},
            {"name": "Alexej Jurčenko", "pos": "ÚTO", "goals": 8,  "xG": 9.2,  "assists": 3,  "xA": 2.1,  "mins": 1420, "tmValue": 2000000},
            {"name": "Oscar",           "pos": "ZÁL", "goals": 6,  "xG": 4.1,  "assists": 11, "xA": 9.4,  "mins": 2560, "tmValue": 6000000},
            {"name": "Lukáš Provod",    "pos": "ZÁL", "goals": 5,  "xG": 6.8,  "assists": 8,  "xA": 6.5,  "mins": 1870, "tmValue": 4500000},
            {"name": "David Douděra",   "pos": "OBR", "goals": 3,  "xG": 2.1,  "assists": 9,  "xA": 7.2,  "mins": 2430, "tmValue": 5000000},
            {"name": "Jan Bořil",       "pos": "OBR", "goals": 2,  "xG": 1.8,  "assists": 4,  "xA": 4.9,  "mins": 2050, "tmValue": 1000000},
            {"name": "Aiham Ousou",     "pos": "OBR", "goals": 1,  "xG": 1.2,  "assists": 2,  "xA": 1.8,  "mins": 2360, "tmValue": 3000000},
        ])
    # Odvozené metriky
    df["xG_diff"]        = (df["goals"]   - df["xG"]).round(2)
    df["xA_diff"]        = (df["assists"] - df["xA"]).round(2)
    df["eur_per_goal"]   = df.apply(lambda r: round(r.tmValue / r.goals)   if r.goals   > 0 else None, axis=1)
    df["eur_per_assist"] = df.apply(lambda r: round(r.tmValue / r.assists) if r.assists > 0 else None, axis=1)
    df["eur_per_ga"]     = df.apply(lambda r: round(r.tmValue / (r.goals + r.assists)) if (r.goals + r.assists) > 0 else None, axis=1)
    df["mins_per_goal"]  = df.apply(lambda r: round(r.mins / r.goals)   if r.goals   > 0 else None, axis=1)
    df["mins_per_assist"]= df.apply(lambda r: round(r.mins / r.assists) if r.assists > 0 else None, axis=1)
    df["mins_per_ga"]    = df.apply(lambda r: round(r.mins / (r.goals + r.assists)) if (r.goals + r.assists) > 0 else None, axis=1)
    return df

def fmt_eur(val):
    if val is None or pd.isna(val): return "–"
    if val >= 1_000_000: return f"€{val/1_000_000:.1f}M"
    if val >= 1_000:     return f"€{val/1_000:.0f}K"
    return f"€{val:.0f}"

def diff_html(val):
    if val > 0:  return f'<span class="diff-pos">▲ +{val}</span>'
    if val < 0:  return f'<span class="diff-neg">▼ {val}</span>'
    return f'<span style="color:#facc15">● {val}</span>'

# ── Načti data ────────────────────────────────────────────────────────────────
df = load_data()

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(160deg,#c8002a 0%,#6b0018 50%,#0d0d0d 100%);
     border-radius:16px;padding:36px 32px 28px;margin-bottom:28px;position:relative;overflow:hidden;">
  <div style="position:absolute;right:-40px;top:-40px;width:220px;height:220px;
       border-radius:50%;border:1px solid rgba(255,255,255,0.06);"></div>
  <div style="font-family:'DM Mono',monospace;font-size:10px;letter-spacing:5px;
       color:rgba(255,255,255,0.5);margin-bottom:10px;">
    SEŠÍVANÍ SOBĚ · SK SLAVIA PRAHA
  </div>
  <div style="font-family:'Playfair Display',serif;font-size:32px;font-weight:800;
       color:white;line-height:1.1;margin-bottom:8px;">
    xG / xA vs skutečnost<br>
    <span style="font-size:18px;font-weight:400;color:rgba(255,255,255,0.45);">
      & hodnota hráčů
    </span>
  </div>
  <div style="font-family:'DM Mono',monospace;font-size:10px;letter-spacing:3px;
       color:rgba(255,255,255,0.3);">
    FORTUNA:LIGA · SEZÓNA 2024/25
  </div>
</div>
""", unsafe_allow_html=True)

# ── FILTRY ────────────────────────────────────────────────────────────────────
col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
with col_f1:
    pos_filter = st.selectbox("Pozice", ["Všechny", "ÚTO", "ZÁL", "OBR", "BRA"])
with col_f2:
    min_mins = st.selectbox("Min. minuty", [0, 300, 600, 900, 1200], index=0)
with col_f3:
    scatter_mode = st.radio("Scatter graf", ["Góly (xG)", "Asistence (xA)"], horizontal=True)

# Filtrování
filtered = df.copy()
if pos_filter != "Všechny":
    filtered = filtered[filtered["pos"] == pos_filter]
filtered = filtered[filtered["mins"] >= min_mins]

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ── SCATTER PLOT ──────────────────────────────────────────────────────────────
st.markdown('<div class="header-label">Scatter analýza</div>', unsafe_allow_html=True)

if scatter_mode == "Góly (xG)":
    x_col, y_col = "xG", "goals"
    x_label, y_label = "xG (očekávané góly)", "Skutečné góly"
else:
    x_col, y_col = "xA", "assists"
    x_label, y_label = "xA (očekávané asistence)", "Skutečné asistence"

axis_max = max(filtered[x_col].max(), filtered[y_col].max()) * 1.15

fig_scatter = go.Figure()

# Diagonála = ideální linie
fig_scatter.add_trace(go.Scatter(
    x=[0, axis_max], y=[0, axis_max],
    mode="lines",
    line=dict(color="#333", dash="dash", width=1),
    showlegend=False, hoverinfo="skip"
))

# Barevné kódování
colors = []
for _, row in filtered.iterrows():
    diff = row[y_col] - row[x_col]
    if diff > 0.5:   colors.append("#4ade80")
    elif diff < -0.5: colors.append("#f87171")
    else:             colors.append("#facc15")

fig_scatter.add_trace(go.Scatter(
    x=filtered[x_col],
    y=filtered[y_col],
    mode="markers+text",
    text=filtered["name"].str.split().str[-1],
    textposition="top center",
    textfont=dict(size=10, color="rgba(255,255,255,0.7)", family="DM Mono"),
    marker=dict(size=14, color=colors, line=dict(color="rgba(255,255,255,0.2)", width=1)),
    customdata=filtered[["name", "pos", x_col, y_col]].values,
    hovertemplate=(
        "<b>%{customdata[0]}</b><br>"
        f"{x_label}: %{{customdata[2]:.2f}}<br>"
        f"{y_label}: %{{customdata[3]}}<br>"
        "<extra></extra>"
    )
))

fig_scatter.update_layout(
    paper_bgcolor="#0f0f0f", plot_bgcolor="#0f0f0f",
    font=dict(color="#888", family="DM Mono"),
    xaxis=dict(title=x_label, gridcolor="#1a1a1a", zeroline=False, range=[0, axis_max]),
    yaxis=dict(title=y_label, gridcolor="#1a1a1a", zeroline=False, range=[0, axis_max]),
    margin=dict(l=40, r=20, t=20, b=40),
    height=420,
    showlegend=False,
)

st.plotly_chart(fig_scatter, use_container_width=True)

# Legenda
leg_col1, leg_col2, leg_col3 = st.columns(3)
leg_col1.markdown("🟢 **Překonává** xG/xA")
leg_col2.markdown("🟡 **Blízko** očekávání")
leg_col3.markdown("🔴 **Nedosahuje** xG/xA")

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ── TABULKA ───────────────────────────────────────────────────────────────────
st.markdown('<div class="header-label">Přehled hráčů</div>', unsafe_allow_html=True)

sort_col = st.selectbox("Seřadit podle", [
    "goals", "xG", "xG_diff", "assists", "xA", "xA_diff",
    "tmValue", "eur_per_goal", "eur_per_assist", "mins_per_ga"
], format_func=lambda x: {
    "goals": "Góly", "xG": "xG", "xG_diff": "G – xG",
    "assists": "Asistence", "xA": "xA", "xA_diff": "A – xA",
    "tmValue": "Hodnota TM", "eur_per_goal": "€ / Gól",
    "eur_per_assist": "€ / Asistence", "mins_per_ga": "Min / G+A"
}[x])

table_df = filtered.sort_values(sort_col, ascending=False if sort_col in ["goals","assists","tmValue","xG","xA"] else True)

# Formátovaná tabulka
display_df = pd.DataFrame({
    "Hráč":       table_df["name"],
    "Pos":        table_df["pos"],
    "G":          table_df["goals"],
    "xG":         table_df["xG"].round(1),
    "G–xG":       table_df["xG_diff"],
    "A":          table_df["assists"],
    "xA":         table_df["xA"].round(1),
    "A–xA":       table_df["xA_diff"],
    "Minuty":     table_df["mins"],
    "TM €":       table_df["tmValue"].apply(fmt_eur),
    "€/Gól":      table_df["eur_per_goal"].apply(lambda v: fmt_eur(v) if v else "–"),
    "€/Asist.":   table_df["eur_per_assist"].apply(lambda v: fmt_eur(v) if v else "–"),
    "Min/G+A":    table_df["mins_per_ga"].apply(lambda v: str(int(v)) if v else "–"),
})

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "G–xG": st.column_config.NumberColumn(format="%.2f"),
        "A–xA": st.column_config.NumberColumn(format="%.2f"),
    }
)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ── TOP METRIKY ───────────────────────────────────────────────────────────────
st.markdown('<div class="header-label">Top hráči</div>', unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)

best_finisher = filtered.loc[filtered["xG_diff"].idxmax()]
m1.metric("Nejlepší finišer", best_finisher["name"].split()[-1],
          f"+{best_finisher['xG_diff']:.1f} nad xG")

best_creator = filtered.loc[filtered["xA_diff"].idxmax()]
m2.metric("Nejlepší kreátor", best_creator["name"].split()[-1],
          f"+{best_creator['xA_diff']:.1f} nad xA")

eff = filtered.dropna(subset=["eur_per_ga"])
if not eff.empty:
    best_value = eff.loc[eff["eur_per_ga"].idxmin()]
    m3.metric("Nejlepší hodnota €", best_value["name"].split()[-1],
              fmt_eur(best_value["eur_per_ga"]) + " / G+A")

fast = filtered.dropna(subset=["mins_per_ga"])
if not fast.empty:
    fastest = fast.loc[fast["mins_per_ga"].idxmin()]
    m4.metric("Nejefektivnější (min)", fastest["name"].split()[-1],
              f"{int(fastest['mins_per_ga'])} min / G+A")

# ── FOOTER ────────────────────────────────────────────────────────────────────
csv_date = ""
if Path("data/players.csv").exists():
    mtime = Path("data/players.csv").stat().st_mtime
    csv_date = f"· Data aktualizována {datetime.fromtimestamp(mtime).strftime('%-d. %-m. %Y')}"

st.markdown(f"""
<div style="text-align:center;padding:32px 0 8px;
     font-family:'DM Mono',monospace;font-size:9px;letter-spacing:3px;color:#222;">
  SEŠÍVANÍ SOBĚ PODCAST {csv_date} · ZDROJ: CHANCELIGA.CZ & TRANSFERMARKT
</div>
""", unsafe_allow_html=True)
