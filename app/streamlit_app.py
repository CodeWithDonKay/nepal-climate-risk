"""Nepal Climate Risk Atlas: Streamlit app (capstone deliverable, Option A).

Run from the project folder:   streamlit run app/streamlit_app.py
Design tokens, styling and chart template live in ui.py; the scoring engine in risk_model.py.
"""
import json
import os

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import risk_model as rm
import ui
from ui import ACCENT, CONTEXT, DATA, MUTED

APP_DIR = os.path.dirname(os.path.abspath(__file__))
st.set_page_config(page_title="Nepal Risk Atlas", page_icon=":material/landscape:", layout="wide")
ui.setup()
st.logo(os.path.join(APP_DIR, "assets", "logo.svg"), size="large")

CORRIDOR = ["SINDHUPALCHOK", "RASUWA", "NUWAKOT"]
INDEX = {  # label, map ramp, emphasis colour for bars
    "risk_landslide": ("Landslide risk", ui.RAMP_LANDSLIDE, ui.RAMP_LANDSLIDE[4]),
    "risk_flood": ("Flood risk", ui.RAMP_FLOOD, ui.RAMP_FLOOD[4]),
    "risk_combined": ("Combined risk", ui.RAMP_RISK, ui.RAMP_RISK[4]),
}


# ---------------------------------------------------------------- data
@st.cache_data
def load():
    df = rm.load_inputs()
    with open(os.path.join(rm.OUT, "deck_data.json")) as f:
        deck = json.load(f)
    events = pd.read_csv(os.path.join(rm.OUT, "clean", "disaster_events_clean.csv"), parse_dates=["incident_date"])
    return df, deck, events


@st.cache_data
def scores(expo_w_items, rain_share, access_share, method):
    df, _, _ = load()
    return rm.compute(df, dict(expo_w_items), rain_share, access_share, method)


df, deck, events = load()

# ---------------------------------------------------------------- sidebar: model settings
DEFAULTS = {"w_pop": 30, "w_den": 20, "w_hyd": 20, "w_hos": 15, "w_sch": 15, "rain_share": 50, "access_share": 50,
            "method": "Geometric mean"}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)


def reset_settings():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v


with st.sidebar:
    st.markdown("<div class='sb-label'>Model settings</div><div class='sb-text'>Defaults reproduce the published analysis. "
                "Adjust them to test how sensitive the rankings are.</div>", unsafe_allow_html=True)
    with st.expander("Exposure weights"):
        st.slider("Population", 0, 100, key="w_pop", format="%d%%")
        st.slider("Population density", 0, 100, key="w_den", format="%d%%")
        st.slider("Hydropower capacity", 0, 100, key="w_hyd", format="%d%%")
        st.slider("Hospitals", 0, 100, key="w_hos", format="%d%%")
        st.slider("Schools", 0, 100, key="w_sch", format="%d%%")
    with st.expander("Hazard and vulnerability mix"):
        st.slider("Heavy-rain share of hazard", 0, 100, key="rain_share", format="%d%%",
                  help="Flood hazard = rain + river score; landslide hazard = rain + terrain score. This sets the rain share.")
        st.slider("Road-access share of vulnerability", 0, 100, key="access_share", format="%d%%",
                  help="The remainder is hospital strain (people per hospital).")
    st.radio("Aggregation", ["Geometric mean", "Weighted sum"], key="method",
             help="Geometric mean: risk is high only where hazard, exposure and vulnerability are all high.")
    st.button("Reset to defaults", on_click=reset_settings, width="stretch")
    changed = any(st.session_state[k] != v for k, v in DEFAULTS.items())
    if changed:
        st.markdown("<div class='note alert' style='font-size:.82rem;padding:10px 12px'><div class='note-title'>Custom settings active</div>"
                    "Reported findings use the default settings.</div>", unsafe_allow_html=True)

expo_w = {"population": st.session_state.w_pop, "population_density_per_km2": st.session_state.w_den,
          "hydropower_capacity_mw": st.session_state.w_hyd, "hospital_count": st.session_state.w_hos,
          "school_count": st.session_state.w_sch}
if sum(expo_w.values()) == 0:
    expo_w = rm.DEFAULT_EXPO_W
METHOD = "additive" if st.session_state.method == "Weighted sum" else "geometric"
S = scores(tuple(expo_w.items()), st.session_state.rain_share / 100, st.session_state.access_share / 100, METHOD)
D = df.join(S)
for c in INDEX:
    D[c + "_rank"] = D[c].rank(ascending=False).astype(int)
D["District"] = D.index.str.title()


