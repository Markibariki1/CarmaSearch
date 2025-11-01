import numpy as np
import pandas as pd
import json
from catboost import CatBoostRegressor
from .features import make_hard_filter, numeric_similarity, jaccard
from .description_detector import DescriptionDetector

def load_optimal_model(model_path, feature_meta_path):
    """Load the optimal CatBoost model and feature metadata."""
    model = CatBoostRegressor()
    model.load_model(model_path)
    
    with open(feature_meta_path) as f:
        meta = json.load(f)
    
    return model, meta

def predict_price_optimal(df, model, meta):
    """Predict price_hat for all rows using the optimal model."""
    X = df[meta["features"]].copy()
    
    # Fill NaN values in categorical features
    for cat_col in meta["categoricals"]:
        if cat_col in X.columns:
            X[cat_col] = X[cat_col].fillna("Unknown")
    
    # Fill NaN values in numeric features
    for col in meta["numeric_features"]:
        if col in X.columns:
            X[col] = X[col].fillna(X[col].median())
    
    log_pred = model.predict(X)
    return np.exp(log_pred)

def compute_deal_score(price_hat, price):
    """Compute deal score: positive = underpriced, negative = overpriced."""
    return np.clip((price_hat - price) / price_hat, -0.5, 0.5)

def compute_deal_score_with_description(price_hat, price, description_impact=0.0):
    """
    Compute deal score accounting for description-based adjustments.
    
    Args:
        price_hat: Predicted price
        price: Actual price
        description_impact: Description-based price impact (-0.2 to +0.2)
    
    Returns:
        Adjusted deal score
    """
    # Adjust price_hat based on description impact
    adjusted_price_hat = price_hat * (1.0 + description_impact)
    return np.clip((adjusted_price_hat - price) / adjusted_price_hat, -0.5, 0.5)

def rank_comparables_optimal(df_with_preds, qid, top=20, description_col='description'):
    """
    Rank comparable vehicles using the optimal scoring system with description adjustments.
    
    Args:
        df_with_preds: DataFrame with price predictions
        qid: Query vehicle ID
        top: Number of top results to return
        description_col: Name of description column
    
    Returns:
        DataFrame with ranked comparable vehicles
    """
    df = df_with_preds.copy()
    
    # Get query vehicle
    qrow_mask = df["id"] == qid
    if not qrow_mask.any():
        raise ValueError(f"Vehicle with id {qid} not found")
    qrow = df[qrow_mask].iloc[0]
    
    # Apply hard filter
    candidates = make_hard_filter(df[df["id"] != qid], qrow)
    
    if len(candidates) == 0:
        return pd.DataFrame()
    
    # Initialize description detector
    detector = DescriptionDetector()
    
    # Get description impacts for query and candidates
    q_desc_impact = 0.0
    if description_col in df.columns and pd.notna(qrow[description_col]):
        q_desc_result = detector.detect_description_impact(qrow[description_col])
        q_desc_impact = q_desc_result['total_impact']
    
    # Compute description impacts for candidates
    candidate_desc_impacts = []
    if description_col in candidates.columns:
        for _, row in candidates.iterrows():
            if pd.notna(row[description_col]):
                desc_result = detector.detect_description_impact(row[description_col])
                candidate_desc_impacts.append(desc_result['total_impact'])
            else:
                candidate_desc_impacts.append(0.0)
    else:
        candidate_desc_impacts = [0.0] * len(candidates)
    
    # Compute similarity scores
    candidates['s_spec'] = candidates.apply(
        lambda row: numeric_similarity(qrow, row, ['age_years', 'mileage_km', 'power_kw', 'displ_cc']), 
        axis=1
    )
    
    candidates['s_trim'] = candidates.apply(
        lambda row: jaccard(qrow, row, ['make', 'model', 'fuel_group', 'transmission_group', 'body_group']), 
        axis=1
    )
    
    # Compute deal scores with description adjustments
    candidates['deal_score'] = [
        compute_deal_score_with_description(
            row['price_hat'], 
            row['price_eur'], 
            candidate_desc_impacts[i]
        ) for i, (_, row) in enumerate(candidates.iterrows())
    ]
    
    # Price-based bonus/penalty
    def compute_price_bonus_penalty(irow):
        rel = (qrow["price_eur"] - irow["price_eur"]) / qrow["price_eur"]
        
        if rel > 0:  # Candidate is cheaper
            bonus = min(rel * 0.8, 0.25)  # Cap at 25%
        else:  # Candidate is more expensive
            penalty = min(-rel * 0.6, 0.3)  # Cap at 30%
            bonus = -penalty
        
        return bonus
    
    candidates['price_bonus'] = candidates.apply(compute_price_bonus_penalty, axis=1)
    
    # Final scoring with optimal weights
    candidates['score'] = (
        0.5 * candidates['s_spec'] +           # Specification similarity (50%)
        0.3 * candidates['deal_score'] +       # Deal score (30%)
        0.1 * candidates['s_trim'] +           # Trim similarity (10%)
        0.1 * candidates['price_bonus']        # Price bonus/penalty (10%)
    )
    
    # Sort by score (descending), then by price (ascending) as tie-breaker
    result = candidates.sort_values(["score", "price_eur"], ascending=[False, True]).head(top)
    
    # Add description impact information to results
    if description_col in candidates.columns:
        result['description_impact'] = [candidate_desc_impacts[i] for i in result.index]
        result['query_description_impact'] = q_desc_impact
    
    return result

