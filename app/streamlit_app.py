"""Nepal Climate Risk Explorer: Streamlit app (capstone deliverable, Option A).

Run from the project folder:   streamlit run app/streamlit_app.py
"""
import json
import os

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import risk_model as rm

st.set_page_config(page_title="Nepal Climate Risk Explorer", page_icon="🏔️", layout="wide")

TERRA, TEAL, SAFFRON, SLATE, NAVY, ICE, GREY = "#C8553D", "#2A7F8E", "#E0A030", "#6B8496", "#14324A", "#EAF0F3", "#B7C4CC"
RISK_SCALE = ["#EAF0F3", "#E0A030", "#C8553D", "#7A2414"]
CORRIDOR = ["SINDHUPALCHOK", "RASUWA", "NUWAKOT"]
INDEX_LABEL = {"risk_landslide": "Landslide risk", "risk_flood": "Flood risk (low confidence)", "risk_combined": "Combined risk"}


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
DEFAULTS = {"w_pop": 30, "w_den": 20, "w_hyd": 20, "w_hos": 15, "w_sch": 15, "rain_share": 50, "access_share": 50, "method": "Geometric mean (multiply)"}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)


def reset_settings():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v


with st.sidebar:
    st.markdown("### Model settings")
    st.caption("Defaults reproduce the notebook. Change them to test how sensitive the results are.")
    with st.expander("Exposure weights (%)"):
        st.slider("Population", 0, 100, key="w_pop")
        st.slider("Population density", 0, 100, key="w_den")
        st.slider("Hydropower capacity", 0, 100, key="w_hyd")
        st.slider("Hospitals", 0, 100, key="w_hos")
        st.slider("Schools", 0, 100, key="w_sch")
    with st.expander("Hazard and vulnerability mix"):
        st.slider("Heavy-rain share of hazard (%)", 0, 100, key="rain_share",
                  help="Flood hazard = rain + river score; landslide hazard = rain + terrain score. This sets the rain share.")
        st.slider("Road-access share of vulnerability (%)", 0, 100, key="access_share",
                  help="The rest is hospital strain (people per hospital).")
    st.radio("Combine hazard, exposure and vulnerability by", ["Geometric mean (multiply)", "Weighted sum (add)"], key="method")
    st.button("Reset to notebook defaults", on_click=reset_settings, width="stretch")
    changed = any(st.session_state[k] != v for k, v in DEFAULTS.items())
    if changed:
        st.warning("Custom settings active. Reported findings use the defaults.")

expo_w = {"population": st.session_state.w_pop, "population_density_per_km2": st.session_state.w_den,
          "hydropower_capacity_mw": st.session_state.w_hyd, "hospital_count": st.session_state.w_hos,
          "school_count": st.session_state.w_sch}
if sum(expo_w.values()) == 0:
    expo_w = rm.DEFAULT_EXPO_W
METHOD = "additive" if st.session_state.method.startswith("Weighted") else "geometric"
S = scores(tuple(expo_w.items()), st.session_state.rain_share / 100, st.session_state.access_share / 100, METHOD)
D = df.join(S)
for c in ["risk_combined", "risk_flood", "risk_landslide"]:
    D[c + "_rank"] = D[c].rank(ascending=False).astype(int)
D["District"] = D.index.str.title()


# ---------------------------------------------------------------- helpers
def nepal_map(color_col, title, scale=RISK_SCALE, highlight=None, height=470, labels=None, zoom=5.3):
    m = D.reset_index()
    m["size"] = 9
    if highlight is not None:
        m["size"] = np.where(m.district_name.isin(highlight), 18, 9)
    fig = px.scatter_map(m, lat="latitude", lon="longitude", color=color_col, size="size", size_max=18,
                         hover_name="District", color_continuous_scale=scale, zoom=zoom, height=height,
                         center={"lat": 28.25, "lon": 84.1}, map_style="carto-positron",
                         hover_data={color_col: ":.0f", "province": True, "size": False, "latitude": False, "longitude": False},
                         labels=labels or {color_col: title})
    fig.update_layout(margin=dict(l=0, r=0, t=30, b=0), title=dict(text=title, font=dict(size=14)),
                      coloraxis_colorbar=dict(title="", thickness=12))
    return fig