# ---------------------------------------------------------------- chart helpers
def nepal_map(color_col, label, ramp, highlight=None, height=480, zoom=5.25, fmt=":.0f"):
    m = D.reset_index()
    m["size"] = np.where(m.district_name.isin(highlight), 17, 10) if highlight is not None else 10
    fig = px.scatter_map(m, lat="latitude", lon="longitude", color=color_col, size="size", size_max=17,
                         hover_name="District", color_continuous_scale=ramp, zoom=zoom,
                         center={"lat": 28.3, "lon": 84.1}, map_style="carto-positron", opacity=0.92,
                         hover_data={color_col: fmt, "province": True, "size": False, "latitude": False, "longitude": False},
                         labels={color_col: label, "province": "Province"})
    # Horizontal colour key inside the map's top-left corner, so the map uses the full column width
    fig.update_layout(height=height, margin=dict(l=0, r=0, t=0, b=0),
                      coloraxis_colorbar=dict(orientation="h", x=0.02, xanchor="left", y=0.98, yanchor="top", len=0.32,
                                              thickness=8, title=dict(text=label, side="top", font=dict(size=11, color=ui.INK_2)),
                                              bgcolor="rgba(255,255,255,0.85)", tickfont=dict(size=10)))
    return fig


def bar_top(series, color, n=10, fmt=".0f", highlight=None):
    s = series.sort_values(ascending=False).head(n)[::-1]
    colors = [ACCENT if highlight is not None and i in highlight else color for i in s.index]
    fig = go.Figure(go.Bar(x=s.values, y=[i.title() for i in s.index], orientation="h", marker_color=colors,
                           text=[format(v, fmt) for v in s.values], textposition="outside", textfont=dict(color=ui.INK_2),
                           hovertemplate="%{y}: %{x:.1f}<extra></extra>"))
    fig.update_layout(height=34 * n + 40, margin=dict(l=8, r=24, t=8, b=8), xaxis=dict(visible=False, range=[0, s.max() * 1.15]),
                      yaxis=dict(tickfont=dict(color=ui.INK, size=12.5)))
    return fig


# ================================================================= pages
def page_intro():
    ui.page_header("Overview", "Where Nepal's climate risk lives",
                   "A district-level assessment of climate-disaster risk across Nepal's 77 districts, tested against 15 years "
                   "of recorded disasters and translated into a USD 100 million resilience investment plan.")
    c1, c2 = st.columns([1, 1.2], gap="large")
    with c1:
        ui.section("The event: 26 August 2026")
        st.markdown("<dl class='dl'><dt>Trigger</dt><dd>Glacier and rock-and-ice collapse at high altitude</dd>"
                    "<dt>Path</dt><dd>Flash flood down the Bhote Koshi and Trishuli river corridor (Sindhupalchok, Rasuwa, Nuwakot)</dd>"
                    "<dt>Impact</dt><dd>Significant loss of life, displacement, and damage to hydropower plants</dd></dl>",
                    unsafe_allow_html=True)
        ui.section("The question")
        ui.note("How do climate hazards, terrain, population, infrastructure and access interact to create risk across "
                "Nepal's 77 districts, and where has that risk actually materialised?")
        ui.section("How risk is measured", "Risk is high only where all three factors coincide.")
        cols = st.columns(3)
        for col, (name, desc, color) in zip(cols, [
                ("Hazard", "Heavy rain, steep terrain, large rivers", ACCENT),
                ("Exposure", "People, hospitals, schools, hydropower", DATA),
                ("Vulnerability", "Sparse roads, overstretched hospitals", ui.NAVY)]):
            col.markdown(f"<div class='factor' style='--c:{color}'><div class='factor-name'>{name}</div>"
                         f"<div class='factor-desc'>{desc}</div></div>", unsafe_allow_html=True)
    with c2:
        ui.section("Landslide risk by district", "Larger markers: the 26 August corridor. Hover for details.")
        ui.chart(nepal_map("risk_landslide", "Landslide risk", ui.RAMP_LANDSLIDE, highlight=CORRIDOR, zoom=5.0, height=430))
    ui.section("Reading this atlas")
    st.markdown("<p class='sec-cap' style='max-width:900px'>Pages follow the assessment in order: the climate record, terrain and "
                "exposure, the risk index, scenario testing, validation against recorded disasters, and the investment plan. "
                "Model settings in the sidebar let you test how sensitive the rankings are to each assumption.</p>",
                unsafe_allow_html=True)