def process_with_description_detection(df, model, meta, description_col='description'):
    """
    Process dataframe with description-based price adjustments.
    
    Args:
        df: Input dataframe
        model: Trained CatBoost model
        meta: Feature metadata
        description_col: Name of description column
    
    Returns:
        DataFrame with predictions and description adjustments
    """
    # Get base predictions
    df_processed = df.copy()
    df_processed['price_hat'] = predict_price_optimal(df, model, meta)
    
    # Initialize description detector
    detector = DescriptionDetector()
    
    # Apply description detection if description column exists
    if description_col in df.columns:
        print("Applying description-based adjustments...")
        df_processed = detector.process_dataframe(df_processed, description_col)
        
        # Apply description adjustments to price predictions
        df_processed['price_hat_adjusted'] = df_processed.apply(
            lambda row: detector.apply_description_adjustment(
                row['price_hat'], 
                row.get('description_total_impact', 0.0)
            ), axis=1
        )
        
        # Update deal scores with description adjustments
        df_processed['deal_score'] = df_processed.apply(
            lambda row: compute_deal_score_with_description(
                row['price_hat'], 
                row['price_eur'], 
                row.get('description_total_impact', 0.0)
            ), axis=1
        )
        
        print(f"Applied description adjustments to {len(df_processed)} vehicles")
        print(f"Average description impact: {df_processed['description_total_impact'].mean():.3f}")
    else:
        print("No description column found, using base predictions only")
        df_processed['price_hat_adjusted'] = df_processed['price_hat']
        df_processed['deal_score'] = compute_deal_score(
            df_processed['price_hat'].values, 
            df_processed['price_eur'].values
        )
    
    return df_processed

def test_optimal_scoring():
    """Test the optimal scoring system."""
    print("Testing optimal scoring system...")
    
    # Create sample data
    sample_data = {
        'id': ['1', '2', '3', '4', '5'],
        'price_eur': [25000, 23000, 27000, 22000, 26000],
        'age_years': [3, 4, 2, 5, 3],
        'mileage_km': [50000, 60000, 30000, 80000, 45000],
        'power_kw': [150, 140, 160, 130, 155],
        'displ_cc': [2000, 1800, 2200, 1600, 2000],
        'make': ['BMW', 'BMW', 'BMW', 'BMW', 'BMW'],
        'model': ['320i', '320i', '320i', '320i', '320i'],
        'fuel_group': ['Benzin', 'Benzin', 'Benzin', 'Benzin', 'Benzin'],
        'transmission_group': ['Manuell', 'Manuell', 'Manuell', 'Manuell', 'Manuell'],
        'body_group': ['Sedan', 'Sedan', 'Sedan', 'Sedan', 'Sedan'],
        'description': [
            'BMW 320i, unfallfrei, checkheftgepflegt, wie neu',
            'BMW 320i, vorschaden, wartungsstau, gebrauchsspuren',
            'BMW 320i, neu lackiert, technisch einwandfrei',
            'BMW 320i, totalschaden wiederaufgebaut, motor läuft unrund',
            'BMW 320i, gepflegt, normale gebrauchsspuren'
        ]
    }
    
    df = pd.DataFrame(sample_data)
    
    # Mock model and meta (for testing)
    class MockModel:
        def predict(self, X):
            return np.log(df['price_eur'].values)  # Simple mock
    
    mock_model = MockModel()
    mock_meta = {
        'features': ['age_years', 'mileage_km', 'power_kw', 'displ_cc', 'make', 'model', 'fuel_group', 'transmission_group', 'body_group'],
        'categoricals': ['make', 'model', 'fuel_group', 'transmission_group', 'body_group'],
        'numeric_features': ['age_years', 'mileage_km', 'power_kw', 'displ_cc']
    }
    
    # Test processing with description detection
    df_processed = process_with_description_detection(df, mock_model, mock_meta)
    
    print("\nTest Results:")
    print("=" * 80)
    for _, row in df_processed.iterrows():
        print(f"ID: {row['id']}")
        print(f"  Price: €{row['price_eur']:,}")
        print(f"  Predicted: €{row['price_hat']:,.0f}")
        print(f"  Adjusted: €{row['price_hat_adjusted']:,.0f}")
        print(f"  Description Impact: {row.get('description_total_impact', 0.0):+.1%}")
        print(f"  Deal Score: {row['deal_score']:+.3f}")
        print(f"  Description: {row['description']}")
        print()

if __name__ == "__main__":
    test_optimal_scoring()
