"""Design system for the app: colour tokens, page styling, the shared chart template and small UI components.

Colour roles (data colours validated for colour-blind safety with a palette checker):
  DATA    steel indigo  - the default colour for any single data series
  ACCENT  crimson       - highlights only (the district or group the reader should look at)
  CONTEXT light grey    - everything else, so the highlight stands out
Maps use one-hue sequential ramps: crimson = combined risk, blue = flood, brown = landslide.
"""
import html

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# Ink, surfaces, interface
INK, INK_2, MUTED = "#14202B", "#4B5A68", "#76838F"
BORDER, PANEL, GRID = "#DDE2E7", "#F5F7F9", "#ECEFF2"
NAVY = "#1F3A5F"

# Data colours
DATA, ACCENT, CONTEXT = "#3B5BA9", "#B8243B", "#C9D1D9"
STATUS = {"good": ("#1F7A4D", "#E5F1EA"), "warn": ("#8A5A00", "#F8EEDB"), "bad": ("#B8243B", "#F8E6E9")}

# Sequential ramps, light -> dark
RAMP_RISK = ["#FBEFF1", "#F2C4CC", "#E28797", "#C94A61", "#A51F3A", "#6A0F22"]
RAMP_FLOOD = ["#EEF4FA", "#C6DBEF", "#8DB8DE", "#4F8DC4", "#2462A3", "#133F73"]
RAMP_LANDSLIDE = ["#F7F1EA", "#E7D3BC", "#CFAA82", "#B07E4C", "#865628", "#553515"]
RAMP_NEUTRAL = ["#EEF2F8", "#C9D5EA", "#97AED6", "#6684BF", "#3B5BA9", "#243C77"]
DIVERGING = [[0.0, "#2462A3"], [0.5, "#F1F3F5"], [1.0, "#A51F3A"]]

FONT = "IBM Plex Sans, -apple-system, Segoe UI, Helvetica, Arial, sans-serif"

CSS = f"""
<style>
[data-testid="stMainBlockContainer"], .block-container {{ max-width: 1280px; padding-top: 2.4rem; padding-bottom: 4rem; }}
[data-testid="stDecoration"] {{ display: none; }}
h1, h2, h3 {{ letter-spacing: -0.01em; }}

.pg-eyebrow {{ font-size: .74rem; font-weight: 600; letter-spacing: .09em; text-transform: uppercase; color: {MUTED}; }}
.pg-title {{ font-size: 2.05rem; font-weight: 600; color: {INK}; line-height: 1.2; margin: .25rem 0 .5rem; letter-spacing: -0.015em; }}
.pg-lede {{ font-size: 1.02rem; color: {INK_2}; max-width: 820px; line-height: 1.6; margin: 0; }}
.pg-rule {{ border-bottom: 1px solid {BORDER}; margin: 1.4rem 0 1.6rem; }}

.sec {{ font-size: 1.02rem; font-weight: 600; color: {INK}; margin: 1.8rem 0 .2rem; }}
.sec-cap {{ font-size: .86rem; color: {MUTED}; margin: 0 0 .7rem; line-height: 1.5; }}

.kpi {{ border: 1px solid {BORDER}; border-radius: 6px; padding: 14px 16px 13px; background: #fff; height: 100%; }}
.kpi-label {{ font-size: .7rem; font-weight: 600; letter-spacing: .07em; text-transform: uppercase; color: {MUTED}; }}
.kpi-value {{ font-size: 1.65rem; font-weight: 600; color: {INK}; margin-top: 6px; line-height: 1.15; }}
.kpi-note {{ font-size: .82rem; color: {INK_2}; margin-top: 4px; line-height: 1.4; }}
.chip {{ display: inline-block; font-size: .68rem; font-weight: 600; letter-spacing: .05em; text-transform: uppercase;
         padding: 2px 7px; border-radius: 3px; margin-top: 8px; }}

.note {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 6px; padding: 14px 18px; color: {INK};
         font-size: .93rem; line-height: 1.6; margin: .4rem 0 1rem; }}
.note-title {{ font-weight: 600; margin-bottom: 3px; }}
.note.alert {{ background: #FBF1F3; border-color: #EDCAD1; }}
.note.alert .note-title {{ color: {ACCENT}; }}

.finding {{ display: flex; gap: 12px; align-items: baseline; padding: 10px 0; border-top: 1px solid {BORDER};
            font-size: .92rem; color: {INK}; line-height: 1.55; }}
.fcode {{ font-family: "IBM Plex Mono", Consolas, monospace; font-size: .72rem; font-weight: 600; color: {NAVY};
          border: 1px solid #C7D1DE; border-radius: 3px; padding: 1px 6px; white-space: nowrap; }}

.factor {{ border-top: 3px solid var(--c); padding-top: 10px; }}
.factor-name {{ font-weight: 600; color: {INK}; font-size: .98rem; }}
.factor-desc {{ color: {INK_2}; font-size: .88rem; line-height: 1.5; margin-top: 2px; }}

.dl {{ display: grid; grid-template-columns: 110px 1fr; row-gap: 8px; column-gap: 14px; font-size: .93rem; line-height: 1.5; }}
.dl dt {{ color: {MUTED}; font-weight: 600; font-size: .78rem; letter-spacing: .05em; text-transform: uppercase; padding-top: 2px; }}
.dl dd {{ margin: 0; color: {INK}; }}

.tbl {{ width: 100%; border-collapse: collapse; font-size: .87rem; }}
.tbl th {{ text-align: left; font-weight: 600; color: {MUTED}; font-size: .7rem; letter-spacing: .07em; text-transform: uppercase;
           border-bottom: 1px solid {BORDER}; padding: 8px 10px; white-space: nowrap; }}
.tbl td {{ border-bottom: 1px solid {GRID}; padding: 9px 10px; vertical-align: top; color: {INK}; line-height: 1.45; }}
.tbl td.num, .tbl th.num {{ text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }}
.tbl td.code {{ font-family: "IBM Plex Mono", Consolas, monospace; font-size: .78rem; color: {NAVY}; white-space: nowrap; }}

.sb-label {{ font-size: .7rem; font-weight: 600; letter-spacing: .09em; text-transform: uppercase; color: {MUTED}; margin: .4rem 0 .2rem; }}
.sb-text {{ font-size: .82rem; color: {INK_2}; line-height: 1.45; margin-bottom: .6rem; }}
.footer {{ border-top: 1px solid {BORDER}; margin-top: 3rem; padding-top: .9rem; font-size: .78rem; color: {MUTED}; line-height: 1.6; }}
</style>
"""


