"""
Sešívaní sobě – SK Slavia Praha Dashboard
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
from datetime import datetime

st.set_page_config(
    page_title="Sešívaní sobě | Slavia Dashboard",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  :root {
    --red:   #E8003D;
    --green: #0A3D2B;
    --green2:#0F5C3F;
    --white: #F5F5F0;
    --bg:    #060C08;
    --card:  #0D1A12;
    --border:#1A3025;
    --muted: #4A7A60;
  }

  html, body, [class*="css"], .stApp {
    background-color: var(--bg) !important;
    color: var(--white) !important;
    font-family: 'Inter', sans-serif !important;
  }
  .main, .block-container {
    background-color: var(--bg) !important;
    padding: 0 !important;
    max-width: 100% !important;
  }
  .block-container { padding: 0 2rem 4rem !important; max-width: 1200px !important; margin: 0 auto !important; }

  h1,h2,h3 { font-family: 'Bebas Neue', sans-serif !important; letter-spacing: 2px !important; color: var(--white) !important; }

  /* Metriky */
  div[data-testid="metric-container"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 20px !important;
  }
  div[data-testid="metric-container"] label {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 10px !important;
    letter-spacing: 3px !important;
    color: var(--muted) !important;
    text-transform: uppercase !important;
  }
  div[data-testid="metric-container"] > div > div {
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 32px !important;
    color: var(--white) !important;
  }
  div[data-testid="metric-container"] > div > div:last-child {
    font-size: 13px !important;
    font-family: 'JetBrains Mono', monospace !important;
    color: var(--red) !important;
  }

  /* Selectbox + radio */
  .stSelectbox label, .stRadio label, .stRadio div[role="radiogroup"] label {
    color: var(--muted) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 2px !important;
  }
  .stSelectbox > div > div, .stRadio > div {
    background: var(--card) !important;
    border-color: var(--border) !important;
    border-radius: 8px !important;
    color: var(--white) !important;
  }

  /* Dataframe – oprava viditelnosti */
  div[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid var(--border) !important;
  }
  div[data-testid="stDataFrame"] * {
    color: var(--white) !important;
  }
  .dvn-scroller { background: var(--card) !important; }
  .stDataFrame thead tr th {
    background: var(--green) !important;
    color: var(--white) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 10px !important;
    letter-spacing: 2px !important;
  }
  .stDataFrame tbody tr:nth-child(even) td {
    background: rgba(10,61,43,0.3) !important;
  }
  .stDataFrame tbody tr:hover td {
    background: rgba(232,0,61,0.08) !important;
  }

  /* Skryj Streamlit branding */
  footer, #MainMenu, header { display: none !important; }
  .stDeployButton { display: none !important; }
</style>
""", unsafe_allow_html=True)


# ── Pomocné funkce ────────────────────────────────────────────────────────────
def fmt_eur(val):
    if val is None or pd.isna(val) or val == 0: return "–"
    if val >= 1_000_000: return f"€{val/1_000_000:.1f}M"
    if val >= 1_000:     return f"€{val/1_000:.0f}K"
    return f"€{int(val)}"


@st.cache_data(ttl=1800)
def load_data():
    csv_path = Path("data/players.csv")
    if csv_path.exists():
        df = pd.read_csv(csv_path)
    else:
        df = pd.DataFrame([
            {"name": "Tomáš Chorý",     "pos": "ÚTO", "goals": 16, "xG": 11.02, "assists": 4,  "xA": 2.80, "mins": 1481, "tmValue": 3000000},
            {"name": "Mojmír Chytil",   "pos": "ÚTO", "goals": 10, "xG": 10.75, "assists": 0,  "xA": 2.46, "mins": 1158, "tmValue": 4000000},
            {"name": "Lukáš Provod",    "pos": "ZÁL", "goals": 6,  "xG": 4.40,  "assists": 8,  "xA": 6.05, "mins": 1859, "tmValue": 8000000},
            {"name": "Štěpán Chaloupek","pos": "OBR", "goals": 4,  "xG": 4.88,  "assists": 2,  "xA": 1.62, "mins": 1507, "tmValue": 8000000},
            {"name": "Michal Sadílek",  "pos": "ZÁL", "goals": 1,  "xG": 2.17,  "assists": 4,  "xA": 4.93, "mins": 1503, "tmValue": 8000000},
        ])

    df["xG_diff"]        = (df["goals"]   - df["xG"]).round(2)
    df["xA_diff"]        = (df["assists"] - df["xA"]).round(2)
    df["eur_per_goal"]   = df.apply(lambda r: round(r.tmValue / r.goals)   if r.goals   > 0 and r.tmValue > 0 else None, axis=1)
    df["eur_per_assist"] = df.apply(lambda r: round(r.tmValue / r.assists) if r.assists > 0 and r.tmValue > 0 else None, axis=1)
    df["eur_per_ga"]     = df.apply(lambda r: round(r.tmValue / (r.goals + r.assists)) if (r.goals + r.assists) > 0 and r.tmValue > 0 else None, axis=1)
    df["mins_per_goal"]  = df.apply(lambda r: round(r.mins / r.goals)   if r.goals   > 0 else None, axis=1)
    df["mins_per_assist"]= df.apply(lambda r: round(r.mins / r.assists) if r.assists > 0 else None, axis=1)
    df["mins_per_ga"]    = df.apply(lambda r: round(r.mins / (r.goals + r.assists)) if (r.goals + r.assists) > 0 else None, axis=1)
    return df


