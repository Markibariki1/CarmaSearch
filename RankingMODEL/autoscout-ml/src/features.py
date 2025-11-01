import pandas as pd
import numpy as np
import re
from typing import Set, Tuple, List

def tokenize_trim(s: str) -> Set[str]:
    """Extract tokens from trim string for similarity matching."""
    if not isinstance(s, str):
        return set()
    toks = re.split(r"[^0-9a-zA-Z]+", s.lower())
    return set([t for t in toks if len(t) >= 2])

def build_feature_df(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, List[str], List[str]]:
    """Build feature matrix and target vector for training."""
    CAT = ["make", "model", "fuel_group", "transmission_group", "body_group", "zip3"]
    FEATS = ["age_years", "mileage_km", "mileage_per_year", "power_kw", "displ_cc"] + CAT
    
    # Ensure all features exist
    missing_feats = [f for f in FEATS if f not in df.columns]
    if missing_feats:
        raise ValueError(f"Missing features: {missing_feats}")
    
    X = df[FEATS].copy()
    y = np.log(df["price_eur"].clip(lower=1.0))
    
    return X, y, CAT, FEATS

def make_hard_filter(df: pd.DataFrame, qrow: pd.Series) -> pd.DataFrame:
    """Apply hard filtering criteria to find comparable vehicles."""
    mask = (
        (df["make"] == qrow["make"]) &
        (df["model"] == qrow["model"]) &
        (df["body_group"] == qrow["body_group"]) &
        (df["fuel_group"] == qrow["fuel_group"]) &
        (df["year"].sub(qrow["year"]).abs() <= 2) &
        (df["power_kw"].between(0.75 * qrow["power_kw"], 1.25 * qrow["power_kw"])) &
        (df["mileage_km"].between(0.7 * qrow["mileage_km"], 1.3 * qrow["mileage_km"]))
    )
    
    # Optional locality filter - only apply if we have candidates without it
    if pd.notna(qrow["zip3"]):
        candidates_with_zip = df[mask & (df["zip3"] == qrow["zip3"])]
        if len(candidates_with_zip) > 0:
            mask &= (df["zip3"] == qrow["zip3"])
    
    return df[mask]

def numeric_similarity(qrow: pd.Series, irow: pd.Series) -> float:
    """Compute numeric similarity between query and candidate vehicle."""
    d_year = abs(irow["year"] - qrow["year"]) / 2.0
    d_power = abs(irow["power_kw"] - qrow["power_kw"]) / (0.25 * max(1.0, qrow["power_kw"]))
    d_mileage = abs(irow["mileage_km"] - qrow["mileage_km"]) / (0.30 * max(1.0, qrow["mileage_km"]))
    d_displ = abs(irow["displ_cc"] - qrow["displ_cc"]) / (0.20 * max(1.0, qrow["displ_cc"]))
    
    return np.exp(-(1.0 * d_year**2 + 1.0 * d_power**2 + 0.8 * d_mileage**2 + 0.5 * d_displ**2))

def jaccard(a, b) -> float:
    """Compute Jaccard similarity between two sets."""
    # Convert to sets if they're not already
    if not isinstance(a, set):
        a = set(a) if a is not None else set()
    if not isinstance(b, set):
        b = set(b) if b is not None else set()
    
    if not a and not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union > 0 else 0.0
