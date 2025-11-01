#!/usr/bin/env python3
"""
Flexible data preparation script for both AutoScout24 and Mobile.de data.

This script can handle different data formats from both sites and produces
the same standardized output format for consistent scoring.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import numpy as np
import re
from src.prepare import build

def detect_data_source(df):
    """Detect if data is from AutoScout24 or Mobile.de based on column names."""
    columns = set(df.columns)
    
    # AutoScout24 columns
    autoscout_columns = {
        'tracking_price', 'mileageInKmRaw', 'tracking_firstRegistration',
        'vehicle_make', 'vehicle_model', 'vehicle_fuel', 'vehicle_transmission',
        'bodyType', 'rawPowerInKw', 'rawDisplacementInCCM', 'location_zip',
        'vehicle_modelVersionInput'
    }
    
    # Mobile.de columns (common patterns)
    mobile_columns = {
        'price', 'mileage', 'first_registration', 'make', 'model', 'fuel',
        'transmission', 'body_type', 'power', 'displacement', 'zip', 'version'
    }
    
    autoscout_match = len(autoscout_columns.intersection(columns))
    mobile_match = len(mobile_columns.intersection(columns))
    
    if autoscout_match > mobile_match:
        return 'autoscout24'
    elif mobile_match > 0:
        return 'mobile_de'
    else:
        return 'unknown'

def prepare_mobile_de_data(input_xlsx, output_parquet):
    """Prepare Mobile.de data with column mapping."""
    print(f"Loading Mobile.de data from {input_xlsx}...")
    df = pd.read_excel(input_xlsx, sheet_name="Sheet1")
    
    print(f"Original dataset shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    # Map Mobile.de columns to standard format
    column_mapping = {}
    
    # Try to find matching columns
    for col in df.columns:
        col_lower = col.lower()
        
        # Price columns
        if 'price' in col_lower and 'tracking_price' not in column_mapping:
            column_mapping['tracking_price'] = col
        elif 'preis' in col_lower and 'tracking_price' not in column_mapping:
            column_mapping['tracking_price'] = col
            
        # Mileage columns
        if 'mileage' in col_lower and 'mileageInKmRaw' not in column_mapping:
            column_mapping['mileageInKmRaw'] = col
        elif 'kilometer' in col_lower and 'mileageInKmRaw' not in column_mapping:
            column_mapping['mileageInKmRaw'] = col
            
        # Year columns
        if 'first_registration' in col_lower and 'tracking_firstRegistration' not in column_mapping:
            column_mapping['tracking_firstRegistration'] = col
        elif 'erstzulassung' in col_lower and 'tracking_firstRegistration' not in column_mapping:
            column_mapping['tracking_firstRegistration'] = col
        elif 'jahr' in col_lower and 'tracking_firstRegistration' not in column_mapping:
            column_mapping['tracking_firstRegistration'] = col
            
        # Make columns
        if col_lower == 'make' and 'vehicle_make' not in column_mapping:
            column_mapping['vehicle_make'] = col
        elif 'marke' in col_lower and 'vehicle_make' not in column_mapping:
            column_mapping['vehicle_make'] = col
            
        # Model columns
        if col_lower == 'model' and 'vehicle_model' not in column_mapping:
            column_mapping['vehicle_model'] = col
        elif 'modell' in col_lower and 'vehicle_model' not in column_mapping:
            column_mapping['vehicle_model'] = col
            
        # Fuel columns
        if col_lower == 'fuel' and 'vehicle_fuel' not in column_mapping:
            column_mapping['vehicle_fuel'] = col
        elif 'kraftstoff' in col_lower and 'vehicle_fuel' not in column_mapping:
            column_mapping['vehicle_fuel'] = col
            
        # Transmission columns
        if col_lower == 'transmission' and 'vehicle_transmission' not in column_mapping:
            column_mapping['vehicle_transmission'] = col
        elif 'getriebe' in col_lower and 'vehicle_transmission' not in column_mapping:
            column_mapping['vehicle_transmission'] = col
            
        # Body type columns
        if 'body_type' in col_lower and 'bodyType' not in column_mapping:
            column_mapping['bodyType'] = col
        elif 'karosserie' in col_lower and 'bodyType' not in column_mapping:
            column_mapping['bodyType'] = col
            
        # Power columns
        if col_lower == 'power' and 'rawPowerInKw' not in column_mapping:
            column_mapping['rawPowerInKw'] = col
        elif 'leistung' in col_lower and 'rawPowerInKw' not in column_mapping:
            column_mapping['rawPowerInKw'] = col
            
        # Displacement columns
        if col_lower == 'displacement' and 'rawDisplacementInCCM' not in column_mapping:
            column_mapping['rawDisplacementInCCM'] = col
        elif 'hubraum' in col_lower and 'rawDisplacementInCCM' not in column_mapping:
            column_mapping['rawDisplacementInCCM'] = col
            
        # ZIP columns
        if col_lower == 'zip' and 'location_zip' not in column_mapping:
            column_mapping['location_zip'] = col
        elif 'plz' in col_lower and 'location_zip' not in column_mapping:
            column_mapping['location_zip'] = col
            
        # Version columns
        if col_lower == 'version' and 'vehicle_modelVersionInput' not in column_mapping:
            column_mapping['vehicle_modelVersionInput'] = col
        elif 'ausstattung' in col_lower and 'vehicle_modelVersionInput' not in column_mapping:
            column_mapping['vehicle_modelVersionInput'] = col
    
    # Add required columns that might be missing
    required_columns = [
        'id', 'url', 'tracking_price', 'mileageInKmRaw', 'tracking_firstRegistration',
        'vehicle_make', 'vehicle_model', 'vehicle_fuel', 'vehicle_transmission',
        'bodyType', 'rawPowerInKw', 'rawDisplacementInCCM', 'location_zip',
        'vehicle_modelVersionInput'
    ]
    
    # Create standardized dataframe
    standardized_df = pd.DataFrame()
    
    # Copy mapped columns
    for std_col, orig_col in column_mapping.items():
        if orig_col in df.columns:
            standardized_df[std_col] = df[orig_col]
        else:
            standardized_df[std_col] = np.nan
    
    # Add id and url if they exist
    if 'id' in df.columns:
        standardized_df['id'] = df['id']
    else:
        standardized_df['id'] = range(len(df))
    
    if 'url' in df.columns:
        standardized_df['url'] = df['url']
    else:
        standardized_df['url'] = ''
    
    # Add description if it exists
    desc_columns = ['description', 'vehicle_description', 'ad_description', 'beschreibung']
    for desc_col in desc_columns:
        if desc_col in df.columns:
            standardized_df['description'] = df[desc_col]
            break
    else:
        standardized_df['description'] = ''
    
    # Fill missing required columns with defaults
    for col in required_columns:
        if col not in standardized_df.columns:
            if col in ['id', 'url']:
                standardized_df[col] = range(len(df)) if col == 'id' else ''
            else:
                standardized_df[col] = np.nan
    
    print(f"Column mapping: {column_mapping}")
    print(f"Standardized dataset shape: {standardized_df.shape}")
    
    # Save temporary file and use existing build function
    temp_file = "temp_standardized.xlsx"
    standardized_df.to_excel(temp_file, index=False)
    
    try:
        # Use existing build function
        build(temp_file, output_parquet)
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file):
            os.remove(temp_file)

def main():
    """Main entry point for flexible data preparation."""
    if len(sys.argv) != 3:
        print("Usage: python prepare_data_flexible.py <input_xlsx> <output_parquet>")
        print("Example: python prepare_data_flexible.py data/mobile_de_sample_data.xlsx data/clean.parquet")
        return 1
    
    input_xlsx = sys.argv[1]
    output_parquet = sys.argv[2]
    
    if not os.path.exists(input_xlsx):
        print(f"❌ Error: Input file {input_xlsx} not found")
        return 1
    
    try:
        # Load data to detect source
        print("🔍 Detecting data source...")
        df_sample = pd.read_excel(input_xlsx, sheet_name="Sheet1", nrows=5)
        data_source = detect_data_source(df_sample)
        
        print(f"📊 Detected data source: {data_source}")
        
        if data_source == 'autoscout24':
            print("🚀 Processing AutoScout24 data...")
            build(input_xlsx, output_parquet)
        elif data_source == 'mobile_de':
            print("🚀 Processing Mobile.de data...")
            prepare_mobile_de_data(input_xlsx, output_parquet)
        else:
            print("⚠️  Unknown data source, trying AutoScout24 format...")
            build(input_xlsx, output_parquet)
        
        print(f"✅ Data preparation completed!")
        print(f"📁 Output saved to: {output_parquet}")
        print(f"🎯 Next step: python scripts/train_optimal_model.py")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error during data preparation: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