df = load_data()

# ── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="
  background: linear-gradient(135deg, #0A3D2B 0%, #0F5C3F 40%, #051A10 100%);
  padding: 40px 40px 32px;
  margin-bottom: 32px;
  position: relative;
  overflow: hidden;
  border-bottom: 2px solid #E8003D;
">
  <div style="position:absolute;right:40px;top:50%;transform:translateY(-50%);
    font-family:'Bebas Neue',sans-serif;font-size:140px;color:rgba(255,255,255,0.04);
    line-height:1;letter-spacing:-4px;user-select:none;">SKS</div>

  <div style="display:flex;align-items:center;gap:16px;margin-bottom:12px;">
    <div style="width:52px;height:52px;border-radius:50%;
      background:linear-gradient(135deg,#E8003D,#9B0028);
      display:flex;align-items:center;justify-content:center;
      font-family:'Bebas Neue',sans-serif;font-size:24px;color:white;
      border:2px solid rgba(255,255,255,0.15);">S</div>
    <div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:10px;
        letter-spacing:5px;color:rgba(255,255,255,0.4);margin-bottom:4px;">
        SEŠÍVANÍ SOBĚ · SK SLAVIA PRAHA</div>
      <div style="font-family:'Bebas Neue',sans-serif;font-size:38px;
        color:white;line-height:1;letter-spacing:2px;">
        Analytický dashboard</div>
    </div>
  </div>
  <div style="display:flex;gap:24px;margin-top:8px;">
    <div style="font-family:'JetBrains Mono',monospace;font-size:10px;
      color:rgba(255,255,255,0.3);letter-spacing:3px;">FORTUNA:LIGA</div>
    <div style="font-family:'JetBrains Mono',monospace;font-size:10px;
      color:rgba(255,255,255,0.3);letter-spacing:3px;">SEZÓNA 2025/26</div>
    <div style="font-family:'JetBrains Mono',monospace;font-size:10px;
      color:#E8003D;letter-spacing:3px;">xG · xA · HODNOTA</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── FILTRY ────────────────────────────────────────────────────────────────────
fc1, fc2, fc3 = st.columns([1, 1, 2])
with fc1:
    pos_filter = st.selectbox("POZICE", ["Všechny", "ÚTO", "ZÁL", "OBR"])
with fc2:
    min_mins = st.selectbox("MIN. MINUTY", [0, 300, 600, 900, 1200])
with fc3:
    scatter_mode = st.radio("ZOBRAZIT V GRAFU", ["Góly (xG)", "Asistence (xA)"], horizontal=True)

filtered = df.copy()
if pos_filter != "Všechny":
    filtered = filtered[filtered["pos"] == pos_filter]
filtered = filtered[filtered["mins"] >= min_mins]

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ── TOP METRIKY ───────────────────────────────────────────────────────────────
st.markdown("""<div style="font-family:'JetBrains Mono',monospace;font-size:10px;
  letter-spacing:4px;color:#4A7A60;margin-bottom:12px;">TOP HRÁČI</div>""", unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)

best_shooter = filtered.loc[filtered["xG_diff"].idxmax()]
m1.metric("Nejlepší střelec", best_shooter["name"].split()[-1],
          f"+{best_shooter['xG_diff']:.1f} nad xG")

best_assist = filtered.loc[filtered["xA_diff"].idxmax()]
m2.metric("Nejlepší asistent", best_assist["name"].split()[-1],
          f"+{best_assist['xA_diff']:.1f} nad xA")

eff = filtered.dropna(subset=["eur_per_ga"])
if not eff.empty:
    best_val = eff.loc[eff["eur_per_ga"].idxmin()]
    m3.metric("Nejlepší hodnota", best_val["name"].split()[-1],
              fmt_eur(best_val["eur_per_ga"]) + " / G+A")

fast = filtered.dropna(subset=["mins_per_ga"])
if not fast.empty:
    fastest = fast.loc[fast["mins_per_ga"].idxmin()]
    m4.metric("Nejefektivnější", fastest["name"].split()[-1],
              f"{int(fastest['mins_per_ga'])} min / G+A")

st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

# ── SCATTER ───────────────────────────────────────────────────────────────────
st.markdown("""<div style="font-family:'JetBrains Mono',monospace;font-size:10px;
  letter-spacing:4px;color:#4A7A60;margin-bottom:16px;">SCATTER ANALÝZA</div>""", unsafe_allow_html=True)

if scatter_mode == "Góly (xG)":
    x_col, y_col = "xG", "goals"
    x_lbl, y_lbl = "xG — očekávané góly", "Skutečné góly"
else:
    x_col, y_col = "xA", "assists"
    x_lbl, y_lbl = "xA — očekávané asistence", "Skutečné asistence"

# Scatter: zobraz jen hráče s alespoň nějakou hodnotou xG nebo xA
scatter_df = filtered[filtered[x_col] > 0.3].copy()

axis_max = max(scatter_df[x_col].max(), scatter_df[y_col].max()) * 1.2 + 0.5 if not scatter_df.empty else 5

colors, sizes = [], []
for _, row in scatter_df.iterrows():
    diff = row[y_col] - row[x_col]
    colors.append("#4ade80" if diff > 0.5 else "#f87171" if diff < -0.5 else "#facc15")
    sizes.append(14)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=[0, axis_max], y=[0, axis_max], mode="lines",
    line=dict(color="#1A3025", dash="dash", width=1),
    showlegend=False, hoverinfo="skip"
))
fig.add_trace(go.Scatter(
    x=scatter_df[x_col], y=scatter_df[y_col],
    mode="markers+text",
    text=scatter_df["name"].str.split().str[-1],
    textposition="top center",
    textfont=dict(size=10, color="rgba(245,245,240,0.6)", family="JetBrains Mono"),
    marker=dict(size=sizes, color=colors,
                line=dict(color="rgba(255,255,255,0.1)", width=1)),
    customdata=scatter_df[["name", x_col, y_col]].values,
    hovertemplate="<b>%{customdata[0]}</b><br>" +
                  f"{x_lbl}: %{{customdata[1]:.2f}}<br>" +
                  f"{y_lbl}: %{{customdata[2]}}<extra></extra>",
))