def bar_top(series, title, color, n=10, fmt=".0f"):
    s = series.sort_values(ascending=False).head(n)[::-1]
    fig = go.Figure(go.Bar(x=s.values, y=[i.title() for i in s.index], orientation="h", marker_color=color,
                           text=[format(v, fmt) for v in s.values], textposition="outside"))
    fig.update_layout(title=dict(text=title, font=dict(size=14)), height=36 * n + 90, margin=dict(l=0, r=30, t=40, b=10),
                      xaxis=dict(visible=False, range=[0, s.max() * 1.18]), plot_bgcolor="white")
    return fig


def finding(tag, text):
    st.markdown(f"<span style='background:{TEAL};color:white;border-radius:10px;padding:2px 9px;font-weight:600;font-size:0.85em'>{tag}</span>&nbsp; {text}",
                unsafe_allow_html=True)


# ================================================================= pages
def page_intro():
    st.title("Where Nepal's climate risk lives")
    st.markdown("A district-level risk assessment of Nepal's 77 districts, tested against 15 years of recorded disasters, "
                "with a USD 100 million resilience recommendation.")
    c1, c2 = st.columns([1, 1.25])
    with c1:
        st.subheader("26 August 2026")
        st.markdown(
            "- **Trigger:** a glacier and rock-and-ice collapse at high altitude\n"
            "- **Path:** a flash flood down the Bhote Koshi and Trishuli river corridor (Sindhupalchok, Rasuwa, Nuwakot)\n"
            "- **Impact:** significant loss of life, displacement, and damage to hydropower plants")
        st.info("**The central question:** How do climate hazards, terrain, population, infrastructure and access interact "
                "to create risk across Nepal's 77 districts, and where has that risk actually materialized?")
        st.subheader("How risk is measured")
        a, b, c = st.columns(3)
        head = "<div style='color:{};font-weight:700;font-size:1.1rem'>{}</div>"
        a.markdown(head.format(TERRA, "Hazard") + "Heavy rain, steep terrain, big rivers", unsafe_allow_html=True)
        b.markdown(head.format(TEAL, "× Exposure") + "People, hospitals, schools, hydropower", unsafe_allow_html=True)
        c.markdown(head.format(SAFFRON, "× Vulnerability") + "Few roads, overstretched hospitals", unsafe_allow_html=True)
        st.caption("Risk is high only where all three meet: a landslide on an empty slope, or a city with no hazard, is low risk.")
    with c2:
        st.plotly_chart(nepal_map("risk_landslide", "Landslide risk by district (larger dots = 26 Aug corridor)", highlight=CORRIDOR,
                                  zoom=5.0), width="stretch")
    st.divider()
    st.markdown("**How to use this app:** work through the pages in the sidebar in order. They follow the assessment from "
                "climate → terrain and exposure → the risk index → validation → investment. Use **Scenarios** to test what "
                "interventions would change, and the **Model settings** in the sidebar to test how sensitive the results are.")