def page_climate():
    ui.page_header("Evidence · Climate", "Rainfall is rising, and extremes with it",
                   "NASA POWER satellite record, 2004–2025. Earlier years are excluded because of a data-source change in 2004; "
                   "2026 is excluded from annual totals because the record ends on 30 August.")
    ui.kpis([
        {"label": "Rainfall trend", "value": f"+{deck['rain_slope']} mm/yr", "note": "2004–2025, p < 0.001"},
        {"label": "Recent vs baseline", "value": f"+{deck['anomaly_median']:.0f}%", "note": f"Normal year-to-year swing ±{deck['cv_median']:.0f}%"},
        {"label": "Series meaningfully wetter", "value": f"{deck['meaningful_n']} of 45", "note": "None meaningfully drier"},
        {"label": "Extreme-rain days per year", "value": f"{deck['ext_base']} → {deck['ext_recent']}", "note": f"+{deck['ext_pct']}% (p = 0.05)"},
    ])
    c1, c2 = st.columns(2, gap="large")
    with c1:
        ui.section("Average annual rainfall", "45 independent satellite series, mm per year")
        fig = go.Figure()
        fig.add_scatter(x=deck["rain_years"], y=deck["rain_mm"], mode="lines+markers", name="Annual rainfall",
                        line=dict(color=DATA, width=2), marker=dict(size=7, color=DATA, line=dict(color="white", width=1.5)),
                        hovertemplate="%{x}: %{y:,.0f} mm<extra></extra>")
        fig.add_scatter(x=deck["rain_years"], y=deck["rain_trend"], mode="lines", name=f"Trend (+{deck['rain_slope']} mm/yr)",
                        line=dict(color=ACCENT, dash="dash", width=2), hoverinfo="skip")
        fig.update_layout(height=340, margin=dict(t=30), yaxis=dict(tickformat=","))
        ui.chart(fig)
    with c2:
        ui.section("Extreme-rain days per district", "Days in the heaviest 5% of rainy days; recent period highlighted")
        yrs = deck["ext_years"]
        fig = go.Figure(go.Bar(x=yrs, y=deck["ext_days"], marker_color=[DATA if y >= 2020 else CONTEXT for y in yrs],
                               hovertemplate="%{x}: %{y:.1f} days<extra></extra>"))
        fig.update_layout(height=340, margin=dict(t=30))
        ui.chart(fig)
    ui.findings([
        ("F1", f"Rainfall is rising by about <b>{deck['rain_slope']} mm a year</b>; 2020–25 was about {deck['anomaly_median']:.0f}% wetter than 2004–19."),
        ("F2", f"Extreme-rain days rose from <b>{deck['ext_base']} to {deck['ext_recent']}</b> per district per year (+{deck['ext_pct']}%), a borderline-significant trend."),
    ])
    ui.note(f"About 20 mm fell in the corridor on 26 August, below the {deck['nat_p95']} mm national extreme threshold. "
            "The trigger was ice, not rain: rainfall monitoring alone would not have flagged it.",
            title="F3 · 26 August 2026 was an ordinary rain day", alert=True)
    ui.section("District view")
    layer = st.segmented_control("Measure", ["Anomaly (%)", "Trend (mm/yr)", "Extreme threshold (mm)"], default="Anomaly (%)",
                                 label_visibility="collapsed") or "Anomaly (%)"
    col = {"Anomaly (%)": "anomaly_pct", "Trend (mm/yr)": "trend_mm_per_yr", "Extreme threshold (mm)": "p95_threshold_mm"}[layer]
    ui.chart(nepal_map(col, layer, ui.RAMP_NEUTRAL, height=440))
    st.caption("Only 45 of 77 districts have independent rainfall data; neighbours sharing one satellite cell show identical values.")


def page_terrain():
    ui.page_header("Evidence · Terrain and exposure", "Physical hazard and what lies in its path",
                   "Terrain ruggedness from HydroSHEDS elevation, river hazard from flow accumulation and distance to channels, "
                   "and exposure from the 2021 Census, OpenStreetMap and hydropower records.")
    t1, t2 = st.tabs(["Terrain and rivers", "Exposure and vulnerability"])
    with t1:
        c1, c2 = st.columns([1.5, 1], gap="large")
        with c1:
            ui.section("Ruggedness against river hazard", "Each point is a district; highlighted points are in the top third on both")
            m = D.reset_index()
            hot = m[m.steep_and_river]
            fig = go.Figure()
            fig.add_scatter(x=m.ruggedness_score, y=m.river_score, mode="markers", name="Other districts", text=m.District,
                            marker=dict(size=10, color=CONTEXT, line=dict(color="white", width=1.5)),
                            hovertemplate="%{text}<br>Ruggedness %{x:.0f} · River %{y:.0f}<extra></extra>")
            fig.add_scatter(x=hot.ruggedness_score, y=hot.river_score, mode="markers", name="Steep and on major rivers",
                            text=hot.District, marker=dict(size=12, color=ACCENT, line=dict(color="white", width=1.5)),
                            hovertemplate="%{text}<br>Ruggedness %{x:.0f} · River %{y:.0f}<extra></extra>")
            fig.update_layout(height=440, margin=dict(t=30), xaxis_title="Terrain ruggedness (0–100)", yaxis_title="River size × proximity (0–100)")
            ui.chart(fig)
        with c2:
            ui.section("Why the combination matters")
            st.markdown("<p class='sec-cap' style='color:#4B5A68;font-size:.92rem'>Landslides can dam rivers and release floods "
                        "downstream; ice collapses travel down steep valleys through river corridors. Steep terrain beside large "
                        "rivers produces cascading hazards.</p>", unsafe_allow_html=True)
            ui.findings([("F4", "Eight districts are in the top third for both ruggedness and river hazard: <b>"
                          + ", ".join(deck["scatter"]["hot_names"]) + "</b>.")])
            st.caption("Ruggedness = spread of elevation within the district. The supplied slope columns are corrupted "
                       "(saturated near 90°) and are not used.")
    with t2:
        c1, c2 = st.columns(2, gap="large")
        with c1:
            ui.section("Exposure", "People and critical assets, top 10 (score 0–100)")
            ui.chart(bar_top(D.exposure_score, DATA))
        with c2:
            ui.section("Vulnerability", "Weak road access and hospital strain, top 10 (score 0–100)")
            ui.chart(bar_top(D.vulnerability_score, DATA))
        ui.findings([
            ("F5", "People and assets cluster in Kathmandu Valley, Pokhara (Kaski), the southern plains and hydropower hubs such as Dolakha (587 MW)."),
            ("F6", "Vulnerability peaks in remote mountain districts: very sparse roads and one or two mapped hospitals for more than 100,000 people."),
        ])
        ui.note("Poverty, age structure, disability, housing construction, early-warning coverage, footpaths and accurate rural "
                "facility counts (OpenStreetMap undercounts) are not in the data and are stated as limitations.",
                title="What vulnerability does not capture")