fig.update_layout(
    paper_bgcolor="#0D1A12", plot_bgcolor="#0D1A12",
    font=dict(color="#4A7A60", family="JetBrains Mono"),
    xaxis=dict(title=x_lbl, gridcolor="#1A3025", zeroline=False,
               range=[0, axis_max], color="#4A7A60"),
    yaxis=dict(title=y_lbl, gridcolor="#1A3025", zeroline=False,
               range=[0, axis_max], color="#4A7A60"),
    margin=dict(l=50, r=20, t=20, b=50),
    height=400,
    showlegend=False,
    hoverlabel=dict(bgcolor="#0A3D2B", bordercolor="#E8003D",
                    font=dict(family="JetBrains Mono", size=12)),
)
st.plotly_chart(fig, use_container_width=True)

lc1, lc2, lc3 = st.columns(3)
lc1.markdown("<div style='font-size:12px;color:#4ade80;font-family:JetBrains Mono,monospace'>● Překonává xG/xA</div>", unsafe_allow_html=True)
lc2.markdown("<div style='font-size:12px;color:#facc15;font-family:JetBrains Mono,monospace'>● Blízko očekávání</div>", unsafe_allow_html=True)
lc3.markdown("<div style='font-size:12px;color:#f87171;font-family:JetBrains Mono,monospace'>● Nedosahuje xG/xA</div>", unsafe_allow_html=True)

st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

# ── TABULKA ───────────────────────────────────────────────────────────────────
st.markdown("""<div style="font-family:'JetBrains Mono',monospace;font-size:10px;
  letter-spacing:4px;color:#4A7A60;margin-bottom:12px;">PŘEHLED HRÁČŮ</div>""", unsafe_allow_html=True)

