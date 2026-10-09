"""Reusable data-cleaning toolkit for pandas DataFrames.

Each function does one check or one fix, so a cleaning process can be built step by step
and every step can be shown and logged. Copy this file into any project and import it:

    from cleaning_toolkit import *
"""
import numpy as np
import pandas as pd


class CleaningLog:
    """Records every cleaning action (what, where, how many rows) so the process is auditable."""

    def __init__(self):
        self.rows = []

    def add(self, dataset, step, action, rows_before=None, rows_after=None, note=""):
        removed = None if rows_before is None or rows_after is None else rows_before - rows_after
        self.rows.append({"dataset": dataset, "step": step, "action": action, "rows_before": rows_before,
                          "rows_after": rows_after, "rows_removed": removed, "note": note})

    def to_frame(self):
        # "Int64" (capital I) = whole numbers that may be blank, so counts don't turn into decimals
        return pd.DataFrame(self.rows).astype({"rows_before": "Int64", "rows_after": "Int64", "rows_removed": "Int64"})


def profile(df):
    """One row per column: data type, missing values, distinct values, min/max and an example value."""
    out = pd.DataFrame({
        "dtype": df.dtypes.astype(str),
        "missing": df.isna().sum(),
        "missing_pct": (df.isna().mean() * 100).round(1),
        "unique": df.nunique(),
    })
    num = df.select_dtypes("number")
    out["min"] = num.min()
    out["max"] = num.max()
    out["example"] = df.apply(lambda s: s.dropna().iloc[0] if s.notna().any() else None)
    return out


def standardize_text(s, case="upper", aliases=None):
    """Trim spaces, collapse repeated spaces, set the case, then map known alternative spellings."""
    s = s.astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
    s = {"upper": s.str.upper(), "lower": s.str.lower(), "title": s.str.title()}[case]
    return s.replace(aliases or {})


def key_mismatches(reference, others, col):
    """Compare a join key across tables. Any value listed would be silently lost in a join."""
    ref = set(reference[col].dropna())
    rows = []
    for name, df in others.items():
        vals = set(df[col].dropna())
        rows.append({"table": name, "missing_from_table": sorted(ref - vals), "not_in_reference": sorted(vals - ref)})
    return pd.DataFrame(rows)


def sentinel_counts(df, sentinels=(-999, -9999, -99, 9999)):
    """Count placeholder codes that some systems use instead of a blank (NASA POWER uses -999)."""
    num = df.select_dtypes("number")
    counts = num.isin(sentinels).sum()
    return counts[counts > 0]


def useless_columns(df):
    """Columns that carry no information: entirely empty, or the same value in every row."""
    empty = [c for c in df.columns if df[c].isna().all()]
    constant = [c for c in df.columns if c not in empty and df[c].nunique(dropna=False) == 1]
    return {"empty": empty, "constant": constant}


def exact_duplicates(df, subset=None):
    """All rows that are repeated exactly (on every column, or only on `subset`)."""
    return df[df.duplicated(subset=subset, keep=False)]


def probable_duplicates(df, ignore):
    """Rows identical in every column except those in `ignore` (e.g. an auto-generated ID).
    Returns every member of each group, sorted so the copies sit next to each other."""
    cols = [c for c in df.columns if c not in ignore]
    return df[df.duplicated(subset=cols, keep=False)].sort_values(cols)


def range_violations(df, rules):
    """rules = {column: (lowest allowed, highest allowed)}; None = no limit. Counts rows outside the range."""
    out = {}
    for col, (lo, hi) in rules.items():
        bad = pd.Series(False, index=df.index)
        if lo is not None:
            bad |= df[col] < lo
        if hi is not None:
            bad |= df[col] > hi
        out[col] = int(bad.sum())
    return pd.Series(out, name="rows_outside_range")


def date_gaps(df, group, date_col, freq="D"):
    """For each group: first date, last date, dates present, dates expected, and how many are missing."""
    g = df.groupby(group)[date_col].agg(["min", "max", "count"])
    g["expected"] = [len(pd.date_range(a, b, freq=freq)) for a, b in zip(g["min"], g["max"])]
    g["missing_dates"] = g["expected"] - g["count"]
    return g


def identical_series(df, group, date_col, value):
    """Give each group a fingerprint of its whole time series; groups with equal fingerprints are identical."""
    wide = df.pivot(index=date_col, columns=group, values=value)
    fingerprint = wide.apply(lambda s: pd.util.hash_pandas_object(s, index=False).sum())
    return fingerprint.rank(method="dense").astype(int).rename("series_id")


def utc_to_local(s, tz):
    """Convert timestamps stored in UTC (without a timezone label) into local time for `tz`."""
    return pd.to_datetime(s).dt.tz_localize("UTC").dt.tz_convert(tz).dt.tz_localize(None)