def page_explorer():
    ui.page_header("Risk index · Explorer", "District risk explorer",
                   "Risk is the geometric mean of hazard, exposure and vulnerability, scored 0–100 relative to other districts. "
                   "Flood and landslide risk are kept separate because validation showed they behave differently.")
    idx = st.segmented_control("Index", list(INDEX), format_func=lambda k: INDEX[k][0], default="risk_landslide",
                               label_visibility="collapsed") or "risk_landslide"
    label, ramp, emph = INDEX[idx]
    c1, c2 = st.columns([1.35, 1], gap="large")
    with c1:
        ui.chart(nepal_map(idx, label, ramp, height=500))
    with c2:
        ui.section(f"Highest {label.lower()}", "Top 10 districts (score 0–100)")
        ui.chart(bar_top(D[idx], emph))
    if idx == "risk_flood":
        ui.note("The flood index did not validate against recorded floods (ρ = 0.24). Treat its rankings as low confidence; "
                "see Validation.", title="Low-confidence index", alert=True)

    ui.section("District profile")
    names = sorted(D.District)
    pick = st.selectbox("District", names, index=names.index("Sindhupalchok"))
    r = D.loc[pick.upper()]
    ui.kpis([
        {"label": "Combined risk", "value": f"{r.risk_combined:.0f}", "note": f"Rank {r.risk_combined_rank} of 77"},
        {"label": "Landslide risk", "value": f"{r.risk_landslide:.0f}", "note": f"Rank {r.risk_landslide_rank} of 77"},
        {"label": "Flood risk", "value": f"{r.risk_flood:.0f}", "note": f"Rank {r.risk_flood_rank} of 77"},
        {"label": "Recorded events / deaths", "value": f"{int(r.events_total)} / {int(r.deaths)}", "note": "2011–2026"},
    ])
    comp = pd.DataFrame({
        "Component": ["Heavy rain", "River hazard", "Terrain ruggedness", "Exposure", "Vulnerability"],
        "District": [r.rain_score, r.river_score, r.ruggedness_score, r.exposure_score, r.vulnerability_score],
        "Median": [D.rain_score.median(), D.river_score.median(), D.ruggedness_score.median(),
                   D.exposure_score.median(), D.vulnerability_score.median()]})
    c1, c2 = st.columns([1.2, 1], gap="large")
    with c1:
        ui.section("Components", f"{pick} compared with the national median (0–100)")
        fig = go.Figure()
        fig.add_bar(y=comp.Component, x=comp.District, orientation="h", name=pick, marker_color=DATA,
                    hovertemplate="%{y}: %{x:.0f}<extra></extra>")
        fig.add_bar(y=comp.Component, x=comp.Median, orientation="h", name="National median", marker_color=CONTEXT,
                    hovertemplate="%{y}: %{x:.0f}<extra></extra>")
        fig.update_layout(barmode="group", height=330, margin=dict(t=30), xaxis=dict(range=[0, 100]),
                          yaxis=dict(autorange="reversed", tickfont=dict(color=ui.INK)), bargap=0.3, bargroupgap=0.08)
        ui.chart(fig)
    with c2:
        gap = comp.assign(g=comp.District - comp.Median).sort_values("g", ascending=False)
        ui.section("Reading")
        st.markdown(f"<p style='font-size:.93rem;color:#14202B;line-height:1.6'>Relative to the national median, {pick}'s "
                    f"strongest driver is <b>{gap.Component.iloc[0].lower()}</b>; its weakest is "
                    f"<b>{gap.Component.iloc[-1].lower()}</b>.</p>", unsafe_allow_html=True)
        if pick.upper() in CORRIDOR:
            ui.note("This district lies in the 26 August 2026 corridor. Its rank is moderate because glacial-collapse hazard "
                    "is not represented in the data (F11).")
        ind = pd.DataFrame({"Indicator": ["Population", "Density (per km²)", "Hydropower (MW)", "Hospitals (mapped)",
                                          "Schools (mapped)", "Road density (km/km²)", "Highest point (m)", "Elevation spread (m)"],
                            "Value": [f"{r.population:,.0f}", f"{r.population_density_per_km2:,.0f}", f"{r.hydropower_capacity_mw:,.1f}",
                                      f"{r.hospital_count:.0f}", f"{r.school_count:.0f}", f"{r.road_density_km_per_km2:.2f}",
                                      f"{r.elevation_max_m:,.0f}", f"{r.elevation_std_m:,.0f}"]})
        st.dataframe(ind, hide_index=True, width="stretch")

    with st.expander("All 77 districts"):
        cols = ["District", "province", "risk_combined", "risk_landslide", "risk_flood", "combined_hazard", "exposure_score",
                "vulnerability_score", "events_total", "deaths"]
        table = D[cols].sort_values("risk_combined", ascending=False)
        num = {c: st.column_config.NumberColumn(format="%.0f") for c in cols[2:8]}
        st.dataframe(table, hide_index=True, width="stretch", column_config={
            "province": "Province", "risk_combined": num["risk_combined"], "events_total": "Events", "deaths": "Deaths", **num})
        st.download_button("Download CSV", table.round(2).to_csv(index=False), "district_risk_scores.csv")


