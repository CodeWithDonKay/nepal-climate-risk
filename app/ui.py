"""Design system for the Nepal Climate Risk Intelligence Platform.

Everything visual lives here: colour tokens, typography, page CSS, the shared Plotly template, risk bands
and reusable components (page header, cards, KPI cards, notes, findings, status chips, tables).

Accessibility rules applied throughout (WCAG 2.2 AA design targets; see About page for what was verified):
  * text colours were checked for >= 4.5:1 contrast; chart marks and UI boundaries for >= 3:1
  * risk levels always carry a text label and a shape/meter, never colour alone
  * chart series are distinguished by colour AND dash style / marker / direct labels
  * every interactive element gets a visible keyboard focus ring
"""
import html
from contextlib import contextmanager

import plotly.graph_objects as go
import plotly.io as pio
from plotly.colors import sample_colorscale
import streamlit as st

# ---------------------------------------------------------------- colour tokens
NAVY, NAV_HOVER, NAV_ACTIVE = "#112B49", "#244B73", "#195B96"
BG, CARD, BORDER = "#F4F7FB", "#FFFFFF", "#E2E8F0"
HEAD, BODY, MUTED = "#172B4D", "#334155", "#526579"
PRIMARY, WARN = "#0072B2", "#B84A00"
CONTEXT = "#76879A"          # grey for context data; 3.7:1 on white

# Okabe-Ito categorical palette (colour-blind safe)
BLUE, VERMILLION, TEAL, PURPLE, ORANGE, SKY = "#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9"
TEMP, PRECIP = VERMILLION, BLUE

# Diverging scale for correlations: blue (negative) - light grey - vermillion (positive)
DIVERGING = [[0.0, BLUE], [0.5, "#F1F4F8"], [1.0, VERMILLION]]

# Risk bands: display labels on the 0-100 relative scores (a presentation layer, not a new calculation)
_band_colors = sample_colorscale("Cividis", [0.05, 0.3, 0.55, 0.78, 0.98])
BANDS = [  # (lower bound, label, level 1-5, map marker symbol, colour)
    (0, "Very low", 1, "circle", _band_colors[0]),
    (20, "Low", 2, "square", _band_colors[1]),
    (40, "Moderate", 3, "diamond", _band_colors[2]),
    (60, "High", 4, "triangle-up", _band_colors[3]),
    (80, "Very high", 5, "star", _band_colors[4]),
]


def band_of(score):
    """Return (label, level, symbol, colour) for a 0-100 score."""
    for lo, label, level, symbol, color in reversed(BANDS):
        if score >= lo:
            return label, level, symbol, color
    return BANDS[0][1:]


FONT = "Inter, 'Source Sans 3', -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"

# ---------------------------------------------------------------- icons (inline SVG, Feather-style line icons)
_ICON_PATHS = {
    "thermometer": '<path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z"/>',
    "droplet": '<path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/>',
    "alert": '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    "layers": '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
    "map": '<polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/><line x1="8" y1="2" x2="8" y2="18"/><line x1="16" y1="6" x2="16" y2="22"/>',
    "activity": '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
    "rain": '<line x1="16" y1="13" x2="16" y2="21"/><line x1="8" y1="13" x2="8" y2="21"/><line x1="12" y1="15" x2="12" y2="23"/><path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"/>',
    "dollar": '<line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
    "users": '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "check": '<polyline points="20 6 9 17 4 12"/>',
}


def icon(name, size=18):
    return (f"<svg width='{size}' height='{size}' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' "
            f"stroke-linecap='round' stroke-linejoin='round' aria-hidden='true' focusable='false'>{_ICON_PATHS[name]}</svg>")


MOUNTAINS = """<svg class='ph-art' viewBox='0 0 640 170' preserveAspectRatio='xMaxYMax slice' aria-hidden='true' focusable='false'>
<polygon points='0,170 90,95 150,130 240,40 300,92 360,60 450,118 520,70 640,128 640,170' fill='#E3EBF5'/>
<polygon points='240,40 262,64 248,60 236,70 224,58' fill='#FFFFFF'/><polygon points='360,60 376,78 362,74 350,82' fill='#FFFFFF'/>
<polygon points='120,170 210,110 280,140 380,78 470,132 560,96 640,140 640,170' fill='#D3DFEE'/>
<polygon points='300,170 400,128 470,150 560,120 640,152 640,170' fill='#C3D3E7'/></svg>"""