def _template():
    axis = dict(gridcolor=GRID, zeroline=False, linecolor="#C5CDD5", ticks="", tickfont=dict(color=MUTED, size=11.5),
                title=dict(font=dict(color=INK_2, size=12)))
    return go.layout.Template(layout=dict(
        font=dict(family=FONT, size=12.5, color=INK_2),
        title=dict(font=dict(family=FONT, size=14, color=INK), x=0, xanchor="left", y=0.97, yanchor="top"),
        paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", colorway=[DATA, ACCENT, CONTEXT],
        xaxis=axis, yaxis={**axis, "showline": False},
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=BORDER, font=dict(family=FONT, color=INK, size=12)),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, xanchor="left", font=dict(size=12, color=INK_2), title_text=""),
        margin=dict(l=8, r=16, t=56, b=8), barcornerradius=3, bargap=0.35,
        coloraxis=dict(colorbar=dict(thickness=10, outlinewidth=0, len=0.75, tickfont=dict(size=11, color=MUTED))),
    ))


def setup():
    """Call once at the top of the app: page styling + default chart template."""
    st.markdown(CSS, unsafe_allow_html=True)
    pio.templates["atlas"] = _template()
    pio.templates.default = "atlas"


def esc(text):
    return html.escape(str(text))


def page_header(eyebrow, title, lede=None):
    st.markdown(f"<div class='pg-eyebrow'>{esc(eyebrow)}</div><div class='pg-title'>{esc(title)}</div>"
                + (f"<p class='pg-lede'>{lede}</p>" if lede else "") + "<div class='pg-rule'></div>", unsafe_allow_html=True)


def section(title, caption=None):
    st.markdown(f"<div class='sec'>{esc(title)}</div>" + (f"<p class='sec-cap'>{caption}</p>" if caption else ""),
                unsafe_allow_html=True)


def kpis(items):
    """items: list of dicts with label, value, optional note and optional status=(tone, text)."""
    for col, it in zip(st.columns(len(items)), items):
        chip = ""
        if it.get("status"):
            tone, label = it["status"]
            fg, bg = STATUS[tone]
            chip = f"<div class='chip' style='color:{fg};background:{bg}'>{esc(label)}</div>"
        col.markdown(f"<div class='kpi'><div class='kpi-label'>{esc(it['label'])}</div><div class='kpi-value'>{esc(it['value'])}</div>"
                     + (f"<div class='kpi-note'>{it['note']}</div>" if it.get("note") else "") + chip + "</div>",
                     unsafe_allow_html=True)


def note(body, title=None, alert=False):
    st.markdown(f"<div class='note{' alert' if alert else ''}'>" + (f"<div class='note-title'>{esc(title)}</div>" if title else "")
                + f"{body}</div>", unsafe_allow_html=True)


def findings(rows):
    """rows: list of (code, html_text)."""
    st.markdown("".join(f"<div class='finding'><span class='fcode'>{esc(c)}</span><span>{t}</span></div>" for c, t in rows),
                unsafe_allow_html=True)


def table(df, num=(), code=()):
    """A plain, wrapping HTML table (better than a data grid for short reference tables with long text)."""
    def cls(c):
        return " class='num'" if c in num else " class='code'" if c in code else ""
    head = "".join(f"<th{' class=num' if c in num else ''}>{esc(c)}</th>" for c in df.columns)
    rows = "".join("<tr>" + "".join(f"<td{cls(c)}>{esc(v)}</td>" for c, v in r.items()) + "</tr>" for _, r in df.iterrows())
    st.markdown(f"<table class='tbl'><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>", unsafe_allow_html=True)


def footer():
    st.markdown("<div class='footer'>Data: NASA POWER · HydroSHEDS · Nepal National Statistics Office (Census 2021) · "
                "OpenStreetMap · BIPAD Portal, Government of Nepal. Scores are relative (0 = lowest district, 100 = highest) "
                "and describe structural risk, not predictions of individual events.</div>", unsafe_allow_html=True)


def chart(fig, height=None):
    if height:
        fig.update_layout(height=height)
    st.plotly_chart(fig, width="stretch", config={"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]})