PRESETS = {
    "Landslide early-warning targets": lambda: list(D.risk_landslide.sort_values(ascending=False).head(8).index),
    "Ten most vulnerable districts": lambda: list(D.vulnerability_score.sort_values(ascending=False).head(10).index),
    "26 August corridor": lambda: CORRIDOR,
    "Custom selection": lambda: [],
}


def page_scenarios():
    ui.page_header("Risk index · Scenarios", "What would interventions change?",
                   "Select districts, apply interventions, and compare risk before and after. Scores are recalculated on the "
                   "baseline scale so that improvements are not hidden by re-normalisation.")
    c1, c2 = st.columns([1, 1.45], gap="large")
    with c1:
        ui.section("Districts")
        preset = st.selectbox("Preset", list(PRESETS))
        sel_names = st.multiselect("Selected districts", sorted(D.District), default=[n.title() for n in PRESETS[preset]()])
        sel = [n.upper() for n in sel_names]
        ui.section("Interventions")
        cov = st.slider("Early-warning coverage", 0, 100, 80, 5, format="%d%%") / 100
        eff = st.slider("Vulnerability reduction at full coverage", 0, 60, 30, 5, format="%d%%",
                        help="Assumption based on the Global Commission on Adaptation (2019): 24 hours' warning of a hazard "
                             "can cut the ensuing damage by about 30%.") / 100
        road = st.slider("Increase in road density", 0, 100, 0, 10, format="+%d%%") / 100
        hosp = st.slider("Additional hospitals per district", 0, 5, 0)
        idx = st.segmented_control("Index", list(INDEX), format_func=lambda k: INDEX[k][0], default="risk_landslide") or "risk_landslide"
    sc = rm.scenario(df, S, sel, cov, eff, road, hosp, METHOD)
    with c2:
        if not sel:
            ui.note("Select at least one district to run a scenario.")
            return
        cmp = pd.DataFrame({"Before": S.loc[sel, idx], "After": sc.loc[sel, idx]}).sort_values("Before", ascending=False)
        cmp["Change"] = cmp.After - cmp.Before
        new_rank = sc[idx].rank(ascending=False)
        ui.kpis([
            {"label": "Average change", "value": f"{cmp.Change.mean():+.1f} pts", "note": f"{INDEX[idx][0]}, selected districts"},
            {"label": "Still in national top 10", "value": f"{int((new_rank.loc[sel] <= 10).sum())} of {len(sel)}",
             "note": f"Before: {int((S[idx].rank(ascending=False).loc[sel] <= 10).sum())} of {len(sel)}"},
        ])
        ui.section(f"{INDEX[idx][0]}: before and after")
        fig = go.Figure()
        ys = [i.title() for i in cmp.index]
        fig.add_bar(y=ys, x=cmp.Before, orientation="h", name="Before", marker_color=CONTEXT, hovertemplate="%{y}: %{x:.1f}<extra></extra>")
        fig.add_bar(y=ys, x=cmp.After, orientation="h", name="After", marker_color=DATA, hovertemplate="%{y}: %{x:.1f}<extra></extra>")
        fig.update_layout(barmode="group", height=max(320, 44 * len(cmp) + 70), margin=dict(t=30),
                          yaxis=dict(autorange="reversed", tickfont=dict(color=ui.INK)), xaxis=dict(range=[0, 100]), bargroupgap=0.08)
        ui.chart(fig)
    with st.expander("Method and assumptions"):
        st.markdown(
            "- **Early warning** reduces a district's vulnerability score by *coverage × effectiveness* (default 80% × 30% = 24%).\n"
            "- **Roads** raise road density, lowering the access-vulnerability score; **hospitals** lower people per hospital.\n"
            "- Hazard and exposure do not change: early warning saves lives but does not stop the landslide.\n"
            "- Because risk is a geometric mean, a 24% cut in vulnerability lowers risk by about 9% (the cube root of 0.76).\n"
            "- Illustrative assumptions, not engineering estimates.")