def page_climate():
    st.title("Climate: rainfall is rising")
    st.caption("NASA POWER satellite data, 2004–2025. Earlier years are excluded because of a data-source change in 2004. "
               "2026 is excluded from annual totals because it ends on 30 August.")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Rainfall trend", f"+{deck['rain_slope']} mm/yr", "p < 0.001")
    m2.metric("Recent vs baseline", f"+{deck['anomaly_median']:.0f}%", f"normal swing ±{deck['cv_median']:.0f}%", delta_color="off", delta_arrow="off")
    m3.metric("Series meaningfully wetter", f"{deck['meaningful_n']} of 45", "none drier", delta_color="off", delta_arrow="off")
    m4.metric("Extreme-rain days / yr", f"{deck['ext_recent']}", f"+{deck['ext_pct']}% vs {deck['ext_base']}")
    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure()
        fig.add_scatter(x=deck["rain_years"], y=deck["rain_mm"], mode="lines+markers", name="Annual rainfall", line=dict(color=SLATE, width=2.5))
        fig.add_scatter(x=deck["rain_years"], y=deck["rain_trend"], mode="lines", name="Trend", line=dict(color=TERRA, dash="dash", width=2.5))
        fig.update_layout(title="Average annual rainfall, 45 independent series (mm)", height=380, plot_bgcolor="white",
                          legend=dict(orientation="h", y=-0.15), margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig, width="stretch")
        finding("F1", f"Rainfall rises about {deck['rain_slope']} mm a year; 2020–25 is about {deck['anomaly_median']:.0f}% wetter than 2004–19.")
    with c2:
        yrs = deck["ext_years"]
        fig = go.Figure(go.Bar(x=yrs, y=deck["ext_days"], marker_color=[TERRA if y >= 2020 else GREY for y in yrs]))
        fig.update_layout(title="Extreme-rain days per district per year (heaviest 5% of rainy days)", height=380,
                          plot_bgcolor="white", margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig, width="stretch")
        finding("F2", f"Extreme days rose from {deck['ext_base']} to {deck['ext_recent']} a year (+{deck['ext_pct']}%); borderline significant (p = 0.05).")
    st.warning(f"**F3. 26 August 2026 was an ordinary rain day.** About 20 mm fell in the corridor, below the {deck['nat_p95']} mm "
               "national extreme threshold. The trigger was ice, not rain, so rainfall monitoring alone would have missed it.")
    st.subheader("District view")
    layer = st.radio("Show", ["Rainfall anomaly (%)", "Trend (mm/yr)", "Extreme-day threshold (mm)"], horizontal=True)
    col = {"Rainfall anomaly (%)": "anomaly_pct", "Trend (mm/yr)": "trend_mm_per_yr", "Extreme-day threshold (mm)": "p95_threshold_mm"}[layer]
    st.plotly_chart(nepal_map(col, layer, scale="Teal"), width="stretch")
    st.caption("Note: only 45 of 77 districts have independent rainfall data. Neighbours sharing one satellite cell show identical values.")


def page_terrain():
    st.title("Terrain, rivers and exposure")
    t1, t2 = st.tabs(["Terrain and rivers", "Exposure and vulnerability"])
    with t1:
        c1, c2 = st.columns([1.5, 1])
        with c1:
            m = D.reset_index()
            m["group"] = np.where(m.steep_and_river, "Steep and on major rivers", "Other districts")
            fig = px.scatter(m, x="ruggedness_score", y="river_score", color="group", hover_name="District",
                             color_discrete_map={"Steep and on major rivers": TERRA, "Other districts": GREY},
                             labels={"ruggedness_score": "Terrain ruggedness (0–100)", "river_score": "River size × closeness (0–100)", "group": ""},
                             height=460)
            fig.update_traces(marker=dict(size=11, line=dict(width=0.5, color="white")))
            fig.update_layout(plot_bgcolor="white", legend=dict(orientation="h", y=-0.15), margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, width="stretch")
        with c2:
            finding("F4", "Eight districts are in the top third for both terrain ruggedness and river hazard:")
            st.markdown(" · ".join(f"**{n}**" for n in deck["scatter"]["hot_names"]))
            st.markdown("**Why together?** Landslides can dam rivers and burst downstream; ice collapses travel down steep "
                        "valleys through river corridors. Steep terrain plus big rivers means *cascading* hazards.")
            st.caption("Ruggedness = spread of elevation in the district (HydroSHEDS). The supplied slope columns are "
                       "corrupted (stuck near 90°) and are not used. River score = geometric mean of river size and closeness to rivers.")
    with t2:
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(bar_top(D.exposure_score, "Exposure: people and critical assets (top 10)", TEAL), width="stretch")
            finding("F5", "People and assets cluster in Kathmandu Valley, Pokhara, the southern plains and hydropower hubs such as Dolakha (587 MW).")
        with c2:
            st.plotly_chart(bar_top(D.vulnerability_score, "Vulnerability: weak road and hospital access (top 10)", TERRA), width="stretch")
            finding("F6", "Remote mountain districts are most vulnerable: very few roads and one or two hospitals for 100,000+ people.")
        with st.expander("What vulnerability does NOT capture"):
            st.markdown("Poverty, age structure, disability, housing construction, early-warning coverage, footpaths and "
                        "footbridges, and accurate rural facility counts (OpenStreetMap undercounts). These are named limitations.")