# ---------------------------------------------------------------- CSS
CSS = f"""
<style>
:root {{ --navy:{NAVY}; --primary:{PRIMARY}; --border:{BORDER}; --head:{HEAD}; --body:{BODY}; --muted:{MUTED}; }}
html, body, [class*="css"] {{ font-family: {FONT}; }}
[data-testid="stMainBlockContainer"] {{ max-width: 1360px; padding: 1.4rem 2rem 3rem; }}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stDecoration"] {{ display: none; }}
h1, h2, h3, h4 {{ color: {HEAD}; letter-spacing: -0.01em; }}

/* Keyboard focus: always visible, never colour-only (3px ring + offset) */
a:focus-visible, button:focus-visible, [role="tab"]:focus-visible, [role="radio"]:focus-visible, [role="slider"]:focus-visible,
input:focus-visible, textarea:focus-visible, [tabindex]:focus-visible, summary:focus-visible {{
  outline: 3px solid {PRIMARY} !important; outline-offset: 2px !important; border-radius: 6px; }}
[data-testid="stSidebar"] a:focus-visible, [data-testid="stSidebar"] button:focus-visible, [data-testid="stSidebar"] summary:focus-visible,
[data-testid="stSidebar"] [role="slider"]:focus-visible, [data-testid="stSidebar"] input:focus-visible {{ outline-color: {SKY} !important; }}
.sr-only {{ position:absolute; width:1px; height:1px; padding:0; margin:-1px; overflow:hidden; clip:rect(0,0,0,0); white-space:nowrap; border:0; }}

/* Sidebar navigation */
[data-testid="stSidebarNav"] {{ padding-top: .3rem; }}
[data-testid="stNavSectionHeader"] {{ color: #A9BCD0 !important; font-size: .7rem; font-weight: 600; letter-spacing: .1em; text-transform: uppercase; }}
[data-testid="stNavSectionHeader"] * {{ color: #A9BCD0 !important; }}
[data-testid="stSidebarNavLink"] {{ border-radius: 8px; padding: .38rem .7rem; margin: 1px 0; transition: background-color .15s ease; }}
[data-testid="stSidebarNavLink"] span {{ color: #DCE6F0 !important; }}
[data-testid="stSidebarNavLink"]:hover {{ background-color: {NAV_HOVER} !important; }}
[data-testid="stSidebarNavLink"][aria-current] {{ background-color: {NAV_ACTIVE} !important; box-shadow: inset 4px 0 0 {SKY}; }}
[data-testid="stSidebarNavLink"][aria-current] span {{ color: #FFFFFF !important; font-weight: 700; }}
.sb-label {{ font-size: .7rem; font-weight: 600; letter-spacing: .1em; text-transform: uppercase; color: #A9BCD0; margin: .2rem 0 .25rem; }}
.sb-text {{ font-size: .82rem; color: #C9D6E3; line-height: 1.45; margin-bottom: .6rem; }}

/* Page header */
.ph {{ position: relative; overflow: hidden; background: {CARD}; border: 1px solid {BORDER}; border-radius: 14px;
       padding: 22px 26px 20px; box-shadow: 0 1px 2px rgba(16,24,40,.05); margin-bottom: 14px; min-height: 112px; }}
.ph-art {{ position: absolute; right: 0; bottom: 0; height: 100%; width: 52%; }}
.ph::after {{ content: ""; position: absolute; inset: 0; background: linear-gradient(90deg, #fff 45%, rgba(255,255,255,.55) 75%, rgba(255,255,255,.15)); }}
.ph-text {{ position: relative; z-index: 1; max-width: 760px; }}
.ph-eyebrow {{ font-size: .74rem; font-weight: 600; letter-spacing: .1em; text-transform: uppercase; color: {PRIMARY}; }}
.ph-title {{ font-size: clamp(1.45rem, 1.1rem + 1.4vw, 2rem); font-weight: 700; overflow-wrap: anywhere; color: {HEAD}; line-height: 1.2; margin: 4px 0 6px; letter-spacing: -0.02em; }}
.ph-sub {{ font-size: 1rem; color: {BODY}; line-height: 1.55; margin: 0; }}

/* Cards (keyed Streamlit containers) */
[class*="st-key-card_"] {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 14px; padding: 18px 20px 14px;
                          box-shadow: 0 1px 2px rgba(16,24,40,.05), 0 1px 3px rgba(16,24,40,.04); }}
.card-title {{ font-size: 1.02rem; font-weight: 600; color: {HEAD}; margin: 0; }}
.card-sub {{ font-size: .85rem; color: {MUTED}; margin: 2px 0 6px; line-height: 1.45; }}

/* Filter bar */
[class*="st-key-filterbar"] {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 14px; padding: 12px 18px 4px;
                              box-shadow: 0 1px 2px rgba(16,24,40,.05); }}

/* KPI cards: CSS grid gives 4 / 2 / 1 per row on desktop / tablet / mobile */
.kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 14px; margin: 2px 0 14px; }}
.kpi {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 14px; padding: 16px 18px 14px; box-shadow: 0 1px 2px rgba(16,24,40,.05); }}
.kpi-top {{ display: flex; align-items: center; gap: 10px; }}
.kpi-icon {{ width: 34px; height: 34px; border-radius: 9px; display: flex; align-items: center; justify-content: center; background: #E6F1F8; color: {PRIMARY}; flex-shrink: 0; }}
.kpi-label {{ font-size: .86rem; font-weight: 600; color: {BODY}; }}
.kpi-value {{ font-size: 1.85rem; font-weight: 700; color: {HEAD}; margin-top: 10px; line-height: 1.1; letter-spacing: -0.02em; }}
.kpi-unit {{ font-size: .95rem; font-weight: 500; color: {MUTED}; margin-left: 4px; letter-spacing: 0; }}
.kpi-note {{ font-size: .82rem; color: {MUTED}; margin-top: 5px; line-height: 1.4; }}
.kpi-trend {{ font-size: .82rem; font-weight: 600; margin-top: 6px; color: {BODY}; }}
.kpi-spark {{ margin-top: 8px; display: block; }}

/* Risk badge: text label + 5-step meter (meaning never carried by colour alone) */
.badge {{ display: inline-flex; align-items: center; gap: 8px; font-size: .8rem; font-weight: 600; color: {HEAD};
          background: #F1F5F9; border: 1px solid #CBD5E1; border-radius: 999px; padding: 3px 10px 3px 9px; margin-top: 8px; }}
.meter {{ display: inline-flex; gap: 2px; }}
.meter i {{ width: 6px; height: 12px; border-radius: 2px; background: #CBD5E1; display: inline-block; }}
.meter i.on {{ background: {HEAD}; }}

/* Notes, findings, status chips, tables */
.note {{ background: #F1F6FB; border: 1px solid #CFE0EE; border-radius: 12px; padding: 13px 16px; color: {BODY}; font-size: .92rem; line-height: 1.55; margin: 6px 0 12px; }}
.note-title {{ font-weight: 700; color: {HEAD}; margin-bottom: 2px; display: flex; gap: 6px; align-items: center; }}
.note.warn {{ background: #FFF5EC; border-color: #F2D2B6; }}
.note.warn .note-title {{ color: {WARN}; }}
.finding {{ display: flex; gap: 12px; align-items: baseline; padding: 9px 0; border-top: 1px solid {BORDER}; font-size: .92rem; color: {BODY}; line-height: 1.55; }}
.fcode {{ font-family: "JetBrains Mono", Consolas, monospace; font-size: .72rem; font-weight: 700; color: {NAV_ACTIVE};
          border: 1px solid #9DBAD6; border-radius: 4px; padding: 1px 6px; white-space: nowrap; }}
.chip {{ display: inline-flex; align-items: center; gap: 6px; font-size: .78rem; font-weight: 700; padding: 3px 10px; border-radius: 999px; margin-top: 8px; color: {HEAD}; border: 1px solid; }}
.chip.good {{ background: #E6F1F8; border-color: #9CC6E2; }}
.chip.mid {{ background: #FEF3E2; border-color: #EBC98F; }}
.chip.bad {{ background: #FBEADF; border-color: #E8B193; }}
.tbl {{ width: 100%; border-collapse: collapse; font-size: .88rem; }}
.tbl caption {{ text-align: left; color: {MUTED}; font-size: .82rem; padding-bottom: 6px; }}
.tbl th {{ text-align: left; font-weight: 600; color: {MUTED}; font-size: .74rem; letter-spacing: .06em; text-transform: uppercase;
           border-bottom: 1px solid #CBD5E1; padding: 8px 10px; white-space: nowrap; }}
.tbl td {{ border-bottom: 1px solid {BORDER}; padding: 9px 10px; vertical-align: top; color: {BODY}; line-height: 1.45; }}
.tbl td.num, .tbl th.num {{ text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }}
.tbl td.code {{ font-family: Consolas, monospace; font-size: .8rem; color: {NAV_ACTIVE}; white-space: nowrap; }}
.dl {{ display: grid; grid-template-columns: 96px 1fr; row-gap: 8px; column-gap: 14px; font-size: .92rem; line-height: 1.5; margin: 6px 0 0; }}
.dl dt {{ color: {MUTED}; font-weight: 600; font-size: .76rem; letter-spacing: .06em; text-transform: uppercase; padding-top: 2px; }}
.dl dd {{ margin: 0; color: {BODY}; }}
.legend-row {{ display: flex; flex-wrap: wrap; gap: 6px 16px; font-size: .82rem; color: {BODY}; margin: 4px 0 2px; }}
.footer {{ border-top: 1px solid {BORDER}; margin-top: 2rem; padding-top: .9rem; font-size: .8rem; color: {MUTED}; line-height: 1.6; }}

/* Filter controls wrap instead of shrinking: 4 per row on desktop, 2 on tablet, 1 on phones */
[class*="st-key-filterbar"] [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap; row-gap: .4rem; }}
[class*="st-key-filterbar"] [data-testid="stColumn"] {{ flex: 1 1 190px !important; min-width: 190px; }}
/* Side-by-side panels stack when the content area gets narrow (tablet with sidebar open, or small laptops) */
@media (max-width: 1180px) {{
  [data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap; }}
  [data-testid="stMainBlockContainer"] [data-testid="stColumn"] {{ flex: 1 1 380px !important; min-width: min(100%, 380px); }}
}}
@media (max-width: 900px) {{
  [data-testid="stMainBlockContainer"] {{ padding: 1rem .9rem 2rem; }}
  .ph-art {{ display: none; }} .ph::after {{ display: none; }}
  .ph-title {{ font-size: 1.55rem; }} .kpi-value {{ font-size: 1.6rem; }}
}}
</style>
"""