def page_validation():
    ui.page_header("Risk index · Validation", f"Tested against {deck_events:,} recorded disasters",
                   "District scores are compared with BIPAD records of events and deaths, 2011–2026, after removing duplicate "
                   "records. Spearman rank correlation (ρ): 0 = no relationship, 0.3 weak, 0.5 moderate, 0.7 and above strong.")
    if changed:
        ui.note("Correlations below reflect custom model settings. Weights must not be tuned to improve the fit; use this "
                "only to test robustness. Reported results use the defaults.", title="Custom settings active", alert=True)
    cor = rm.correlations(S, df)
    ui.kpis([
        {"label": "Landslide index vs landslides", "value": f"ρ = {cor.loc['risk_landslide', 'landslide_events']:.2f}",
         "note": "Terrain ruggedness is the strongest driver", "status": ("good", "Validated · F8")},
        {"label": "Combined index vs all events", "value": f"ρ = {cor.loc['risk_combined', 'events_total']:.2f}",
         "note": "Driven mainly by its landslide component", "status": ("warn", "Moderate · F7")},
        {"label": "Flood index vs floods", "value": f"ρ = {cor.loc['risk_flood', 'flood_events']:.2f}",
         "note": "Lowland floods are not captured", "status": ("bad", "Not validated · F9")},
    ])
    c1, c2 = st.columns([1.15, 1], gap="large")
    with c1:
        ui.section("Correlation matrix", "Scores (rows) against recorded outcomes (columns)")
        nice = {"risk_combined": "Combined risk", "risk_flood": "Flood risk", "risk_landslide": "Landslide risk",
                "combined_hazard": "Combined hazard", "flood_hazard": "Flood hazard", "landslide_hazard": "Landslide hazard",
                "exposure_score": "Exposure", "vulnerability_score": "Vulnerability"}
        z = cor.rename(index=nice, columns={"events_total": "All events", "flood_events": "Floods",
                                            "landslide_events": "Landslides", "deaths": "Deaths"})
        fig = px.imshow(z, text_auto=".2f", color_continuous_scale=ui.DIVERGING, zmin=-0.7, zmax=0.7, aspect="auto")
        fig.update_traces(xgap=2, ygap=2, hovertemplate="%{y} vs %{x}: ρ = %{z:.2f}<extra></extra>")
        fig.update_layout(height=420, margin=dict(t=8), coloraxis_showscale=False,
                          xaxis=dict(side="top", tickfont=dict(color=ui.INK)), yaxis=dict(tickfont=dict(color=ui.INK)))
        ui.chart(fig)
    with c2:
        ui.section("Why the flood index fails")
        st.markdown(f"<p style='font-size:.93rem;line-height:1.6;color:#14202B'>Most recorded floods are in "
                    f"<b>{', '.join(deck['top_flood_events']['labels'])}</b>: mostly flat southern lowlands. The flood variables "
                    "describe mountain rivers and rainfall; nothing in the data captures floodplain flatness. Floods are also "
                    "recorded more where people and roads are.</p>", unsafe_allow_html=True)
        fc = pd.Series(deck["flood_corr"])
        ui.section("Correlation with recorded floods", "Spearman ρ; blue = negative, crimson = positive")
        fig = go.Figure(go.Bar(x=fc.values, y=fc.index, orientation="h",
                               marker_color=[ui.DIVERGING[0][1] if v < 0 else ui.DIVERGING[2][1] for v in fc.values],
                               text=[f"{v:+.2f}" for v in fc.values], textposition="outside", textfont=dict(color=ui.INK_2),
                               hovertemplate="%{y}: ρ = %{x:+.2f}<extra></extra>"))
        fig.update_layout(height=210, margin=dict(t=8, l=8), xaxis=dict(range=[-0.5, 0.55], zeroline=True, zerolinecolor="#9AA5B1"), yaxis=dict(tickfont=dict(color=ui.INK)))
        ui.chart(fig)
    ui.section("Decision: separate flood and landslide indices")
    st.markdown("<p style='font-size:.93rem;line-height:1.6;max-width:900px;color:#14202B'>Floods and landslides strike different "
                "districts (ρ = −0.13 between their counts). Each hazard-specific index outperforms the combined index on its own "
                "hazard, and a single index would conceal that landslides are predicted well and floods poorly.</p>",
                unsafe_allow_html=True)
    ui.section("Blind spots in the record", "Recorded events per year; 2024 onward highlighted")
    c1, c2 = st.columns([1.3, 1], gap="large")
    with c1:
        yrs = deck["events_years"]
        fig = go.Figure(go.Bar(x=yrs, y=deck["events_n"], marker_color=[DATA if y >= 2024 else CONTEXT for y in yrs],
                               hovertemplate="%{x}: %{y:,} events<extra></extra>"))
        fig.update_layout(height=300, margin=dict(t=8), yaxis=dict(tickformat=","))
        ui.chart(fig)
    with c2:
        late = events[(events.incident_date >= "2026-08-25") & events.district_name.isin(CORRIDOR)]
        cr = deck["corridor_rank"]
        ui.findings([
            ("F10", f"Events roughly quadrupled after 2023 while deaths per event fell from {deck['deaths_per_event'][0]} to "
                    f"{deck['deaths_per_event'][-1]}: more minor incidents are being logged, not more disasters."),
            ("F10", f"The 26 August collapse is missing: only {len(late)} minor corridor events from 25 August, with "
                    f"{int(late.deaths.sum())} deaths recorded."),
            ("F11", f"Glacial hazard is invisible to the data: Sindhupalchok ranks #{cr['Sindhupalchok']} and Rasuwa #{cr['Rasuwa']}."),
        ])