def page_explorer():
    st.title("Risk explorer")
    st.caption("Risk = geometric mean of hazard, exposure and vulnerability, scored 0–100 (relative: 0 = lowest in Nepal). "
               "We use separate flood and landslide indices because validation showed they behave differently.")
    idx = st.radio("Index", list(INDEX_LABEL), format_func=INDEX_LABEL.get, horizontal=True)
    c1, c2 = st.columns([1.3, 1])
    with c1:
        st.plotly_chart(nepal_map(idx, INDEX_LABEL[idx], height=520), width="stretch")
    with c2:
        st.plotly_chart(bar_top(D[idx], f"Top 10: {INDEX_LABEL[idx]}", TERRA), width="stretch")
    if idx == "risk_flood":
        st.warning("The flood index failed validation (ρ = 0.24 with recorded floods). Treat it as low confidence. See Validation.")

    st.subheader("District profile")
    names = sorted(D.District)
    pick = st.selectbox("Choose a district", names, index=names.index("Sindhupalchok"))
    r = D.loc[pick.upper()]
    a, b, c, d = st.columns(4)
    a.metric("Combined risk", f"{r.risk_combined:.0f}", f"rank {r.risk_combined_rank} of 77", delta_color="off", delta_arrow="off")
    b.metric("Landslide risk", f"{r.risk_landslide:.0f}", f"rank {r.risk_landslide_rank}", delta_color="off", delta_arrow="off")
    c.metric("Flood risk", f"{r.risk_flood:.0f}", f"rank {r.risk_flood_rank}", delta_color="off", delta_arrow="off")
    d.metric("Recorded events / deaths", f"{int(r.events_total)} / {int(r.deaths)}", "2011–2026", delta_color="off", delta_arrow="off")

    comp = pd.DataFrame({
        "Component": ["Heavy rain", "River hazard", "Terrain ruggedness", "Exposure", "Vulnerability"],
        "District": [r.rain_score, r.river_score, r.ruggedness_score, r.exposure_score, r.vulnerability_score],
        "Nepal median": [D.rain_score.median(), D.river_score.median(), D.ruggedness_score.median(),
                         D.exposure_score.median(), D.vulnerability_score.median()]})
    c1, c2 = st.columns([1.2, 1])
    with c1:
        fig = go.Figure()
        fig.add_bar(y=comp.Component, x=comp.District, orientation="h", name=pick, marker_color=TERRA)
        fig.add_bar(y=comp.Component, x=comp["Nepal median"], orientation="h", name="Nepal median", marker_color=GREY)
        fig.update_layout(barmode="group", height=330, plot_bgcolor="white", xaxis=dict(range=[0, 105], title="score 0–100"),
                          yaxis=dict(autorange="reversed"), legend=dict(orientation="h", y=-0.25), margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, width="stretch")
    with c2:
        top_c = comp.assign(gap=comp.District - comp["Nepal median"]).sort_values("gap", ascending=False)
        st.markdown(f"**What drives {pick}'s risk:** its highest component relative to the national median is "
                    f"**{top_c.Component.iloc[0].lower()}**, and its lowest is **{top_c.Component.iloc[-1].lower()}**.")
        if pick.upper() in CORRIDOR:
            st.info("This district is in the 26 Aug 2026 corridor. Its rank is middling because glacial-collapse hazard is not in the data (finding F11).")
        raw = pd.DataFrame({"Indicator": ["Population", "Density (people/km²)", "Hydropower (MW)", "Hospitals (mapped)",
                                          "Schools (mapped)", "Road density (km/km²)", "Highest point (m)", "Elevation spread (m)"],
                            "Value": [f"{r.population:,.0f}", f"{r.population_density_per_km2:,.0f}", f"{r.hydropower_capacity_mw:,.1f}",
                                      f"{r.hospital_count:.0f}", f"{r.school_count:.0f}", f"{r.road_density_km_per_km2:.2f}",
                                      f"{r.elevation_max_m:,.0f}", f"{r.elevation_std_m:,.0f}"]})
        st.dataframe(raw, hide_index=True, width="stretch")

    with st.expander("Full table: all 77 districts"):
        cols = ["District", "province", "risk_combined", "risk_landslide", "risk_flood", "combined_hazard", "exposure_score",
                "vulnerability_score", "events_total", "deaths"]
        st.dataframe(D[cols].sort_values("risk_combined", ascending=False).round(1), hide_index=True, width="stretch")
        st.download_button("Download scores (CSV)", D[cols].round(2).to_csv(index=False), "district_risk_scores.csv")


