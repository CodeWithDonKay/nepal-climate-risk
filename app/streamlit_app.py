"""Nepal Climate Risk Intelligence Platform: Streamlit app (capstone deliverable, Option A).

Run from the project folder:   streamlit run app/streamlit_app.py
  ui.py          design system (colours, CSS, chart template, components)
  risk_model.py  scoring engine (unchanged; reproduces the notebook exactly)
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
from ui import BLUE, CONTEXT, HEAD, MUTED, VERMILLION

APP_DIR = os.path.dirname(os.path.abspath(__file__))
st.set_page_config(page_title="Nepal Climate Risk Intelligence Platform", page_icon=":material/landscape:", layout="wide")
ui.setup()
st.logo(os.path.join(APP_DIR, "assets", "logo.svg"), size="large",
        icon_image=os.path.join(APP_DIR, "assets", "logo_icon.svg"))  # icon-only mark when the sidebar is collapsed

CORRIDOR = ["SINDHUPALCHOK", "RASUWA", "NUWAKOT"]
HAZARD = {"risk_landslide": "Landslide", "risk_flood": "Flood (low confidence)", "risk_combined": "Combined"}
ALL_PROV, ALL_DIST = "All provinces", "All districts"


# ---------------------------------------------------------------- data (cached)
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

# ---------------------------------------------------------------- state: model settings + shared filters
MODEL_DEFAULTS = {"w_pop": 30, "w_den": 20, "w_hyd": 20, "w_hos": 15, "w_sch": 15, "rain_share": 50, "access_share": 50,
                  "method": "Geometric mean"}
FILTER_DEFAULTS = {"flt_province": ALL_PROV, "flt_district": ALL_DIST, "flt_hazard": "risk_landslide", "flt_period": (2004, 2025)}
for k, v in {**MODEL_DEFAULTS, **FILTER_DEFAULTS}.items():
    # Re-assigning keeps a widget's value when the user moves to a page where that widget isn't drawn
    st.session_state[k] = st.session_state.get(k, v)


def reset_model():
    for k, v in MODEL_DEFAULTS.items():
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
    st.button("Reset model settings", on_click=reset_model, width="stretch")
    changed = any(st.session_state[k] != v for k, v in MODEL_DEFAULTS.items())
    if changed:
        st.markdown("<div class='sb-text' style='margin-top:.6rem'><b>⚠ Custom settings active.</b> Reported findings use the defaults.</div>",
                    unsafe_allow_html=True)

expo_w = {"population": st.session_state.w_pop, "population_density_per_km2": st.session_state.w_den,
          "hydropower_capacity_mw": st.session_state.w_hyd, "hospital_count": st.session_state.w_hos,
          "school_count": st.session_state.w_sch}
if sum(expo_w.values()) == 0:
    expo_w = rm.DEFAULT_EXPO_W
METHOD = "additive" if st.session_state.method == "Weighted sum" else "geometric"
S = scores(tuple(expo_w.items()), st.session_state.rain_share / 100, st.session_state.access_share / 100, METHOD)
D = df.join(S)
for c in HAZARD:
    D[c + "_rank"] = D[c].rank(ascending=False).astype(int)
    D[c + "_band"] = D[c].map(lambda v: ui.band_of(v)[0])
D["District"] = D.index.str.title()
PROVINCES = [ALL_PROV] + sorted(D.province.unique())


# ---------------------------------------------------------------- filters
def scope():
    p = st.session_state.flt_province
    return D if p == ALL_PROV else D[D.province == p]


def scope_name():
    p = st.session_state.flt_province
    return "Nepal" if p == ALL_PROV else f"{p} Province"


def selected_district():
    d = st.session_state.flt_district
    return None if d == ALL_DIST else d.upper()


def _on_province():
    d = selected_district()
    if d and st.session_state.flt_province not in (ALL_PROV, D.loc[d, "province"]):
        st.session_state.flt_district = ALL_DIST


def filter_bar(fields, key):
    """Shared filter bar; values live in session state so they carry across pages. Only shows filters that affect the page."""
    widths = {"province": 1.1, "district": 1.2, "hazard": 1.1, "period": 1.5}
    with st.container(key=f"filterbar_{key}"):
        cols = st.columns([widths[f] for f in fields], gap="medium")
        for col, f in zip(cols, fields):
            with col:
                if f == "province":
                    st.selectbox("Province", PROVINCES, key="flt_province", on_change=_on_province)
                elif f == "district":
                    opts = [ALL_DIST] + sorted(scope().District)
                    if st.session_state.flt_district not in opts:
                        st.session_state.flt_district = ALL_DIST
                    st.selectbox("District", opts, key="flt_district")
                elif f == "hazard":
                    st.selectbox("Hazard index", list(HAZARD), format_func=HAZARD.get, key="flt_hazard")
                elif f == "period":
                    st.slider("Period (climate record)", 2004, 2025, key="flt_period",
                              help="2004-2025 only: a data-source change makes earlier rainfall incomparable; 2026 is incomplete.")


def _map_select(key):
    """Clicking a district on a map selects it in the shared district filter."""
    def cb():
        ev = st.session_state.get(key)
        pts = ev.selection.points if ev and ev.selection else []
        if pts:
            lat, lon = pts[0].get("lat"), pts[0].get("lon")
            if lat is not None:
                d = ((df.latitude - lat) ** 2 + (df.longitude - lon) ** 2).idxmin()
                st.session_state.flt_district = d.title()
                if st.session_state.flt_province not in (ALL_PROV, df.loc[d, "province"]):
                    st.session_state.flt_province = ALL_PROV
    return cb


# ---------------------------------------------------------------- charts
# One-hue colour ramps per hazard, as in the original design (light = lower risk, dark = higher risk)
MAP_RAMP = {
    "risk_landslide": ["#F7F1EA", "#E7D3BC", "#CFAA82", "#B07E4C", "#865628", "#553515"],
    "risk_flood": ["#EEF4FA", "#C6DBEF", "#8DB8DE", "#4F8DC4", "#2462A3", "#133F73"],
    "risk_combined": ["#FBEFF1", "#F2C4CC", "#E28797", "#C94A61", "#A51F3A", "#6A0F22"],
}


def _view(data):
    """Centre and zoom that fit the districts shown (all of Nepal, or one province)."""
    lat0, lat1, lon0, lon1 = data.latitude.min(), data.latitude.max(), data.longitude.min(), data.longitude.max()
    span = max(lon1 - lon0, (lat1 - lat0) * 2, 0.8)
    zoom = float(np.clip(np.log2(360 / span) - 0.55, 4.5, 8.5))
    return {"lat": (lat0 + lat1) / 2, "lon": (lon0 + lon1) / 2}, zoom


def risk_map(idx, key, data, height=500, select=True):
    """Interactive basemap (zoom, pan, scroll-zoom, hover) with each district shaded on its hazard's colour ramp.
    The selected district is ringed; hover shows score, risk band and rank."""
    sel = selected_district()
    m = data.reset_index()
    m["band"] = m[idx].map(lambda v: ui.band_of(v)[0])
    fig = go.Figure()
    if sel in data.index:  # dark ring under the selected district
        r = data.loc[sel]
        fig.add_scattermap(lat=[r.latitude], lon=[r.longitude], mode="markers", hoverinfo="skip", showlegend=False,
                           marker=dict(size=27, color=HEAD))
    fig.add_scattermap(
        lat=m.latitude, lon=m.longitude, mode="markers", showlegend=False,
        marker=dict(size=np.where(m.district_name == sel, 20, 13), color=m[idx], cmin=0, cmax=100,
                    colorscale=MAP_RAMP[idx], opacity=0.95,
                    colorbar=dict(orientation="h", x=0.02, xanchor="left", y=0.98, yanchor="top", len=0.34, thickness=9,
                                  title=dict(text=f"{HAZARD[idx]} risk (0–100)", side="top", font=dict(size=11, color=ui.BODY)),
                                  bgcolor="rgba(255,255,255,0.88)", tickfont=dict(size=10, color=ui.BODY))),
        customdata=np.stack([m.District, m.province, m[idx].round(0), m.band, m[idx + "_rank"],
                             m.risk_landslide.round(0), m.risk_flood.round(0)], axis=-1),
        hovertemplate=("<b>%{customdata[0]}</b> · %{customdata[1]} Province<br>" + f"{HAZARD[idx]} risk: " +
                       "<b>%{customdata[2]}</b> / 100 (%{customdata[3]})<br>Rank %{customdata[4]} of 77<br>"
                       "Landslide %{customdata[5]} · Flood %{customdata[6]}<extra></extra>"))
    center, zoom = _view(data)
    fig.update_layout(height=height, margin=dict(l=0, r=0, t=0, b=0),
                      map=dict(style="carto-positron", center=center, zoom=zoom))
    return ui.chart(fig, key=key, on_select=_map_select(key) if select else "ignore", selection_mode=("points", "box"))


def hbar(series, color=BLUE, n=10, labels=None, height=None):
    s = series.sort_values(ascending=False).head(n)[::-1]
    txt = labels[s.index] if labels is not None else [f"{v:.0f}" for v in s.values]
    fig = go.Figure(go.Bar(x=s.values, y=[i.title() for i in s.index], orientation="h", marker_color=color,
                           marker_line=dict(color=HEAD, width=0.5), text=txt, textposition="outside",
                           textfont=dict(color=ui.BODY, size=12), cliponaxis=False, hovertemplate="%{y}: %{x:.1f}<extra></extra>"))
    fig.update_layout(height=height or 32 * len(s) + 40, margin=dict(l=8, r=110, t=8, b=8),
                      xaxis=dict(visible=False, range=[0, max(s.max(), 1) * 1.05]), yaxis=dict(tickfont=dict(color=HEAD, size=12.5)))
    return fig


def trend_chart(years, values, trend, name, unit, color, symbol, y0, y1, fmt=",.0f"):
    yrs = np.array(years)
    m = (yrs >= y0) & (yrs <= y1)
    fig = go.Figure()
    fig.add_scatter(x=yrs[m], y=np.array(values)[m], mode="lines+markers", name=name, line=dict(color=color, width=2.2),
                    marker=dict(symbol=symbol, size=8, color=color, line=dict(color="white", width=1.2)),
                    hovertemplate="%{x}: %{y:" + fmt + "} " + unit + "<extra></extra>")
    if trend is not None:
        fig.add_scatter(x=yrs[m], y=np.array(trend)[m], mode="lines", name="Linear trend 2004–2025",
                        line=dict(color=HEAD, width=1.8, dash="dash"), hoverinfo="skip")
    fig.update_layout(height=300, yaxis=dict(tickformat=fmt, title=unit))
    return fig


def sel_period():
    y0, y1 = st.session_state.flt_period
    return int(y0), int(y1)


def _trend_line(years, values):
    b, a = np.polyfit(years, values, 1)
    return [a + b * y for y in years]


# ================================================================= pages
def page_overview():
    ui.page_header("Climate Overview", "Explore climate patterns, risks and future projections for Nepal.", "Dashboard")
    st.caption("This platform covers historical climate (2004–2025), structural risk and recorded disasters. "
               "It contains no future climate projections.")
    filter_bar(["province", "district", "hazard", "period"], "overview")
    idx, (y0, y1), sc, d = st.session_state.flt_hazard, sel_period(), scope(), selected_district()

    yrs = np.array(deck["temp_years"])
    tm = (yrs >= y0) & (yrs <= y1)
    temps = np.array(deck["temp_c"])[tm]
    ryrs = np.array(deck["rain_years"])
    rm_ = (ryrs >= y0) & (ryrs <= y1)
    rain = np.array(deck["rain_mm"])[rm_]
    if d:
        r = D.loc[d]
        risk_item = {"icon": "alert", "label": "Climate risk index", "value": f"{r[idx]:.0f}", "unit": "/ 100",
                     "note": f"{r.District} · {HAZARD[idx]} · rank {r[idx + '_rank']} of 77", "badge": ui.risk_badge(r[idx])}
    else:
        hi = int((sc[idx] >= 60).sum())
        risk_item = {"icon": "alert", "label": "Climate risk index", "value": f"{hi}", "unit": f"of {len(sc)} districts",
                     "note": f"rated High or Very high for {HAZARD[idx].lower()} risk in {scope_name()}"}
    ev_scope = events[events.district_name.isin(sc.index)]
    ui.kpi_grid([
        {"icon": "thermometer", "label": "Average temperature", "value": f"{temps.mean():.1f}", "unit": "°C",
         "trend": f"{deck['temp_slope_decade']:+.2f} °C per decade · not statistically significant (p = {deck['temp_p']:.2f})",
         "note": f"National annual mean, {y0}–{y1}", "spark": temps, "spark_color": ui.TEMP,
         "spark_label": f"Annual mean temperature {y0} to {y1}, from {temps[0]:.1f} to {temps[-1]:.1f} degrees"},
        {"icon": "droplet", "label": "Annual precipitation", "value": f"{rain.mean():,.0f}", "unit": "mm / yr",
         "trend": f"▲ +{deck['anomaly_median']:.0f}% in 2020–25 vs 2004–19 (median district)",
         "note": f"National annual mean, {y0}–{y1}", "spark": rain, "spark_color": ui.PRECIP,
         "spark_label": f"Annual rainfall {y0} to {y1}, from {rain[0]:,.0f} to {rain[-1]:,.0f} millimetres"},
        risk_item,
        {"icon": "layers", "label": "District coverage", "value": f"{len(sc)}", "unit": "districts",
         "note": f"{sc.climate_grid_cluster.nunique()} independent climate series · {len(ev_scope):,} disaster records (2011–2026) in {scope_name()}"},
    ])

    c1, c2 = st.columns([1.55, 1], gap="medium")
    with c1:
        with ui.card("ov_map", f"{HAZARD[idx]} risk by district", f"{scope_name()}. Darker = higher risk. Zoom, pan and hover; "
                                                                   "click a district to open it."):
            risk_map(idx, "map_overview", sc, height=380)
    with c2:
        if d:
            r = D.loc[d]
            comp = pd.Series({"Heavy rain": r.rain_score, "River hazard": r.river_score, "Terrain ruggedness": r.ruggedness_score,
                              "Exposure": r.exposure_score, "Vulnerability": r.vulnerability_score})
            med = pd.Series({"Heavy rain": D.rain_score.median(), "River hazard": D.river_score.median(),
                             "Terrain ruggedness": D.ruggedness_score.median(), "Exposure": D.exposure_score.median(),
                             "Vulnerability": D.vulnerability_score.median()})
            with ui.card("ov_profile", f"Hazard profile: {r.District}", "All components on the same 0–100 relative scale"):
                fig = go.Figure()
                fig.add_bar(y=comp.index, x=comp.values, orientation="h", name=r.District, marker_color=BLUE,
                            text=[f"{v:.0f}" for v in comp.values], textposition="outside", cliponaxis=False,
                            hovertemplate="%{y}: %{x:.0f}<extra></extra>")
                fig.add_scatter(y=med.index, x=med.values, mode="markers", name="National median",
                                marker=dict(symbol="line-ns", size=22, line=dict(width=3, color=HEAD)),
                                hovertemplate="National median %{y}: %{x:.0f}<extra></extra>")
                fig.update_layout(height=330, margin=dict(r=36, t=30), xaxis=dict(range=[0, 108]),
                                  yaxis=dict(autorange="reversed", tickfont=dict(color=HEAD)))
                ui.chart(fig)
                st.markdown(ui.risk_badge(r[idx]) + f"&nbsp; <span style='font-size:.85rem;color:{MUTED}'>{HAZARD[idx]} risk</span>",
                            unsafe_allow_html=True)
        else:
            with ui.card("ov_top", f"Highest {HAZARD[idx].split(' (')[0].lower()} risk", f"Top 10 districts in {scope_name()}"):
                lab = sc[idx].map(lambda v: f"{v:.0f} · {ui.band_of(v)[0]}")
                ui.chart(hbar(sc[idx], BLUE, labels=lab, height=380))

    c1, c2 = st.columns(2, gap="medium")
    with c1:
        with ui.card("ov_rain", "Annual precipitation", f"National mean of 45 independent satellite series, {y0}–{y1}"):
            ui.chart(trend_chart(deck["rain_years"], deck["rain_mm"], deck["rain_trend"], "Annual rainfall", "mm",
                                 ui.PRECIP, "circle", y0, y1))
    with c2:
        with ui.card("ov_temp", "Average temperature", f"National annual mean, {y0}–{y1}"):
            ui.chart(trend_chart(deck["temp_years"], deck["temp_c"], _trend_line(deck["temp_years"], deck["temp_c"]),
                                 "Mean temperature", "°C", ui.TEMP, "diamond", y0, y1, fmt=".1f"))

    c1, c2 = st.columns([1, 1.2], gap="medium")
    with c1:
        with ui.card("ov_event", "Context: 26 August 2026"):
            st.markdown("<dl class='dl'><dt>Trigger</dt><dd>Glacier and rock-and-ice collapse at high altitude</dd>"
                        "<dt>Path</dt><dd>Flash flood down the Bhote Koshi and Trishuli corridor (Sindhupalchok, Rasuwa, Nuwakot)</dd>"
                        "<dt>Impact</dt><dd>Loss of life, displacement and damage to hydropower plants</dd></dl>", unsafe_allow_html=True)
    with c2:
        with ui.card("ov_find", "Key findings"):
            ui.findings([
                ("F1", f"Rainfall is rising about <b>{deck['rain_slope']} mm a year</b> since 2004."),
                ("F8", "The <b>landslide index validates</b> against recorded landslides (ρ = 0.52)."),
                ("F9", "The <b>flood index does not</b> (ρ = 0.24): recorded floods are on the flat southern plains."),
                ("F11", "Glacial-collapse hazard, the trigger on 26 August, is <b>not visible</b> in the available data."),
            ])


def page_risk_mapping():
    ui.page_header("Risk Mapping", "District risk from hazard, exposure and vulnerability, scored 0–100 relative to other districts. "
                   "Flood and landslide risk are kept separate because validation showed they behave differently.", "Analysis")
    filter_bar(["province", "district", "hazard"], "mapping")
    idx, sc, d = st.session_state.flt_hazard, scope(), selected_district()
    if idx == "risk_flood":
        ui.note("The flood index did not validate against recorded floods (ρ = 0.24). Treat its rankings as low confidence.",
                "Low-confidence index", warn=True)
    c1, c2 = st.columns([1.5, 1], gap="medium")
    with c1:
        with ui.card("rm_map", f"{HAZARD[idx]} risk", f"{scope_name()} · zoom, pan and hover; click a district to open its profile"):
            risk_map(idx, "map_mapping", sc, height=520)
    with c2:
        with ui.card("rm_rank", "District ranking", "Search, sort or download with the table toolbar"):
            t = sc.sort_values(idx, ascending=False)
            st.dataframe(pd.DataFrame({"District": t.District, "Score": t[idx].round(1), "Risk band": t[idx + "_band"],
                                       "National rank": t[idx + "_rank"]}),
                         hide_index=True, width="stretch", height=505,
                         column_config={"Score": st.column_config.ProgressColumn("Score (0–100)", min_value=0, max_value=100, format="%.0f"),
                                        "National rank": st.column_config.NumberColumn("Rank", format="%d")})

    if not d:
        ui.note("Choose a district in the filter bar, or click one on the map, to see its profile.", "District profile")
        return
    r = D.loc[d]
    st.markdown(f"<h2 class='card-title' style='margin:10px 0 8px'>District profile: {r.District}</h2>", unsafe_allow_html=True)
    ui.kpi_grid([
        {"icon": "alert", "label": "Combined risk", "value": f"{r.risk_combined:.0f}", "unit": "/ 100",
         "note": f"Rank {r.risk_combined_rank} of 77", "badge": ui.risk_badge(r.risk_combined)},
        {"icon": "map", "label": "Landslide risk", "value": f"{r.risk_landslide:.0f}", "unit": "/ 100",
         "note": f"Rank {r.risk_landslide_rank} of 77", "badge": ui.risk_badge(r.risk_landslide)},
        {"icon": "rain", "label": "Flood risk", "value": f"{r.risk_flood:.0f}", "unit": "/ 100",
         "note": f"Rank {r.risk_flood_rank} of 77 · low confidence", "badge": ui.risk_badge(r.risk_flood)},
        {"icon": "activity", "label": "Recorded events / deaths", "value": f"{int(r.events_total)} / {int(r.deaths)}",
         "note": "BIPAD records 2011–2026, after removing duplicates"},
    ])
    comp = pd.DataFrame({
        "Component": ["Heavy rain", "River hazard", "Terrain ruggedness", "Exposure", "Vulnerability"],
        "District": [r.rain_score, r.river_score, r.ruggedness_score, r.exposure_score, r.vulnerability_score],
        "Median": [D.rain_score.median(), D.river_score.median(), D.ruggedness_score.median(),
                   D.exposure_score.median(), D.vulnerability_score.median()]})
    c1, c2 = st.columns([1.2, 1], gap="medium")
    with c1:
        with ui.card("rm_comp", "Hazard comparison", f"{r.District} vs the national median; every bar uses the same 0–100 scale"):
            fig = go.Figure()
            fig.add_bar(y=comp.Component, x=comp.District, orientation="h", name=r.District, marker_color=BLUE,
                        text=[f"{v:.0f}" for v in comp.District], textposition="outside", cliponaxis=False,
                        hovertemplate="%{y}: %{x:.0f}<extra></extra>")
            fig.add_bar(y=comp.Component, x=comp.Median, orientation="h", name="National median", marker_color=CONTEXT,
                        marker_pattern_shape="/", marker_pattern_fgcolor="#FFFFFF",
                        text=[f"{v:.0f}" for v in comp.Median], textposition="outside", cliponaxis=False,
                        hovertemplate="Median %{y}: %{x:.0f}<extra></extra>")
            fig.update_layout(barmode="group", height=360, margin=dict(r=36, t=30), xaxis=dict(range=[0, 108]),
                              yaxis=dict(autorange="reversed", tickfont=dict(color=HEAD)), bargap=0.25, bargroupgap=0.08)
            ui.chart(fig)
            gap = comp.assign(g=comp.District - comp.Median).sort_values("g", ascending=False)
            st.markdown(f"<p class='card-sub'>Strongest driver relative to the median: <b>{gap.Component.iloc[0].lower()}</b>; "
                        f"weakest: <b>{gap.Component.iloc[-1].lower()}</b>.</p>", unsafe_allow_html=True)
    with c2:
        with ui.card("rm_ind", "Indicators"):
            if d in CORRIDOR:
                ui.note("This district lies in the 26 August 2026 corridor. Its rank is moderate because glacial-collapse "
                        "hazard is not represented in the data (F11).")
            ui.table(pd.DataFrame({
                "Indicator": ["Population", "Density", "Hydropower", "Hospitals (mapped)", "Schools (mapped)",
                              "Road density", "Highest point", "Elevation spread"],
                "Value": [f"{r.population:,.0f}", f"{r.population_density_per_km2:,.0f} per km²", f"{r.hydropower_capacity_mw:,.1f} MW",
                          f"{r.hospital_count:.0f}", f"{r.school_count:.0f}", f"{r.road_density_km_per_km2:.2f} km/km²",
                          f"{r.elevation_max_m:,.0f} m", f"{r.elevation_std_m:,.0f} m"]}), num=("Value",))


def page_climate():
    ui.page_header("Climate Trends", "NASA POWER satellite record, 2004–2025. Earlier years are excluded because of a data-source "
                   "change in 2004; 2026 is excluded from annual totals because the record ends on 30 August.", "Analysis")
    filter_bar(["province", "district", "period"], "climate")
    (y0, y1), sc, d = sel_period(), scope(), selected_district()
    ui.kpi_grid([
        {"icon": "rain", "label": "Rainfall trend", "value": f"+{deck['rain_slope']}", "unit": "mm / yr", "note": "2004–2025 · p < 0.001"},
        {"icon": "droplet", "label": "Recent vs baseline", "value": f"+{deck['anomaly_median']:.0f}", "unit": "%",
         "note": f"2020–25 vs 2004–19 · normal year-to-year swing ±{deck['cv_median']:.0f}%"},
        {"icon": "layers", "label": "Series meaningfully wetter", "value": f"{deck['meaningful_n']}", "unit": "of 45",
         "note": "None meaningfully drier"},
        {"icon": "activity", "label": "Extreme-rain days", "value": f"{deck['ext_base']} → {deck['ext_recent']}", "unit": "per yr",
         "note": f"+{deck['ext_pct']}% · borderline significant (p = 0.05)"},
    ])
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        with ui.card("cl_rain", "Annual precipitation", f"National mean, {y0}–{y1}; dashed line = 2004–2025 linear trend"):
            ui.chart(trend_chart(deck["rain_years"], deck["rain_mm"], deck["rain_trend"], "Annual rainfall", "mm", ui.PRECIP,
                                 "circle", y0, y1))
    with c2:
        with ui.card("cl_ext", "Extreme-rain days per district", "Heaviest 5% of rainy days; hatched bars = recent period 2020–2025"):
            yrs = np.array(deck["ext_years"])
            m = (yrs >= y0) & (yrs <= y1)
            recent = yrs[m] >= 2020
            fig = go.Figure(go.Bar(x=yrs[m], y=np.array(deck["ext_days"])[m], marker_color=np.where(recent, BLUE, CONTEXT),
                                   marker_pattern_shape=np.where(recent, "/", ""), marker_pattern_fgcolor="#FFFFFF",
                                   hovertemplate="%{x}: %{y:.1f} days<extra></extra>"))
            fig.update_layout(height=300, yaxis=dict(title="days per year"))
            ui.chart(fig)
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        with ui.card("cl_temp", "Average temperature", f"National mean, {y0}–{y1}; dashed line = linear trend"):
            ui.chart(trend_chart(deck["temp_years"], deck["temp_c"], _trend_line(deck["temp_years"], deck["temp_c"]),
                                 "Mean temperature", "°C", ui.TEMP, "diamond", y0, y1, fmt=".1f"))
            st.markdown(f"<p class='card-sub'>Trend {deck['temp_slope_decade']:+.2f} °C per decade; not statistically significant "
                        f"(p = {deck['temp_p']:.2f}).</p>", unsafe_allow_html=True)
    with c2:
        if d:
            r = D.loc[d]
            with ui.card("cl_dist", f"Climate record: {r.District}", f"2004–2025 · climate cluster {r.climate_grid_cluster}"):
                ui.table(pd.DataFrame({
                    "Measure": ["Mean daily rainfall", "Extreme-day threshold (P95)", "Extreme-rain days per year",
                                "Rainfall trend", "Recent vs baseline"],
                    "Value": [f"{r.mean_daily_rain_mm:.2f} mm", f"{r.p95_threshold_mm:.1f} mm", f"{r.extreme_days_per_yr:.1f}",
                              f"{r.trend_mm_per_yr:+.1f} mm / yr", f"{r.anomaly_pct:+.1f}%"]}), num=("Value",))
                same = D[D.climate_grid_cluster == r.climate_grid_cluster].District.tolist()
                if len(same) > 1:
                    st.markdown(f"<p class='card-sub'>Shares one satellite cell with: {', '.join(x for x in same if x != r.District)} "
                                "(identical rainfall values).</p>", unsafe_allow_html=True)
        else:
            with ui.card("cl_anom", "Rainfall anomaly by district", f"{scope_name()} · 2020–25 vs 2004–19 (%)"):
                t = sc.sort_values("anomaly_pct", ascending=False)
                st.dataframe(pd.DataFrame({"District": t.District, "Anomaly (%)": t.anomaly_pct.round(1),
                                           "Trend (mm/yr)": t.trend_mm_per_yr.round(1), "P95 (mm)": t.p95_threshold_mm.round(1)}),
                             hide_index=True, width="stretch", height=300)
    with ui.card("cl_find", "Findings"):
        ui.findings([
            ("F1", f"Rainfall is rising by about <b>{deck['rain_slope']} mm a year</b>; 2020–25 was about {deck['anomaly_median']:.0f}% wetter than 2004–19."),
            ("F2", f"Extreme-rain days rose from <b>{deck['ext_base']} to {deck['ext_recent']}</b> per district per year (+{deck['ext_pct']}%)."),
            ("F3", f"26 August 2026 was an ordinary rain day: about 20 mm fell in the corridor, below the {deck['nat_p95']} mm "
                   "extreme threshold. The trigger was ice, not rain."),
        ])
        st.caption("Only 45 of 77 districts have independent rainfall data; neighbours sharing one satellite cell show identical values.")


def page_vulnerability():
    ui.page_header("Exposure & Vulnerability", "Terrain and river hazard, the people and assets in their path, and how hard it is "
                   "to reach and treat them.", "Analysis")
    filter_bar(["province"], "vuln")
    sc = scope()
    t1, t2 = st.tabs(["Terrain and rivers", "Exposure and vulnerability"])
    with t1:
        c1, c2 = st.columns([1.5, 1], gap="medium")
        with c1:
            with ui.card("vu_scatter", "Ruggedness against river hazard",
                         "Each marker is a district. Triangles: top third on both measures." +
                         (f" Districts outside {scope_name()} are faded." if st.session_state.flt_province != ALL_PROV else "")):
                m = D.reset_index()
                insc = m.district_name.isin(sc.index)
                fig = go.Figure()
                for flag, name, sym, color, size in [(False, "Other districts", "circle", CONTEXT, 10),
                                                     (True, "Steep and on major rivers", "triangle-up", VERMILLION, 14)]:
                    part = m[m.steep_and_river == flag]
                    fig.add_scatter(x=part.ruggedness_score, y=part.river_score, mode="markers", name=name, text=part.District,
                                    marker=dict(symbol=sym, size=size, color=color, line=dict(color="white", width=1),
                                                opacity=np.where(insc[part.index], 1.0, 0.25)),
                                    hovertemplate="%{text}<br>Ruggedness %{x:.0f} · River %{y:.0f}<extra></extra>")
                fig.update_layout(height=430, xaxis_title="Terrain ruggedness (0–100)", yaxis_title="River size × proximity (0–100)")
                ui.chart(fig)
        with c2:
            with ui.card("vu_why", "Why the combination matters"):
                st.markdown("<p style='font-size:.92rem;line-height:1.6'>Landslides can dam rivers and release floods downstream; "
                            "ice collapses travel down steep valleys through river corridors. Steep terrain beside large rivers "
                            "produces cascading hazards.</p>", unsafe_allow_html=True)
                ui.findings([("F4", "Eight districts are in the top third for both: <b>" + ", ".join(deck["scatter"]["hot_names"]) + "</b>.")])
                st.caption("Ruggedness = spread of elevation within the district. The supplied slope columns are corrupted and not used.")
    with t2:
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            with ui.card("vu_exp", "Exposure", f"People and critical assets · top 10 in {scope_name()} (0–100)"):
                ui.chart(hbar(sc.exposure_score))
        with c2:
            with ui.card("vu_vul", "Vulnerability", f"Weak road access and hospital strain · top 10 in {scope_name()} (0–100)"):
                ui.chart(hbar(sc.vulnerability_score))
        with ui.card("vu_find", "Findings"):
            ui.findings([
                ("F5", "People and assets cluster in Kathmandu Valley, Pokhara (Kaski), the southern plains and hydropower hubs such as Dolakha (587 MW)."),
                ("F6", "Vulnerability peaks in remote mountain districts: very sparse roads and one or two mapped hospitals for more than 100,000 people."),
            ])
            ui.note("Poverty, age structure, disability, housing construction, early-warning coverage, footpaths and accurate rural "
                    "facility counts are not in the data and are stated as limitations.", "What vulnerability does not capture")


PRESETS = {
    "Landslide early-warning targets": lambda: list(D.risk_landslide.sort_values(ascending=False).head(8).index),
    "Ten most vulnerable districts": lambda: list(D.vulnerability_score.sort_values(ascending=False).head(10).index),
    "26 August corridor": lambda: CORRIDOR,
    "Custom selection": lambda: [],
}


def page_scenarios():
    ui.page_header("Scenarios", "Select districts, apply interventions, and compare risk before and after. Scores are recalculated on "
                   "the baseline scale so improvements are not hidden by re-normalisation.", "Analysis")
    c1, c2 = st.columns([1, 1.5], gap="medium")
    with c1:
        with ui.card("sc_ctrl", "Districts and interventions"):
            preset = st.selectbox("Preset", list(PRESETS))
            sel_names = st.multiselect("Selected districts", sorted(D.District), default=[n.title() for n in PRESETS[preset]()])
            sel = [n.upper() for n in sel_names]
            cov = st.slider("Early-warning coverage", 0, 100, 80, 5, format="%d%%") / 100
            eff = st.slider("Vulnerability reduction at full coverage", 0, 60, 30, 5, format="%d%%",
                            help="Assumption based on the Global Commission on Adaptation (2019): 24 hours' warning of a hazard "
                                 "can cut the ensuing damage by about 30%.") / 100
            road = st.slider("Increase in road density", 0, 100, 0, 10, format="+%d%%") / 100
            hosp = st.slider("Additional hospitals per district", 0, 5, 0)
            idx = st.selectbox("Hazard index", list(HAZARD), format_func=HAZARD.get, key="sc_idx")
    sc = rm.scenario(df, S, sel, cov, eff, road, hosp, METHOD)
    with c2:
        if not sel:
            ui.note("Select at least one district to run a scenario.")
            return
        cmp = pd.DataFrame({"Before": S.loc[sel, idx], "After": sc.loc[sel, idx]}).sort_values("Before", ascending=False)
        cmp["Change"] = cmp.After - cmp.Before
        new_rank = sc[idx].rank(ascending=False)
        ui.kpi_grid([
            {"icon": "activity", "label": "Average change", "value": f"{cmp.Change.mean():+.1f}", "unit": "points",
             "note": f"{HAZARD[idx]} risk, selected districts"},
            {"icon": "alert", "label": "Still in national top 10", "value": f"{int((new_rank.loc[sel] <= 10).sum())}",
             "unit": f"of {len(sel)}", "note": f"Before: {int((S[idx].rank(ascending=False).loc[sel] <= 10).sum())} of {len(sel)}"},
        ])
        with ui.card("sc_chart", f"{HAZARD[idx]} risk: before and after", "Solid grey = before; hatched blue = after"):
            ys = [i.title() for i in cmp.index]
            fig = go.Figure()
            fig.add_bar(y=ys, x=cmp.Before, orientation="h", name="Before", marker_color=CONTEXT,
                        text=[f"{v:.0f}" for v in cmp.Before], textposition="outside", cliponaxis=False,
                        hovertemplate="%{y} before: %{x:.1f}<extra></extra>")
            fig.add_bar(y=ys, x=cmp.After, orientation="h", name="After", marker_color=BLUE, marker_pattern_shape="/",
                        marker_pattern_fgcolor="#FFFFFF", text=[f"{v:.0f}" for v in cmp.After], textposition="outside",
                        cliponaxis=False, hovertemplate="%{y} after: %{x:.1f}<extra></extra>")
            fig.update_layout(barmode="group", height=max(320, 46 * len(cmp) + 70), margin=dict(r=36, t=30),
                              yaxis=dict(autorange="reversed", tickfont=dict(color=HEAD)), xaxis=dict(range=[0, 108]), bargroupgap=0.08)
            ui.chart(fig)
    with st.expander("Method and assumptions"):
        st.markdown(
            "- **Early warning** reduces a district's vulnerability score by *coverage × effectiveness* (default 80% × 30% = 24%).\n"
            "- **Roads** raise road density, lowering the access-vulnerability score; **hospitals** lower people per hospital.\n"
            "- Hazard and exposure do not change: early warning saves lives but does not stop the landslide.\n"
            "- Because risk is a geometric mean, a 24% cut in vulnerability lowers risk by about 9% (the cube root of 0.76).\n"
            "- Illustrative assumptions, not engineering estimates.")


def page_validation():
    ui.page_header("Validation", f"District scores compared with {len(events):,} BIPAD disaster records (2011–2026, duplicates removed). "
                   "Spearman rank correlation ρ: 0 = no relationship, 0.3 weak, 0.5 moderate, 0.7 and above strong.", "Analysis")
    if changed:
        ui.note("Correlations reflect custom model settings. Weights must not be tuned to improve the fit; use this only to test "
                "robustness. Reported results use the defaults.", "Custom settings active", warn=True)
    cor = rm.correlations(S, df)
    ui.kpi_grid([
        {"icon": "check", "label": "Landslide index vs landslides", "value": f"ρ = {cor.loc['risk_landslide', 'landslide_events']:.2f}",
         "note": "Terrain ruggedness is the strongest driver", "badge": ui.status_chip("good", "Validated · F8")},
        {"icon": "activity", "label": "Combined index vs all events", "value": f"ρ = {cor.loc['risk_combined', 'events_total']:.2f}",
         "note": "Driven mainly by its landslide component", "badge": ui.status_chip("mid", "Moderate · F7")},
        {"icon": "alert", "label": "Flood index vs floods", "value": f"ρ = {cor.loc['risk_flood', 'flood_events']:.2f}",
         "note": "Lowland floods are not captured", "badge": ui.status_chip("bad", "Not validated · F9")},
    ])
    c1, c2 = st.columns([1.2, 1], gap="medium")
    with c1:
        with ui.card("va_heat", "Correlation matrix", "Scores (rows) against recorded outcomes (columns); values printed in every cell"):
            nice = {"risk_combined": "Combined risk", "risk_flood": "Flood risk", "risk_landslide": "Landslide risk",
                    "combined_hazard": "Combined hazard", "flood_hazard": "Flood hazard", "landslide_hazard": "Landslide hazard",
                    "exposure_score": "Exposure", "vulnerability_score": "Vulnerability"}
            z = cor.rename(index=nice, columns={"events_total": "All events", "flood_events": "Floods",
                                                "landslide_events": "Landslides", "deaths": "Deaths"})
            fig = px.imshow(z, text_auto=".2f", color_continuous_scale=ui.DIVERGING, zmin=-0.7, zmax=0.7, aspect="auto")
            fig.update_traces(xgap=3, ygap=3, textfont=dict(size=13), hovertemplate="%{y} vs %{x}: ρ = %{z:.2f}<extra></extra>")
            fig.update_layout(height=430, margin=dict(t=8), coloraxis_colorbar=dict(title="ρ", thickness=10),
                              xaxis=dict(side="top", tickfont=dict(color=HEAD), ticks=""), yaxis=dict(tickfont=dict(color=HEAD)))
            ui.chart(fig)
    with c2:
        with ui.card("va_flood", "Why the flood index fails"):
            st.markdown(f"<p style='font-size:.92rem;line-height:1.6'>Most recorded floods are in <b>{', '.join(deck['top_flood_events']['labels'])}</b>: "
                        "mostly flat southern lowlands. The flood variables describe mountain rivers and rainfall; nothing in the data "
                        "captures floodplain flatness. Floods are also recorded more where people and roads are.</p>", unsafe_allow_html=True)
            fc = pd.Series(deck["flood_corr"])
            fig = go.Figure(go.Bar(x=fc.values, y=fc.index, orientation="h",
                                   marker_color=[BLUE if v < 0 else VERMILLION for v in fc.values],
                                   marker_pattern_shape=["" if v < 0 else "/" for v in fc.values], marker_pattern_fgcolor="#FFFFFF",
                                   text=[f"{v:+.2f}" for v in fc.values], textposition="outside", cliponaxis=False,
                                   hovertemplate="%{y}: ρ = %{x:+.2f}<extra></extra>"))
            fig.update_layout(height=230, margin=dict(t=10, l=8, r=30), xaxis=dict(range=[-0.5, 0.55], zeroline=True, zerolinecolor="#64748B",
                              title="Correlation with recorded floods (ρ)"), yaxis=dict(tickfont=dict(color=HEAD)))
            ui.chart(fig)
            st.caption("Negative = solid blue; positive = hatched orange-red. The sign is also printed on each bar.")
    with ui.card("va_decision", "Decision: separate flood and landslide indices"):
        st.markdown("<p style='font-size:.92rem;line-height:1.6;margin:0'>Floods and landslides strike different districts "
                    "(ρ = −0.13 between their counts). Each hazard-specific index outperforms the combined index on its own hazard, "
                    "and a single index would conceal that landslides are predicted well and floods poorly.</p>", unsafe_allow_html=True)
    c1, c2 = st.columns([1.3, 1], gap="medium")
    with c1:
        with ui.card("va_years", "Recorded events per year", "Hatched bars: 2024 onward"):
            yrs = np.array(deck["events_years"])
            new = yrs >= 2024
            fig = go.Figure(go.Bar(x=yrs, y=deck["events_n"], marker_color=np.where(new, BLUE, CONTEXT),
                                   marker_pattern_shape=np.where(new, "/", ""), marker_pattern_fgcolor="#FFFFFF",
                                   hovertemplate="%{x}: %{y:,} events<extra></extra>"))
            fig.update_layout(height=300, margin=dict(t=10), yaxis=dict(tickformat=",", title="events"))
            ui.chart(fig)
    with c2:
        with ui.card("va_blind", "Blind spots in the record"):
            late = events[(events.incident_date >= "2026-08-25") & events.district_name.isin(CORRIDOR)]
            cr = deck["corridor_rank"]
            ui.findings([
                ("F10", f"Events roughly quadrupled after 2023 while deaths per event fell from {deck['deaths_per_event'][0]} to "
                        f"{deck['deaths_per_event'][-1]}: more minor incidents are being logged, not more disasters."),
                ("F10", f"The 26 August collapse is missing: only {len(late)} minor corridor events from 25 August, with "
                        f"{int(late.deaths.sum())} deaths recorded."),
                ("F11", f"Glacial hazard is invisible to the data: Sindhupalchok ranks #{cr['Sindhupalchok']} and Rasuwa #{cr['Rasuwa']}."),
            ])


def page_investment():
    ui.page_header("Investment Plan", "USD 100 million, allocated by evidence. Where validation is strong, funds go to targeted "
                   "protection; where the analysis revealed blind spots, funds go to monitoring and data.", "Outputs")
    al = pd.DataFrame(deck["alloc"])
    al["Line"] = al.line.str.replace(r"^\S+\s", "", regex=True)
    act = int(al[al.line.str.split().str[0].isin(["1a", "1b", "3", "4"])].usd.sum())
    ui.kpi_grid([
        {"icon": "dollar", "label": "Targeted protection", "value": f"${act}M", "note": "Early warning, infrastructure, community preparedness"},
        {"icon": "layers", "label": "Closing blind spots", "value": f"${100 - act}M", "note": "Glacial and terrain monitoring, disaster and flood data"},
        {"icon": "map", "label": "Districts targeted", "value": f"{len({t.strip() for row in al.targets for t in row.split(',')})}",
         "unit": "of 77", "note": "Selected by explicit rules from the index"},
    ])
    c1, c2 = st.columns([1, 1.3], gap="medium")
    with c1:
        with ui.card("in_alloc", "Allocation", "USD million"):
            s = al.sort_values("usd")
            fig = go.Figure(go.Bar(x=s.usd, y=s.Line, orientation="h", marker_color=BLUE, text=[f"${v}M" for v in s.usd],
                                   textposition="outside", cliponaxis=False, hovertemplate="%{y}: $%{x}M<extra></extra>"))
            fig.update_layout(height=330, margin=dict(t=8, r=50), xaxis=dict(visible=False, range=[0, 26]),
                              yaxis=dict(tickfont=dict(color=HEAD, size=12.5)))
            ui.chart(fig)
    with c2:
        with ui.card("in_trace", "Traceability", "Each line, the findings it rests on, and its target districts"):
            ui.table(pd.DataFrame({"Line": al.Line, "USD": [f"${v}M" for v in al.usd], "Findings": al.findings,
                                   "Target districts": al.targets}), num=("USD",), code=("Findings",))
    with ui.card("in_effect", "Effect of the early-warning lines",
                 "Scenario defaults (80% coverage × 30% effectiveness) applied to the early-warning target districts"):
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


def page_data():
    ui.page_header("Data Explorer", "All 77 districts with their scores, risk bands and recorded disasters. Filter, search, sort and "
                   "download.", "Outputs")
    filter_bar(["province", "hazard"], "data")
    idx, sc = st.session_state.flt_hazard, scope()
    c1, c2 = st.columns([1.4, 1], gap="medium")
    with c1:
        q = st.text_input("Search districts", placeholder="Type a district name")
    with c2:
        bands = st.multiselect("Risk band", [b[1] for b in ui.BANDS], placeholder="All bands")
    t = sc.copy()
    if q:
        t = t[t.District.str.contains(q.strip(), case=False)]
    if bands:
        t = t[t[idx + "_band"].isin(bands)]
    t = t.sort_values(idx, ascending=False)
    table = pd.DataFrame({
        "District": t.District, "Province": t.province,
        f"{HAZARD[idx]} score": t[idx].round(1), "Risk band": t[idx + "_band"], "Rank": t[idx + "_rank"],
        "Combined": t.risk_combined.round(1), "Landslide": t.risk_landslide.round(1), "Flood": t.risk_flood.round(1),
        "Exposure": t.exposure_score.round(1), "Vulnerability": t.vulnerability_score.round(1),
        "Events": t.events_total.astype(int), "Deaths": t.deaths.astype(int),
        "Rain trend (mm/yr)": t.trend_mm_per_yr.round(1), "Rain anomaly (%)": t.anomaly_pct.round(1)})
    with ui.card("da_table", f"{len(table)} districts", f"{scope_name()} · sorted by {HAZARD[idx].lower()} score · "
                                                         "risk bands are labels on the 0–100 relative scores"):
        st.dataframe(table, hide_index=True, width="stretch", height=560, column_config={
            f"{HAZARD[idx]} score": st.column_config.ProgressColumn(f"{HAZARD[idx]} score (0–100)", min_value=0, max_value=100, format="%.0f"),
            "Events": st.column_config.NumberColumn("Events (2011–26)", format="%d"),
        })
        st.download_button("Download CSV", table.to_csv(index=False), "nepal_district_risk.csv", mime="text/csv")


def page_about():
    ui.page_header("About", "Method, assumptions, data sources and accessibility. The full analysis, including every data-cleaning "
                   "step, is documented in the project notebook.", "Reference")
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        with ui.card("ab_assume", "Key assumptions"):
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
        with ui.card("ab_bands", "Risk bands", "Display labels on the relative 0–100 scores; they are not absolute danger thresholds"):
            ui.table(pd.DataFrame({"Band": [b[1] for b in ui.BANDS],
                                   "Score": ["0–19", "20–39", "40–59", "60–79", "80–100"],
                                   "Card meter": ["1 of 5", "2 of 5", "3 of 5", "4 of 5", "5 of 5"]}))
        with ui.card("ab_limits", "Limitations"):
            st.markdown("- No poverty, age, housing or early-warning coverage data\n- OpenStreetMap undercounts rural facilities and roads\n"
                        "- One rainfall point per district on a coarse satellite grid; no district boundary file, so maps show points\n"
                        "- No floodplain or glacial-lake variables; no future climate projections\n"
                        "- Disaster record: reporting surge after 2023; the 26 August 2026 event is missing\n"
                        "- Correlation shows association, not causation")
    with c2:
        with ui.card("ab_sources", "Data sources"):
            st.markdown(
                "- **NASA POWER** (power.larc.nasa.gov): daily rainfall (PRECTOTCORR), temperature, humidity, wind\n"
                "- **HydroSHEDS**: elevation (15 arc-second DEM) and flow accumulation\n"
                "- **Nepal National Statistics Office**, Census 2021: population and density\n"
                "- **OpenStreetMap** (Overpass API): hospitals, schools, roads, bridges\n"
                "- **Wikipedia**, List of power stations in Nepal (9 March 2026): hydropower capacity\n"
                "- **geoBoundaries ADM2**: district representative points and area\n"
                "- **BIPAD Portal**, Government of Nepal: disaster incidents 2011–2026\n"
                "- Map basemap: Natural Earth national boundaries, rivers and lakes (via Plotly)")
        with ui.card("ab_a11y", "Accessibility"):
            st.markdown(
                "- Colour palette: Okabe–Ito (designed for colour-vision deficiency); maps use one-hue light-to-dark scales, readable by lightness alone\n"
                "- Risk levels always carry a **text label** (map hover, tables, badges) and a meter on cards, never colour alone\n"
                "- Series are separated by dash style, marker shape, hatching and direct labels\n"
                "- Text colours checked against WCAG contrast (≥ 4.5:1); chart marks ≥ 3:1 except orange, which is never used alone\n"
                "- Visible keyboard focus rings on all interactive elements\n"
                "- Not yet verified: full screen-reader testing and keyboard operation of map markers (the district filter is the keyboard alternative)")
        with ui.card("ab_gloss", "Glossary"):
            st.markdown("- **P95:** the value 95% of observations fall below\n"
                        "- **p-value:** the chance of a result this strong if no real effect existed\n"
                        "- **Spearman ρ:** rank correlation, from −1 to +1\n"
                        "- **Geometric mean:** multiply, then take the root; low if any component is low\n"
                        "- **Min-max scaling:** rescales to 0–100 (lowest district = 0)")


pg = st.navigation({
    "Dashboard": [st.Page(page_overview, title="Overview", icon=":material/dashboard:", default=True)],
    "Analysis": [st.Page(page_risk_mapping, title="Risk Mapping", icon=":material/map:", url_path="explorer"),
                 st.Page(page_climate, title="Climate Trends", icon=":material/rainy:", url_path="climate"),
                 st.Page(page_vulnerability, title="Exposure & Vulnerability", icon=":material/landscape:", url_path="terrain"),
                 st.Page(page_scenarios, title="Scenarios", icon=":material/tune:", url_path="scenarios"),
                 st.Page(page_validation, title="Validation", icon=":material/fact_check:", url_path="validation")],
    "Outputs": [st.Page(page_investment, title="Investment Plan", icon=":material/payments:", url_path="investment"),
                st.Page(page_data, title="Data Explorer", icon=":material/table_view:", url_path="data")],
    "Reference": [st.Page(page_about, title="About", icon=":material/info:", url_path="method")],
})
pg.run()
ui.footer()