def page_invest():
    ui.page_header("Decision · Investment", "USD 100 million, allocated by evidence",
                   "Every line traces to a named finding. Where validation is strong, funds go to targeted protection; where the "
                   "analysis revealed blind spots, funds go to monitoring and data.")
    al = pd.DataFrame(deck["alloc"])
    al["Line"] = al.line.str.replace(r"^\S+\s", "", regex=True)
    act = int(al[al.line.str.split().str[0].isin(["1a", "1b", "3", "4"])].usd.sum())
    ui.kpis([
        {"label": "Targeted protection", "value": f"${act}M", "note": "Early warning, infrastructure, community preparedness"},
        {"label": "Closing blind spots", "value": f"${100 - act}M", "note": "Glacial and terrain monitoring, disaster and flood data"},
        {"label": "Districts targeted", "value": f"{len({t.strip() for row in al.targets for t in row.split(',')})}",
         "note": "Selected by explicit rules from the index"},
    ])
    c1, c2 = st.columns([1, 1.25], gap="large")
    with c1:
        ui.section("Allocation", "USD million")
        s = al.sort_values("usd")
        fig = go.Figure(go.Bar(x=s.usd, y=s.Line, orientation="h", marker_color=DATA, text=[f"${v}M" for v in s.usd],
                               textposition="outside", textfont=dict(color=ui.INK_2), hovertemplate="%{y}: $%{x}M<extra></extra>"))
        fig.update_layout(height=320, margin=dict(t=8, r=40), xaxis=dict(visible=False, range=[0, 29]),
                          yaxis=dict(tickfont=dict(color=ui.INK, size=12.5)))
        ui.chart(fig)
    with c2:
        ui.section("Traceability", "Each line, the findings it rests on, and its target districts")
        ui.table(pd.DataFrame({"Line": al.Line, "USD": [f"${v}M" for v in al.usd], "Findings": al.findings,
                               "Target districts": al.targets}), num=("USD",), code=("Findings",))
    ui.section("Effect of the early-warning lines",
               "Scenario defaults (80% coverage × 30% effectiveness) applied to the early-warning target districts")
    targets = [t.strip().upper() for row in al[al.line.str.startswith(("1a", "1b"))].targets for t in row.split(",")]
    sc = rm.scenario(df, S, targets, 0.8, 0.3, 0, 0, METHOD)
    res = pd.DataFrame({"District": [t.title() for t in targets],
                        "Landslide before": S.loc[targets, "risk_landslide"].values, "Landslide after": sc.loc[targets, "risk_landslide"].values,
                        "Flood before": S.loc[targets, "risk_flood"].values, "Flood after": sc.loc[targets, "risk_flood"].values})
    st.dataframe(res, hide_index=True, width="stretch",
                 column_config={c: st.column_config.NumberColumn(format="%.1f") for c in res.columns[1:]})
    with st.expander("Rationale for each amount"):
        st.markdown(
            "| Line | USD M | Rationale |\n|---|---|---|\n"
            "| Terrain and glacial monitoring | 22 | The 26 August disaster was a glacial collapse (F3) missed by the index and the record (F10, F11); ruggedness is the strongest predictor (F8) |\n"
            "| Infrastructure reinforcement | 20 | Concentrated exposure (F5), including the hydropower damaged on 26 August |\n"
            "| Landslide early warning | 18 | Best-validated finding (F8); extreme rainfall is rising (F1, F2) |\n"
            "| Community preparedness | 15 | Remote districts where outside help arrives slowest (F6) |\n"
            "| Data infrastructure | 15 | Flood index failure (F9), reporting surge and missing event (F10), only 45 independent rainfall series |\n"
            "| Flood early warning | 10 | Floods concentrate in the Terai (F9), but the index cannot rank them, so funds go only to proven hotspots |")