PRESETS = {
    "Landslide early-warning targets (top 8 landslide risk)": lambda: list(D.risk_landslide.sort_values(ascending=False).head(8).index),
    "Most vulnerable 10 districts": lambda: list(D.vulnerability_score.sort_values(ascending=False).head(10).index),
    "26 Aug corridor": lambda: CORRIDOR,
    "Custom selection": lambda: [],
}


def page_scenarios():
    st.title("Scenarios: what would interventions change?")
    st.markdown("Pick districts, apply interventions, and see how their risk scores move. Scores are re-calculated on the "
                "**baseline scale**, so improvements are not hidden by re-normalising.")
    c1, c2 = st.columns([1, 1.4])
    with c1:
        preset = st.selectbox("Districts to treat", list(PRESETS))
        default = PRESETS[preset]()
        sel_names = st.multiselect("Selected districts", sorted(D.District), default=[n.title() for n in default])
        sel = [n.upper() for n in sel_names]
        st.markdown("**Interventions**")
        cov = st.slider("Early-warning coverage (share of people reached)", 0, 100, 80, 5, format="%d%%") / 100
        eff = st.slider("Vulnerability reduction at full coverage", 0, 60, 30, 5, format="%d%%",
                        help="Assumption: the Global Commission on Adaptation (2019) estimates that 24 hours' warning of a "
                             "hazard can cut the ensuing damage by about 30%.") / 100
        road = st.slider("Increase in road density", 0, 100, 0, 10, format="+%d%%") / 100
        hosp = st.slider("Extra hospitals per district", 0, 5, 0)
        idx = st.radio("Index to show", list(INDEX_LABEL), format_func=INDEX_LABEL.get, horizontal=True)
    sc = rm.scenario(df, S, sel, cov, eff, road, hosp, METHOD)
    with c2:
        if not sel:
            st.info("Select at least one district to see a scenario.")
            return
        cmp = pd.DataFrame({"Before": S.loc[sel, idx], "After": sc.loc[sel, idx]}).sort_values("Before", ascending=False)
        cmp["Change"] = cmp.After - cmp.Before
        fig = go.Figure()
        fig.add_bar(y=[i.title() for i in cmp.index], x=cmp.Before, orientation="h", name="Before", marker_color=GREY)
        fig.add_bar(y=[i.title() for i in cmp.index], x=cmp.After, orientation="h", name="After", marker_color=TEAL)
        fig.update_layout(barmode="group", height=max(320, 46 * len(cmp) + 80), plot_bgcolor="white",
                          title=f"{INDEX_LABEL[idx]}: before vs after", yaxis=dict(autorange="reversed"),
                          xaxis=dict(range=[0, 105]), legend=dict(orientation="h", y=-0.12), margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig, width="stretch")
        new_rank = sc[idx].rank(ascending=False)
        a, b = st.columns(2)
        a.metric("Average change in risk score", f"{cmp.Change.mean():+.1f} points")
        b.metric("Treated districts still in national top 10", f"{int((new_rank.loc[sel] <= 10).sum())} of {len(sel)}",
                 f"were {int((S[idx].rank(ascending=False).loc[sel] <= 10).sum())}", delta_color="off", delta_arrow="off")
    with st.expander("How the scenario works (assumptions)"):
        st.markdown(
            "- **Early warning** reduces a district's vulnerability score by *coverage × effectiveness*. Default 80% × 30% = 24% lower vulnerability.\n"
            "- **Roads** raise road density, which lowers the road-access vulnerability score.\n"
            "- **Hospitals** lower people-per-hospital, which lowers the health-strain score.\n"
            "- Hazard and exposure do not change: early warning saves lives but does not stop the landslide.\n"
            "- Because risk is a geometric mean, a 24% cut in vulnerability lowers risk by about 9% (the cube root of 0.76), not 24%. "
            "This is the honest arithmetic of a multiplicative index.\n"
            "- These are illustrative assumptions, not engineering estimates.")