def _template():
    axis = dict(automargin=True, gridcolor="#EEF2F6", zeroline=False, linecolor="#94A3B8", ticks="outside", tickcolor="#94A3B8", ticklen=4,
                tickfont=dict(color=MUTED, size=12), title=dict(font=dict(color=BODY, size=12.5)))
    return go.layout.Template(layout=dict(
        font=dict(family=FONT, size=13, color=BODY),
        title=dict(font=dict(family=FONT, size=15, color=HEAD), x=0, xanchor="left"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        colorway=[BLUE, VERMILLION, TEAL, PURPLE, ORANGE, SKY],
        xaxis=axis, yaxis={**axis, "showline": False, "ticks": ""},
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#94A3B8", font=dict(family=FONT, color=HEAD, size=12.5)),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, xanchor="left", font=dict(size=12.5, color=BODY), title_text=""),
        margin=dict(l=8, r=16, t=36, b=8), barcornerradius=4, bargap=0.32,
    ))


def setup():
    """Apply page CSS and the default chart template. Call once per run."""
    st.markdown(CSS, unsafe_allow_html=True)
    pio.templates["nepal"] = _template()
    pio.templates.default = "nepal"


def esc(text):
    return html.escape(str(text))


# ---------------------------------------------------------------- components
def page_header(title, subtitle, eyebrow):
    st.markdown(f"<header class='ph'>{MOUNTAINS}<div class='ph-text'><div class='ph-eyebrow'>{esc(eyebrow)}</div>"
                f"<div class='ph-title' role='heading' aria-level='1'>{esc(title)}</div><p class='ph-sub'>{subtitle}</p></div></header>",
                unsafe_allow_html=True)


@contextmanager
def card(key, title=None, subtitle=None):
    """A white dashboard card (a keyed Streamlit container styled in CSS)."""
    with st.container(key=f"card_{key}"):
        if title:
            st.markdown(f"<div class='card-title' role='heading' aria-level='2'>{esc(title)}</div>"
                        + (f"<p class='card-sub'>{subtitle}</p>" if subtitle else ""),
                        unsafe_allow_html=True)
        yield


def sparkline(values, color=PRIMARY, label=""):
    vals = [float(v) for v in values]
    if len(vals) < 2:
        return ""
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1
    w, h = 200, 34
    pts = " ".join(f"{i * w / (len(vals) - 1):.1f},{h - 3 - (v - lo) / span * (h - 6):.1f}" for i, v in enumerate(vals))
    return (f"<svg class='kpi-spark' viewBox='0 0 {w} {h}' width='100%' height='{h}' preserveAspectRatio='none' role='img' "
            f"aria-label='{esc(label)}'><polyline points='{pts}' fill='none' stroke='{color}' stroke-width='2' "
            f"vector-effect='non-scaling-stroke' stroke-linejoin='round'/></svg>")


def risk_badge(score):
    label, level, _, _ = band_of(score)
    bars = "".join(f"<i class='{'on' if i < level else ''}'></i>" for i in range(5))
    return f"<span class='badge'><span class='meter' aria-hidden='true'>{bars}</span>{label}<span class='sr-only'> risk, level {level} of 5</span></span>"


def kpi_grid(items):
    """items: dicts with icon, label, value, optional unit, note, trend, spark (list), spark_label, badge (html)."""
    cards = []
    for it in items:
        cards.append(
            "<div class='kpi'><div class='kpi-top'>"
            f"<span class='kpi-icon'>{icon(it.get('icon', 'activity'))}</span><span class='kpi-label'>{esc(it['label'])}</span></div>"
            f"<div class='kpi-value'>{esc(it['value'])}" + (f"<span class='kpi-unit'>{esc(it['unit'])}</span>" if it.get("unit") else "") + "</div>"
            + (f"<div class='kpi-trend'>{it['trend']}</div>" if it.get("trend") else "")
            + (f"<div class='kpi-note'>{it['note']}</div>" if it.get("note") else "")
            + (it.get("badge") or "")
            + (sparkline(it["spark"], it.get("spark_color", PRIMARY), it.get("spark_label", "")) if it.get("spark") is not None else "")
            + "</div>")
    st.markdown(f"<section class='kpi-grid' aria-label='Key indicators'>{''.join(cards)}</section>", unsafe_allow_html=True)


def note(body, title=None, warn=False):
    sym = "⚠" if warn else "ⓘ"
    st.markdown(f"<div class='note{' warn' if warn else ''}' role='note'>"
                + (f"<div class='note-title'><span aria-hidden='true'>{sym}</span>{esc(title)}</div>" if title else "")
                + f"{body}</div>", unsafe_allow_html=True)


def findings(rows):
    st.markdown("".join(f"<div class='finding'><span class='fcode'>{esc(c)}</span><span>{t}</span></div>" for c, t in rows),
                unsafe_allow_html=True)


STATUS = {"good": ("good", "✓"), "mid": ("mid", "◐"), "bad": ("bad", "✕")}


def status_chip(kind, text):
    cls, sym = STATUS[kind]
    return f"<span class='chip {cls}'><span aria-hidden='true'>{sym}</span>{esc(text)}</span>"


def band_legend():
    items = "".join(f"<span>{_symbol_glyph(sym)} {label} ({lo}–{lo + 20 if lo < 80 else 100})</span>"
                    for lo, label, _, sym, _ in BANDS)
    st.markdown(f"<div class='legend-row' aria-label='Risk band legend'>{items}</div>", unsafe_allow_html=True)


def _symbol_glyph(symbol):
    return {"circle": "●", "square": "■", "diamond": "◆", "triangle-up": "▲", "star": "★"}[symbol]


def table(df, num=(), code=(), caption=None):
    """A wrapping HTML table for short reference tables (data tables use st.dataframe for search/sort)."""
    def cls(c):
        return " class='num'" if c in num else " class='code'" if c in code else ""
    head = "".join(f"<th scope='col'{' class=num' if c in num else ''}>{esc(c)}</th>" for c in df.columns)
    rows = "".join("<tr>" + "".join(f"<td{cls(c)}>{esc(v)}</td>" for c, v in r.items()) + "</tr>" for _, r in df.iterrows())
    cap = f"<caption>{esc(caption)}</caption>" if caption else ""
    st.markdown(f"<table class='tbl'>{cap}<thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>", unsafe_allow_html=True)


def chart(fig, height=None, key=None, on_select="ignore", selection_mode=("points",)):
    if height:
        fig.update_layout(height=height)
    fig.update_layout(paper_bgcolor=CARD, plot_bgcolor=CARD)  # Streamlit otherwise injects the page background
    # theme=None: use our own template instead of Streamlit's chart theme
    return st.plotly_chart(fig, width="stretch", theme=None, key=key, on_select=on_select, selection_mode=selection_mode,
                           config={"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"], "responsive": True})


def footer():
    st.markdown("<footer class='footer'>Data: NASA POWER · HydroSHEDS · Nepal National Statistics Office (Census 2021) · "
                "OpenStreetMap · Wikipedia (hydropower) · geoBoundaries · BIPAD Portal, Government of Nepal. "
                "Scores are relative (0 = lowest district, 100 = highest) and describe structural risk; they are not forecasts.</footer>",
                unsafe_allow_html=True)
