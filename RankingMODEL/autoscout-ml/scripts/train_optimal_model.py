#!/usr/bin/env python3
"""
Train the optimal AutoScout24 ML model.

This script trains the streamlined model that achieves 5.2% MAPE with minimal complexity.
It uses only the 26 optimal features and incorporates description-based scoring.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.train_optimal import train_optimal_model

def main():
    """Train the optimal model."""
    print("🚀 Training Optimal AutoScout24 ML Model")
    print("=" * 50)
    
    # Paths
    clean_parquet = "data/clean.parquet"
    model_path = "artifacts/model_optimal.cbm"
    artifacts_dir = "artifacts"
    
    # Check if clean data exists
    if not os.path.exists(clean_parquet):
        print(f"❌ Error: {clean_parquet} not found")
        print("Please run prepare_data.py first to create clean data")
        return 1
    
    # Create artifacts directory if it doesn't exist
    os.makedirs(artifacts_dir, exist_ok=True)
    
    try:
        # Train the optimal model
        model, feature_meta, metrics = train_optimal_model(
            clean_parquet, 
            model_path, 
            artifacts_dir
        )
        
        print("\n✅ Training completed successfully!")
        print(f"📊 Model Performance:")
        print(f"   MAPE: {metrics['cv_mape']:.1f}% ± {metrics['cv_mape_std']:.1f}%")
        print(f"   RMSE: {metrics['cv_rmse_log']:.4f} ± {metrics['cv_rmse_log_std']:.4f}")
        print(f"   Features: {metrics['features_used']}")
        print(f"   Training samples: {metrics['training_samples']}")
        
        print(f"\n📁 Files created:")
        print(f"   Model: {model_path}")
        print(f"   Metadata: {artifacts_dir}/feature_meta_optimal.json")
        print(f"   Metrics: {artifacts_dir}/metrics_optimal.json")
        
        print(f"\n🎯 Next steps:")
        print(f"   1. Run: python scripts/precompute_scores_optimal.py")
        print(f"   2. Start API: python -m src.api_optimal")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error during training: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