def page_validation():
    st.title("Validation against 12,341 real disasters")
    st.markdown("Our index is a hypothesis until it is checked against what actually happened. We correlate district scores "
                "with BIPAD's recorded events and deaths (2011–2026) using **Spearman ρ**: 0 = no link, 0.3 weak, 0.5 moderate, 0.7+ strong.")
    if changed:
        st.warning("You are viewing correlations under custom model settings. The brief forbids tuning weights until the "
                   "correlation looks good. Use this only to check robustness; reported results use the defaults.")
    cor = rm.correlations(S, df)
    a, b, c = st.columns(3)
    a.metric("Landslide index vs landslides", f"ρ = {cor.loc['risk_landslide', 'landslide_events']:.2f}", "works (F8)", delta_arrow="off")
    b.metric("Combined index vs all events", f"ρ = {cor.loc['risk_combined', 'events_total']:.2f}", "moderate (F7)", delta_color="off", delta_arrow="off")
    c.metric("Flood index vs floods", f"ρ = {cor.loc['risk_flood', 'flood_events']:.2f}", "fails (F9)", delta_color="inverse", delta_arrow="off")
    c1, c2 = st.columns([1.1, 1])
    with c1:
        nice = {"risk_combined": "Combined risk", "risk_flood": "Flood risk", "risk_landslide": "Landslide risk",
                "combined_hazard": "Combined hazard", "flood_hazard": "Flood hazard", "landslide_hazard": "Landslide hazard",
                "exposure_score": "Exposure", "vulnerability_score": "Vulnerability"}
        z = cor.rename(index=nice, columns={"events_total": "All events", "flood_events": "Floods", "landslide_events": "Landslides", "deaths": "Deaths"})
        fig = px.imshow(z, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-0.8, zmax=0.8, aspect="auto", height=430)
        fig.update_layout(title="Do our scores match recorded disasters?", margin=dict(l=0, r=0, t=40, b=0), coloraxis_showscale=False)
        st.plotly_chart(fig, width="stretch")
    with c2:
        st.subheader("Why the flood index fails")
        st.markdown(f"Most recorded floods are in **{', '.join(deck['top_flood_events']['labels'])}**: flat southern lowlands. "
                    "Our flood variables describe mountain rivers and rain; no variable captures floodplain flatness. "
                    "Floods are also recorded more where people and roads are.")
        fc = pd.Series(deck["flood_corr"])
        fig = go.Figure(go.Bar(x=fc.values, y=fc.index, orientation="h", marker_color=[TERRA if v < 0 else TEAL for v in fc.values],
                               text=[f"{v:+.2f}" for v in fc.values], textposition="outside"))
        fig.update_layout(title="Correlation with recorded floods", height=250, plot_bgcolor="white",
                          xaxis=dict(range=[-0.5, 0.55]), margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig, width="stretch")
    st.subheader("Decision: separate flood and landslide indices")
    st.markdown("Floods and landslides strike different districts (ρ = −0.13 between their counts). Each specific index "
                "beats the combined index on its own hazard. A single index would hide that we predict landslides well and floods poorly.")
    st.subheader("Blind spots in the record")
    c1, c2 = st.columns([1.3, 1])
    with c1:
        yrs = deck["events_years"]
        fig = go.Figure(go.Bar(x=yrs, y=deck["events_n"], marker_color=[TERRA if y >= 2024 else GREY for y in yrs]))
        fig.update_layout(title="Recorded events per year (BIPAD)", height=320, plot_bgcolor="white", margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig, width="stretch")
    with c2:
        finding("F10", f"Events quadrupled after 2023 while deaths per event fell from {deck['deaths_per_event'][0]} to "
                       f"{deck['deaths_per_event'][-1]}: more minor incidents logged, not more disasters.")
        late = events[(events.incident_date >= "2026-08-25") & events.district_name.isin(CORRIDOR)]
        finding("F10", f"The 26 Aug collapse is missing: only {len(late)} minor corridor events from 25 Aug on, with {int(late.deaths.sum())} deaths recorded.")
        cr = deck["corridor_rank"]
        finding("F11", f"Glacial risk is invisible to our data: Sindhupalchok ranks #{cr['Sindhupalchok']}, Rasuwa #{cr['Rasuwa']}.")