sort_col = st.selectbox("SEŘADIT PODLE", [
    "goals", "xG", "xG_diff", "assists", "xA", "xA_diff",
    "tmValue", "eur_per_goal", "eur_per_assist", "mins_per_ga"
], format_func=lambda x: {
    "goals": "Góly", "xG": "xG", "xG_diff": "G – xG",
    "assists": "Asistence", "xA": "xA", "xA_diff": "A – xA",
    "tmValue": "Hodnota TM", "eur_per_goal": "€ / Gól",
    "eur_per_assist": "€ / Asistence", "mins_per_ga": "Min / G+A"
}[x])

asc = sort_col not in ["goals", "assists", "tmValue", "xG", "xA"]
table_df = filtered.sort_values(sort_col, ascending=asc, na_position="last")

def color_diff(val):
    try:
        v = float(val)
        if v > 0:   return f'<span style="color:#4ade80;font-weight:700">+{val}</span>'
        elif v < 0: return f'<span style="color:#f87171;font-weight:700">{val}</span>'
        else:       return f'<span style="color:#facc15">{val}</span>'
    except:
        return val

rows_html = ""
for _, row in table_df.iterrows():
    rows_html += f"""
    <tr>
      <td style="font-weight:600;color:#F5F5F0">{row['name']}</td>
      <td style="color:#4A7A60;font-family:monospace">{row['pos']}</td>
      <td style="color:#F5F5F0;font-weight:700">{row['goals']}</td>
      <td style="color:#888">{row['xG']:.1f}</td>
      <td>{color_diff(f"{row['xG_diff']:.2f}")}</td>
      <td style="color:#F5F5F0;font-weight:700">{row['assists']}</td>
      <td style="color:#888">{row['xA']:.1f}</td>
      <td>{color_diff(f"{row['xA_diff']:.2f}")}</td>
      <td style="color:#888">{row['mins']}</td>
      <td style="color:#E8003D">{fmt_eur(row['tmValue'])}</td>
      <td style="color:#F5F5F0">{fmt_eur(row['eur_per_goal']) if pd.notna(row['eur_per_goal']) and row['eur_per_goal'] else '–'}</td>
      <td style="color:#F5F5F0">{fmt_eur(row['eur_per_assist']) if pd.notna(row['eur_per_assist']) and row['eur_per_assist'] else '–'}</td>
      <td style="color:#F5F5F0">{str(int(row['mins_per_ga'])) if pd.notna(row['mins_per_ga']) and row['mins_per_ga'] else '–'}</td>
    </tr>"""

st.markdown(f"""
<div style="overflow-x:auto;border-radius:12px;border:1px solid #1A3025;">
<table style="width:100%;border-collapse:collapse;font-size:13px;font-family:'Inter',sans-serif;">
  <thead>
    <tr style="background:#0A3D2B;border-bottom:1px solid #1A3025;">
      {''.join(f'<th style="padding:10px 12px;text-align:left;font-family:monospace;font-size:10px;letter-spacing:2px;color:#4A7A60;white-space:nowrap">{c}</th>'
               for c in ["HRÁČ","POS","G","xG","G–xG","A","xA","A–xA","MIN","TM €","€/G","€/A","MIN/G+A"])}
    </tr>
  </thead>
  <tbody>
    {rows_html}
  </tbody>
</table>
</div>
<style>
  table tr:nth-child(even) {{ background: rgba(10,61,43,0.2); }}
  table tr:hover {{ background: rgba(232,0,61,0.06) !important; }}
  table td {{ padding: 9px 12px; border-bottom: 1px solid #0D1A12; white-space:nowrap; }}
</style>
""", unsafe_allow_html=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
csv_path = Path("data/players.csv")
updated = ""
if csv_path.exists():
    mtime = csv_path.stat().st_mtime
    updated = f"· Data: {datetime.fromtimestamp(mtime).strftime('%-d. %-m. %Y')}"

st.markdown(f"""
<div style="text-align:center;margin-top:48px;padding:20px 0;
  border-top:1px solid #1A3025;">
  <div style="font-family:'JetBrains Mono',monospace;font-size:9px;
    letter-spacing:4px;color:#1A3025;">
    SEŠÍVANÍ SOBĚ {updated} · ZDROJ: CHANCELIGA.CZ & TRANSFERMARKT
  </div>
</div>
""", unsafe_allow_html=True)
