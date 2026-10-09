"""Risk model used by the Streamlit app.

Mirrors the notebook (nepal_risk_assessment.ipynb, Phases 2-5) but takes the weights as
parameters, so the app can recompute scores live. With default parameters it reproduces
the notebook's scores exactly (checked by `python risk_model.py`).
"""
import os
import numpy as np
import pandas as pd
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "nepal_climate_capstone_student_data")
OUT = os.path.join(ROOT, "outputs")

EXPO_VARS = ["population", "population_density_per_km2", "hydropower_capacity_mw", "hospital_count", "school_count"]
DEFAULT_EXPO_W = {"population": 0.30, "population_density_per_km2": 0.20, "hydropower_capacity_mw": 0.20,
                  "hospital_count": 0.15, "school_count": 0.15}


def minmax(s):
    return (s - s.min()) / (s.max() - s.min()) * 100


def scale_like(x, ref):
    """Min-max x using the min/max of a reference (baseline) series, so scenario values stay comparable."""
    return ((x - ref.min()) / (ref.max() - ref.min()) * 100).clip(0, 100)


def load_inputs():
    """Raw district indicators + climate and event summaries produced by the notebook."""
    raw = pd.read_csv(os.path.join(DATA, "exposure_vulnerability.csv"))
    raw["district_name"] = raw["district_name"].str.upper()
    raw = raw.set_index("district_name")
    nb = pd.read_csv(os.path.join(OUT, "district_risk_scores.csv"), index_col=0)
    pts = pd.read_csv(os.path.join(OUT, "district_points.csv"), index_col=0)
    keep_nb = ["climate_grid_cluster", "mean_daily_rain_mm", "p95_threshold_mm", "extreme_days_per_yr",
               "nat_extreme_days_per_yr", "trend_mm_per_yr", "anomaly_pct", "events_total", "flood_events",
               "landslide_events", "deaths", "steep_and_river"]
    df = raw.join(nb[keep_nb]).join(pts)
    df["pop_per_hospital"] = df.population / df.hospital_count.replace(0, np.nan)
    df["pop_per_hospital"] = df.pop_per_hospital.fillna(df.pop_per_hospital.max())
    return df


def compute(df, expo_w=None, rain_share=0.5, access_share=0.5, method="geometric"):
    """Hazard, exposure, vulnerability and risk scores (0-100) for every district.

    rain_share:   weight of the heavy-rain score inside flood/landslide hazard (notebook: 0.5)
    access_share: weight of road access inside vulnerability (notebook: 0.5; rest = hospital strain)
    method:       'geometric' (notebook) or 'additive' (0.4 H + 0.3 E + 0.3 V)
    """
    expo_w = expo_w or DEFAULT_EXPO_W
    s = pd.DataFrame(index=df.index)
    # Hazard (Phase 2 + rain from Phase 1)
    s["rain_score"] = minmax(df.nat_extreme_days_per_yr)
    s["ruggedness_score"] = minmax(df.elevation_std_m)
    size = minmax(np.log10(df.flow_acc_max))
    prox = minmax(-df.dist_to_river_mean_km)
    s["river_score"] = minmax(np.sqrt(size * prox))
    s["flood_hazard"] = minmax(rain_share * s.rain_score + (1 - rain_share) * s.river_score)
    s["landslide_hazard"] = minmax(rain_share * s.rain_score + (1 - rain_share) * s.ruggedness_score)
    s["combined_hazard"] = minmax((s.rain_score + s.river_score + s.ruggedness_score) / 3)
    # Exposure (Phase 3)
    logs = np.log1p(df[EXPO_VARS]).apply(minmax)
    total = sum(expo_w.values())
    s["exposure_score"] = minmax(sum(logs[v] * w / total for v, w in expo_w.items()))
    # Vulnerability (Phase 4)
    s["access_vuln_score"] = 100 - minmax(np.log(df.road_density_km_per_km2))
    s["health_vuln_score"] = minmax(np.log(df.pop_per_hospital))
    s["vulnerability_score"] = minmax(access_share * s.access_vuln_score + (1 - access_share) * s.health_vuln_score)
    # Risk (Phase 5)
    for name, h in [("risk_combined", "combined_hazard"), ("risk_flood", "flood_hazard"), ("risk_landslide", "landslide_hazard")]:
        s[name + "_raw"] = combine(s[h], s.exposure_score, s.vulnerability_score, method)
        s[name] = minmax(s[name + "_raw"])
    return s