def page_method():
    ui.page_header("Reference", "Method, assumptions and sources",
                   "The full analysis, including every data-cleaning step, is documented in the project notebook.")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        ui.section("Key assumptions")
        st.markdown(
            "1. Climate trends use 2004–2025 only (data-source break before 2004; 2026 incomplete)\n"
            "2. 45 independent rainfall series, each counted once in national statistics\n"
            "3. Extreme day: above the district's 95th percentile of rainy days (≥ 1 mm)\n"
            "4. Baseline 2004–19 vs recent 2020–25; meaningful if larger than normal year-to-year variation\n"
            "5. Terrain ruggedness: elevation standard deviation (slope data corrupted)\n"
            "6. River hazard: geometric mean of river size (log) and proximity to rivers\n"
            "7. Skewed variables log-scaled, then min-max scaled to 0–100\n"
            "8. Exposure weights 30/20/20/15/15 (population, density, hydropower, hospitals, schools)\n"
            "9. Vulnerability: equal mix of road access and people per hospital\n"
            "10. Risk: geometric mean of hazard, exposure and vulnerability (components floored at 1)\n"
            "11. Disaster records: 177 duplicates removed; timestamps converted from UTC to Nepal time")
        ui.section("Limitations")
        st.markdown("- No poverty, age, housing or early-warning coverage data\n- OpenStreetMap undercounts rural facilities and roads\n"
                    "- One rainfall point per district on a coarse satellite grid\n- No floodplain or glacial-lake variables\n"
                    "- Disaster record: reporting surge after 2023; the 26 August 2026 event is missing\n"
                    "- Correlation shows association, not causation")
    with c2:
        ui.section("Data sources")
        st.markdown(
            "- **NASA POWER** (power.larc.nasa.gov): daily rainfall (PRECTOTCORR), temperature, humidity, wind\n"
            "- **HydroSHEDS**: elevation (15 arc-second DEM) and flow accumulation\n"
            "- **Nepal National Statistics Office**, Census 2021: population and density\n"
            "- **OpenStreetMap** (Overpass API): hospitals, schools, roads, bridges\n"
            "- **Wikipedia**, List of power stations in Nepal (9 March 2026): hydropower capacity\n"
            "- **geoBoundaries ADM2**: district boundaries, area and representative points\n"
            "- **BIPAD Portal**, Government of Nepal: disaster incidents 2011–2026")
        ui.section("Glossary")
        st.markdown("- **Percentile (P95):** the value 95% of observations fall below\n"
                    "- **p-value:** the chance of a result this strong if no real effect existed\n"
                    "- **Spearman ρ:** rank correlation, from −1 to +1\n"
                    "- **Geometric mean:** multiply, then take the root; low if any component is low\n"
                    "- **Min-max scaling:** rescales to 0–100 (lowest district = 0)")


deck_events = len(events)
pg = st.navigation({
    "Overview": [st.Page(page_intro, title="The question", icon=":material/flag:", default=True)],
    "Evidence": [st.Page(page_climate, title="Climate", icon=":material/rainy:", url_path="climate"),
                 st.Page(page_terrain, title="Terrain and exposure", icon=":material/landscape:", url_path="terrain")],
    "Risk index": [st.Page(page_explorer, title="Explorer", icon=":material/map:", url_path="explorer"),
                   st.Page(page_scenarios, title="Scenarios", icon=":material/tune:", url_path="scenarios"),
                   st.Page(page_validation, title="Validation", icon=":material/fact_check:", url_path="validation")],
    "Decision": [st.Page(page_invest, title="Investment", icon=":material/payments:", url_path="investment")],
    "Reference": [st.Page(page_method, title="Method and sources", icon=":material/menu_book:", url_path="method")],
})
pg.run()
ui.footer()