def page_invest():
    st.title("USD 100 million: money follows evidence")
    al = pd.DataFrame(deck["alloc"])
    al["Line"] = al.line.str.replace(r"^\S+\s", "", regex=True)
    act = al[al.line.str.split().str[0].isin(["1a", "1b", "3", "4"])].usd.sum()
    a, b = st.columns(2)
    a.metric("Act where evidence is strong", f"${act}M", "early warning, infrastructure, preparedness", delta_color="off", delta_arrow="off")
    b.metric("Close the blind spots", f"${100 - act}M", "glacial monitoring, better data", delta_color="off", delta_arrow="off")
    c1, c2 = st.columns([1, 1.2])
    with c1:
        s = al.sort_values("usd")
        fig = go.Figure(go.Bar(x=s.usd, y=s.Line, orientation="h", marker_color=TEAL, text=[f"${v}M" for v in s.usd], textposition="outside"))
        fig.update_layout(title="Allocation (USD million)", height=380, plot_bgcolor="white", xaxis=dict(visible=False, range=[0, 27]),
                          margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig, width="stretch")
    with c2:
        st.dataframe(al[["Line", "usd", "findings", "targets"]].rename(columns={"usd": "USD M", "findings": "Findings", "targets": "Target districts"}),
                     hide_index=True, width="stretch", height=380)
    st.subheader("What the early-warning lines would do")
    st.caption("Applies the Scenarios page defaults (80% coverage × 30% effectiveness) to the early-warning target districts.")
    targets = [t.strip().upper() for row in al[al.line.str.startswith(("1a", "1b"))].targets for t in row.split(",")]
    sc = rm.scenario(df, S, targets, 0.8, 0.3, 0, 0, METHOD)
    res = pd.DataFrame({"District": [t.title() for t in targets], "Landslide risk before": S.loc[targets, "risk_landslide"].values,
                        "after": sc.loc[targets, "risk_landslide"].values, "Flood risk before": S.loc[targets, "risk_flood"].values,
                        "after ": sc.loc[targets, "risk_flood"].values}).round(1)
    st.dataframe(res, hide_index=True, width="stretch")
    with st.expander("Why each line is sized as it is"):
        st.markdown(
            "| Line | USD M | Why |\n|---|---|---|\n"
            "| Terrain & glacial monitoring | 22 | The 26 Aug disaster was a glacial collapse (F3) missed by both our index and the record (F10, F11); ruggedness is the strongest predictor (F8) |\n"
            "| Infrastructure reinforcement | 20 | Concentrated exposure (F5), including the hydropower damaged on 26 Aug |\n"
            "| Landslide early warning | 18 | Best-validated finding (F8); extreme rain is rising (F1, F2) |\n"
            "| Community preparedness | 15 | Remote districts where help arrives slowest (F6) |\n"
            "| Data infrastructure | 15 | Flood index failure (F9), reporting surge and missing event (F10), only 45 independent rain series |\n"
            "| Flood early warning | 10 | Floods concentrate in the Terai (F9), but our index can't rank them, so funding goes only to proven hotspots |")