def combine(h, e, v, method="geometric"):
    if method == "additive":
        return 0.4 * h + 0.3 * e + 0.3 * v
    return np.cbrt(h.clip(lower=1) * e.clip(lower=1) * v.clip(lower=1))


def scenario(df, base, districts, ews_coverage=0.0, ews_effect=0.30, road_increase=0.0, extra_hospitals=0,
             method="geometric"):
    """Apply interventions to selected districts and re-score them on the BASELINE scale.

    ews_coverage:    share of people (0-1) reached by early warning in the selected districts
    ews_effect:      vulnerability reduction at full coverage (default 30%, see app text for source)
    road_increase:   proportional increase in road density (0.2 = +20%)
    extra_hospitals: hospitals added per selected district
    Scores are rescaled with the baseline min/max so a district's improvement is not hidden by re-normalisation.
    """
    d = df.copy()
    sel = d.index.isin(districts)
    d.loc[sel, "road_density_km_per_km2"] *= (1 + road_increase)
    d.loc[sel, "hospital_count"] += extra_hospitals
    d["pop_per_hospital"] = d.population / d.hospital_count.replace(0, np.nan)
    d["pop_per_hospital"] = d.pop_per_hospital.fillna(df.pop_per_hospital.max())

    base_access_raw = np.log(df.road_density_km_per_km2)
    base_health_raw = np.log(df.pop_per_hospital)
    access = 100 - scale_like(np.log(d.road_density_km_per_km2), base_access_raw)
    health = scale_like(np.log(d.pop_per_hospital), base_health_raw)
    base_mix = (base["access_vuln_score"] + base["health_vuln_score"]) / 2
    v = scale_like((access + health) / 2, base_mix)
    v = v.where(~sel, v * (1 - ews_coverage * ews_effect))

    out = pd.DataFrame(index=df.index)
    out["vulnerability_score"] = v
    for name, h in [("risk_combined", "combined_hazard"), ("risk_flood", "flood_hazard"), ("risk_landslide", "landslide_hazard")]:
        raw = combine(base[h], base.exposure_score, v, method)
        out[name] = scale_like(raw, base[name + "_raw"])
    return out


def correlations(scores, df):
    rows = {}
    for s in ["risk_combined", "risk_flood", "risk_landslide", "combined_hazard", "flood_hazard", "landslide_hazard",
              "exposure_score", "vulnerability_score"]:
        rows[s] = {o: stats.spearmanr(scores[s], df[o])[0] for o in ["events_total", "flood_events", "landslide_events", "deaths"]}
    return pd.DataFrame(rows).T


if __name__ == "__main__":
    df = load_inputs()
    s = compute(df)
    nb = pd.read_csv(os.path.join(OUT, "district_risk_scores.csv"), index_col=0)
    cols = ["rain_score", "river_score", "ruggedness_score", "flood_hazard", "landslide_hazard", "combined_hazard",
            "exposure_score", "vulnerability_score", "risk_combined", "risk_flood", "risk_landslide"]
    diff = (s[cols] - nb.loc[s.index, cols]).abs().max()
    print("max abs difference vs notebook:\n", diff.round(4))
    assert (diff < 0.01).all(), "app model does not match notebook"
    sc = scenario(df, s, [], 0)
    assert (sc.risk_combined - s.risk_combined).abs().max() < 1e-6, "empty scenario must equal baseline"
    print("OK: app model reproduces notebook scores; empty scenario = baseline")
