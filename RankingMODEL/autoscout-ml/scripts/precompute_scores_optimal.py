#!/usr/bin/env python3
"""
Precompute scores for all vehicles using the optimal model.

This script processes all vehicles with the optimal model and description-based adjustments.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
from src.scoring_optimal import load_optimal_model, process_with_description_detection

def main():
    """Precompute scores for all vehicles."""
    print("🚀 Precomputing Scores with Optimal Model")
    print("=" * 50)
    
    # Paths
    clean_parquet = "data/clean.parquet"
    model_path = "artifacts/model_optimal.cbm"
    feature_meta_path = "artifacts/feature_meta_optimal.json"
    output_path = "data/precomputed_optimal.parquet"
    
    # Check if required files exist
    if not os.path.exists(clean_parquet):
        print(f"❌ Error: {clean_parquet} not found")
        print("Please run prepare_data.py first")
        return 1
    
    if not os.path.exists(model_path):
        print(f"❌ Error: {model_path} not found")
        print("Please run train_optimal_model.py first")
        return 1
    
    if not os.path.exists(feature_meta_path):
        print(f"❌ Error: {feature_meta_path} not found")
        print("Please run train_optimal_model.py first")
        return 1
    
    try:
        # Load data
        print("📊 Loading clean data...")
        df = pd.read_parquet(clean_parquet)
        print(f"   Loaded {len(df)} vehicles")
        
        # Load model
        print("🤖 Loading optimal model...")
        model, meta = load_optimal_model(model_path, feature_meta_path)
        print(f"   Model loaded with {len(meta['features'])} features")
        
        # Process with description detection
        print("🔍 Processing with description-based adjustments...")
        df_processed = process_with_description_detection(df, model, meta)
        
        # Save results
        print(f"💾 Saving results to {output_path}...")
        df_processed.to_parquet(output_path, index=False)
        
        # Print summary
        print("\n✅ Precomputation completed successfully!")
        print(f"📊 Results summary:")
        print(f"   Total vehicles: {len(df_processed)}")
        print(f"   Average price: €{df_processed['price_eur'].mean():,.0f}")
        print(f"   Average predicted price: €{df_processed['price_hat'].mean():,.0f}")
        
        if 'description_total_impact' in df_processed.columns:
            desc_impact = df_processed['description_total_impact']
            print(f"   Description adjustments applied: {(desc_impact != 0).sum()}")
            print(f"   Average description impact: {desc_impact.mean():.3f}")
            print(f"   Max positive impact: {desc_impact.max():.3f}")
            print(f"   Max negative impact: {desc_impact.min():.3f}")
        
        print(f"\n📁 Output file: {output_path}")
        print(f"🎯 Next step: Start API with 'python -m src.api_optimal'")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error during precomputation: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