def page_method():
    st.title("Method, assumptions and sources")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Key assumptions")
        st.markdown(
            "1. Climate trends use 2004–2025 only (data-source break before 2004; 2026 incomplete)\n"
            "2. 45 independent rainfall series, each counted once in national statistics\n"
            "3. Extreme day = above the district's 95th percentile of rainy days (≥ 1 mm)\n"
            "4. Baseline 2004–19 vs recent 2020–25; meaningful if larger than normal year-to-year variation\n"
            "5. Terrain ruggedness = elevation standard deviation (slope data corrupted)\n"
            "6. River hazard = geometric mean of river size (log) and closeness to rivers\n"
            "7. Skewed variables log-scaled, then min-max to 0–100\n"
            "8. Exposure weights 30/20/20/15/15 (population, density, hydropower, hospitals, schools)\n"
            "9. Vulnerability = equal mix of road access and people per hospital\n"
            "10. Risk = geometric mean of hazard, exposure, vulnerability (components floored at 1)")
        st.subheader("Limitations")
        st.markdown("- No poverty, age, housing or early-warning coverage data\n- OpenStreetMap undercounts rural facilities and roads\n"
                    "- One rainfall point per district; coarse satellite grid\n- No floodplain or glacial-lake variables\n"
                    "- Disaster record: reporting surge after 2023; 26 Aug 2026 event missing\n- Correlation shows association, not cause")
    with c2:
        st.subheader("Data sources")
        st.markdown(
            "- **NASA POWER** (power.larc.nasa.gov): daily rainfall (PRECTOTCORR), temperature, humidity, wind\n"
            "- **HydroSHEDS**: elevation (15 arc-sec DEM) and flow accumulation\n"
            "- **Nepal National Statistics Office**, 2021 Census: population and density\n"
            "- **OpenStreetMap** (Overpass API): hospitals, schools, roads, bridges\n"
            "- **Wikipedia**, List of power stations in Nepal (9 Mar 2026): hydropower capacity\n"
            "- **geoBoundaries ADM2**: district boundaries, area and representative points\n"
            "- **BIPAD Portal**, Government of Nepal: disaster incidents 2011–2026")
        st.subheader("Glossary")
        st.markdown("- **Percentile (P95):** the value 95% of observations fall below\n- **p-value:** chance of a result this strong if nothing real were going on\n"
                    "- **Spearman ρ:** rank correlation, −1 to +1\n- **Geometric mean:** multiply, then take the root; low if any part is low\n"
                    "- **Min-max:** rescales to 0–100 (lowest district = 0)")
        st.caption("Full reasoning and code: nepal_risk_assessment.ipynb")


pg = st.navigation([
    st.Page(page_intro, title="The question", icon="🏔️", default=True),
    st.Page(page_climate, title="Climate", icon="🌧️", url_path="climate"),
    st.Page(page_terrain, title="Terrain and exposure", icon="⛰️", url_path="terrain"),
    st.Page(page_explorer, title="Risk explorer", icon="🗺️", url_path="explorer"),
    st.Page(page_scenarios, title="Scenarios", icon="🎚️", url_path="scenarios"),
    st.Page(page_validation, title="Validation", icon="✅", url_path="validation"),
    st.Page(page_invest, title="Investment", icon="💰", url_path="investment"),
    st.Page(page_method, title="Method and sources", icon="📚", url_path="method"),
])
pg.run()
