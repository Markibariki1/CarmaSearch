#!/usr/bin/env python3
"""
Cleanup script to remove unnecessary files from the complex system.

This script removes files that are no longer needed after creating the optimal system.
It keeps only the essential files for the streamlined system.
"""

import os
import shutil
from pathlib import Path

def main():
    """Remove unnecessary files and keep only the optimal system."""
    print("🧹 Cleaning up complex system files...")
    print("=" * 50)
    
    # Files to remove (complex system files)
    files_to_remove = [
        # Complex training scripts
        "src/train_ultra.py",
        "src/train_super_ensemble.py", 
        "src/train_refined.py",
        "src/train_ensemble.py",
        
        # Complex scoring systems
        "src/scoring_advanced.py",
        "src/production_system.py",
        "src/scalable_architecture.py",
        
        # Complex API
        "src/api_enhanced.py",
        
        # Complex detectors
        "src/advanced_description_detector.py",
        "src/placeholder_detector.py",
        "src/comprehensive_feature_engineer.py",
        
        # Complex scripts
        "scripts/train_ultra_model.py",
        "scripts/train_super_ensemble_model.py",
        "scripts/train_refined_model.py", 
        "scripts/train_ensemble_model.py",
        "scripts/comprehensive_attribute_analysis.py",
        "scripts/comprehensive_model_analysis.py",
        "scripts/comprehensive_test.py",
        "scripts/cost_optimized_deployment.py",
        "scripts/description_pattern_analysis.py",
        "scripts/model_quality_test.py",
        "scripts/performance_test.py",
        "scripts/process_and_score_data.py",
        "scripts/process_real_data.py",
        "scripts/process_with_repaint_detection.py",
        "scripts/proper_train_test_split.py",
        "scripts/realistic_deployment_plan.py",
        "scripts/test_complete_system.py",
        "scripts/test_repaint_detection.py",
        "scripts/train_model_with_proper_split.py",
        
        # Complex artifacts (keep only optimal)
        "artifacts/model_ultra.cbm",
        "artifacts/super_ensemble_catboost.cbm",
        "artifacts/super_ensemble_huber.pkl",
        "artifacts/super_ensemble_knn.pkl", 
        "artifacts/super_ensemble_lightgbm.pkl",
        "artifacts/super_ensemble_mlp.pkl",
        "artifacts/super_ensemble_random_forest.pkl",
        "artifacts/super_ensemble_scaler.pkl",
        "artifacts/super_ensemble_stacking.pkl",
        "artifacts/super_ensemble_svr.pkl",
        "artifacts/super_ensemble_theil_sen.pkl",
        "artifacts/super_ensemble_xgboost.pkl",
        "artifacts/ensemble_catboost.cbm",
        "artifacts/ensemble_elastic_net.pkl",
        "artifacts/ensemble_gradient_boosting.pkl",
        "artifacts/ensemble_random_forest.pkl",
        "artifacts/ensemble_ridge.pkl",
        "artifacts/ensemble_scaler.pkl",
        "artifacts/feature_meta_ultra.json",
        "artifacts/feature_meta_advanced.json",
        "artifacts/metrics_ultra.json",
        "artifacts/metrics_advanced.json",
        "artifacts/ensemble_meta.json",
        "artifacts/ensemble_metrics.json",
        "artifacts/super_ensemble_meta.json",
        "artifacts/super_ensemble_metrics.json",
        "artifacts/comprehensive_results.json",
        "artifacts/performance_results.json",
        "artifacts/refined_metrics.json",
        "artifacts/refined_model_meta.json",
        "artifacts/refined_model.cbm",
        
        # Complex documentation
        "CORRECTED_ANALYSIS.md",
        "MODEL_REFINEMENT_SUCCESS.md", 
        "PLACEHOLDER_PRICE_STRATEGY.md",
        "UPDATED_PLACEHOLDER_STRATEGY.md",
        "REPAINT_DETECTION_IMPLEMENTATION.md",
    ]
    
    # Directories to remove
    dirs_to_remove = [
        "catboost_info",  # CatBoost training logs
    ]
    
    removed_files = 0
    removed_dirs = 0
    
    # Remove files
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"✅ Removed: {file_path}")
                removed_files += 1
            except Exception as e:
                print(f"❌ Error removing {file_path}: {e}")
        else:
            print(f"⏭️  Not found: {file_path}")
    
    # Remove directories
    for dir_path in dirs_to_remove:
        if os.path.exists(dir_path):
            try:
                shutil.rmtree(dir_path)
                print(f"✅ Removed directory: {dir_path}")
                removed_dirs += 1
            except Exception as e:
                print(f"❌ Error removing directory {dir_path}: {e}")
        else:
            print(f"⏭️  Directory not found: {dir_path}")
    
    print(f"\n🎉 Cleanup completed!")
    print(f"   Removed {removed_files} files")
    print(f"   Removed {removed_dirs} directories")
    
    # Show what remains
    print(f"\n📁 Remaining optimal system files:")
    optimal_files = [
        "src/description_detector.py",
        "src/train_optimal.py", 
        "src/scoring_optimal.py",
        "src/api_optimal.py",
        "scripts/train_optimal_model.py",
        "scripts/precompute_scores_optimal.py",
        "scripts/serve_optimal_api.sh",
        "artifacts/model_optimal.cbm",
        "artifacts/feature_meta_optimal.json",
        "artifacts/metrics_optimal.json",
        "README_OPTIMAL.md"
    ]
    
    for file_path in optimal_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ⚠️  {file_path} (not created yet)")
    
    print(f"\n🚀 System is now streamlined and ready for production!")
    print(f"   Next steps:")
    print(f"   1. python scripts/train_optimal_model.py")
    print(f"   2. python scripts/precompute_scores_optimal.py") 
    print(f"   3. bash scripts/serve_optimal_api.sh")

if __name__ == "__main__":
    main()
