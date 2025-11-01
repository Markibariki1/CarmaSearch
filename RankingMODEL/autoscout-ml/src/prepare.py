import pandas as pd
import numpy as np
import re
import json
import math

FUEL_MAP = {
    "Benzin": "Petrol",
    "Diesel": "Diesel", 
    "Autogas (LPG)": "LPG",
    "Erdgas (CNG)": "CNG",
    "Sonstige": "Other"
}

TRANS_MAP = {
    "Schaltgetriebe": "Manual",
    "Automatik": "Automatic", 
    "Halbautomatik": "Semi"
}

BODY_MAP = {
    "Limousine": "Sedan",
    "Kombi": "Wagon",
    "Kleinwagen": "Hatch", 
    "Coupé": "Coupe",
    "Cabrio": "Cabrio",
    "SUV/Geländewagen/Pickup": "SUV",
    "Transporter": "Van",
    "Van/Kleinbus": "Van",
    "Pritschenwagen": "Pickup",
    "Sonstige": "Other"
}

def tokenize_trim(s):
    """Extract tokens from trim string for similarity matching."""
    if not isinstance(s, str):
        return set()
    toks = re.split(r"[^0-9a-zA-Z]+", s.lower())
    return set([t for t in toks if len(t) >= 2])

def parse_year(s):
    """Parse year from MM-YYYY format."""
    if not isinstance(s, str):
        return np.nan
    m = re.match(r"(\d{2})-(\d{4})", s)
    if not m:
        return np.nan
    return int(m.group(2))

def zip3(z):
    """Extract first 3 digits from ZIP code."""
    if not isinstance(z, str):
        return np.nan
    m = re.match(r"(\d{3})", z)
    return m.group(1) if m else np.nan

def parse_price(price_str):
    """Parse price from string format like '€ 100'."""
    if pd.isna(price_str):
        return np.nan
    if isinstance(price_str, (int, float)):
        return float(price_str)
    
    # Extract numeric value from string
    match = re.search(r'€\s*(\d+)', str(price_str))
    if match:
        return float(match.group(1))
    return np.nan

def build(input_xlsx, output_parquet):
    """Build cleaned dataset with canonical features."""
    print(f"Loading data from {input_xlsx}...")
    df = pd.read_excel(input_xlsx, sheet_name="Sheet1")
    
    print(f"Original dataset shape: {df.shape}")
    
    # Build canonical features
    out = pd.DataFrame({
        "id": df["id"],
        "url": df["url"],
        "price_eur": df["tracking_price"].astype(float),
        "mileage_km": df["mileageInKmRaw"].astype(float),
        "year": df["tracking_firstRegistration"].map(parse_year),
        "make": df["vehicle_make"].astype(str),
        "model": df["vehicle_model"].astype(str),
        "fuel_group": df["vehicle_fuel"].map(FUEL_MAP),
        "transmission_group": df["vehicle_transmission"].map(TRANS_MAP),
        "body_group": df["bodyType"].map(BODY_MAP),
        "power_kw": df["rawPowerInKw"].astype(float),
        "displ_cc": df["rawDisplacementInCCM"],  # keep float/nan
        "zip3": df["location_zip"].map(zip3),
        "trim_tokens": df["vehicle_modelVersionInput"].map(tokenize_trim)
    })
    
    # Add description column if it exists
    if "description" in df.columns:
        out["description"] = df["description"].astype(str)
    elif "vehicle_description" in df.columns:
        out["description"] = df["vehicle_description"].astype(str)
    elif "ad_description" in df.columns:
        out["description"] = df["ad_description"].astype(str)
    else:
        # Create empty description column if none exists
        out["description"] = ""
    
    # Handle missing price_eur by parsing price/price_text columns
    missing_price_mask = out["price_eur"].isna()
    if missing_price_mask.sum() > 0:
        print(f"Parsing {missing_price_mask.sum()} missing prices from price/price_text columns...")
        out.loc[missing_price_mask, "price_eur"] = df.loc[missing_price_mask, "price"].map(parse_price)
    
    # Derived features
    out["age_years"] = (2025 - out["year"]).clip(lower=0)
    out["mileage_per_year"] = (out["mileage_km"] / out["age_years"].replace(0, np.nan)).fillna(out["mileage_km"])
    
    # Impute displacement: median by model, then global median
    print("Imputing displacement values...")
    med_model = out.groupby(["make", "model"])["displ_cc"].transform(lambda s: s.fillna(s.median()))
    out["displ_cc"] = out["displ_cc"].fillna(med_model).fillna(out["displ_cc"].median())
    
    # Drop rows with missing required fields
    req = ["price_eur", "mileage_km", "power_kw", "year", "make", "model", "fuel_group", "transmission_group", "body_group"]
    print(f"Dropping rows with missing required fields: {req}")
    
    initial_rows = len(out)
    out = out.dropna(subset=req)
    final_rows = len(out)
    print(f"Dropped {initial_rows - final_rows} rows ({initial_rows - final_rows}/{initial_rows:.1%})")
    
    print(f"Final dataset shape: {out.shape}")
    print(f"Saving to {output_parquet}...")
    out.to_parquet(output_parquet, index=False)
    
    # Print summary statistics
    print("\nDataset Summary:")
    print(f"Price range: €{out['price_eur'].min():.0f} - €{out['price_eur'].max():.0f}")
    print(f"Mileage range: {out['mileage_km'].min():.0f} - {out['mileage_km'].max():.0f} km")
    print(f"Year range: {out['year'].min()} - {out['year'].max()}")
    print(f"Power range: {out['power_kw'].min():.0f} - {out['power_kw'].max():.0f} kW")
    print(f"Unique makes: {out['make'].nunique()}")
    print(f"Unique models: {out['model'].nunique()}")

def main(input_xlsx, output_parquet):
    """Main entry point for data preparation."""
    build(input_xlsx, output_parquet)

