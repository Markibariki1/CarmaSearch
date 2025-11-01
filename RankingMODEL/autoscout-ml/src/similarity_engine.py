#!/usr/bin/env python3
"""
CARMA Similarity Engine - Weighted Feature Similarity Algorithm
Finds the most similar vehicles and best deals using content-based ranking
"""

import numpy as np
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class SimilarityEngine:
    """
    Weighted Feature Similarity Engine for vehicle comparison
    
    Calculates similarity based on multiple features:
    - Categorical matches (make, model, fuel, transmission)
    - Numerical distances (age, mileage, power)
    - Market-based deal scoring (price percentile)
    """
    
    # Default weights for similarity scoring
    DEFAULT_SIMILARITY_WEIGHTS = {
        'make_match': 0.30,        # 30% - Same manufacturer
        'model_match': 0.25,       # 25% - Same model
        'age_distance': 0.15,      # 15% - Year difference
        'mileage_distance': 0.15,  # 15% - Mileage difference
        'fuel_match': 0.10,        # 10% - Same fuel type
        'transmission_match': 0.05 # 5% - Same transmission
    }
    
    # Default weights for final score
    DEFAULT_FINAL_WEIGHTS = {
        'similarity': 0.70,  # 70% - How similar
        'deal_score': 0.30   # 30% - How good the deal
    }
    
    def __init__(
        self,
        similarity_weights: Dict[str, float] = None,
        final_weights: Dict[str, float] = None
    ):
        """
        Initialize the similarity engine
        
        Args:
            similarity_weights: Custom weights for similarity components
            final_weights: Custom weights for final score calculation
        """
        self.similarity_weights = similarity_weights or self.DEFAULT_SIMILARITY_WEIGHTS
        self.final_weights = final_weights or self.DEFAULT_FINAL_WEIGHTS
        
        # Validate weights sum to 1.0
        sim_sum = sum(self.similarity_weights.values())
        if not 0.99 <= sim_sum <= 1.01:
            logger.warning(f"Similarity weights sum to {sim_sum}, normalizing...")
            self._normalize_weights(self.similarity_weights)
        
        final_sum = sum(self.final_weights.values())
        if not 0.99 <= final_sum <= 1.01:
            logger.warning(f"Final weights sum to {final_sum}, normalizing...")
            self._normalize_weights(self.final_weights)
    
    @staticmethod
    def _normalize_weights(weights: Dict[str, float]) -> None:
        """Normalize weights to sum to 1.0"""
        total = sum(weights.values())
        for key in weights:
            weights[key] /= total
    
    def calculate_similarity(
        self,
        target: Dict[str, Any],
        candidate: Dict[str, Any]
    ) -> float:
        """
        Calculate similarity score between target and candidate vehicle
        
        Args:
            target: Target vehicle features
            candidate: Candidate vehicle features
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        scores = {}
        
        # Categorical matches (0 or 1)
        scores['make_match'] = 1.0 if self._safe_match(target, candidate, 'make') else 0.0
        scores['model_match'] = 1.0 if self._safe_match(target, candidate, 'model') else 0.0
        scores['fuel_match'] = 1.0 if self._safe_match(target, candidate, 'fuel_type') else 0.0
        scores['transmission_match'] = 1.0 if self._safe_match(target, candidate, 'transmission') else 0.0
        
        # Numerical distances (normalized to 0-1, where 1 = identical)
        scores['age_distance'] = self._calculate_age_similarity(target, candidate)
        scores['mileage_distance'] = self._calculate_mileage_similarity(target, candidate)
        
        # Calculate weighted similarity
        similarity = sum(
            self.similarity_weights.get(key, 0.0) * score
            for key, score in scores.items()
        )
        
        return max(0.0, min(1.0, similarity))
    
    def calculate_deal_score(
        self,
        candidate: Dict[str, Any],
        market_vehicles: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate deal score based on price percentile in market
        
        Args:
            candidate: Candidate vehicle to score
            market_vehicles: List of similar vehicles for market comparison
            
        Returns:
            Deal score between 0.0 (bad deal) and 1.0 (great deal)
        """
        if not market_vehicles or len(market_vehicles) < 3:
            return 0.5  # Neutral score if insufficient market data
        
        try:
            candidate_price = self._extract_price(candidate)
            if candidate_price is None or candidate_price <= 0:
                return 0.5
            
            # Extract prices from market vehicles
            market_prices = []
            for v in market_vehicles:
                price = self._extract_price(v)
                if price and price > 0:
                    market_prices.append(price)
            
            if len(market_prices) < 3:
                return 0.5
            
            # Calculate percentile (0 = cheapest, 1 = most expensive)
            percentile = self._calculate_percentile(candidate_price, market_prices)
            
            # Invert: lower price = better deal
            deal_score = 1.0 - percentile
            
            # Adjust for mileage (lower mileage at same price = better deal)
            mileage_adjustment = self._calculate_mileage_adjustment(candidate, market_vehicles)
            adjusted_score = deal_score * (1.0 + 0.1 * mileage_adjustment)
            
            return max(0.0, min(1.0, adjusted_score))
            
        except Exception as e:
            logger.error(f"Error calculating deal score: {e}")
            return 0.5
    
    def calculate_final_score(
        self,
        similarity_score: float,
        deal_score: float
    ) -> float:
        """
        Calculate final ranking score
        
        Args:
            similarity_score: Similarity score (0-1)
            deal_score: Deal quality score (0-1)
            
        Returns:
            Final score between 0.0 and 1.0
        """
        final = (
            self.final_weights['similarity'] * similarity_score +
            self.final_weights['deal_score'] * deal_score
        )
        return max(0.0, min(1.0, final))
    
    def rank_candidates(
        self,
        target: Dict[str, Any],
        candidates: List[Dict[str, Any]],
        market_vehicles: List[Dict[str, Any]] = None
    ) -> List[Tuple[Dict[str, Any], float, float, float]]:
        """
        Rank all candidate vehicles
        
        Args:
            target: Target vehicle
            candidates: List of candidate vehicles
            market_vehicles: Optional market data for deal scoring
            
        Returns:
            List of tuples: (vehicle, similarity_score, deal_score, final_score)
            Sorted by final_score descending
        """
        if market_vehicles is None:
            market_vehicles = candidates
        
        results = []
        
        for candidate in candidates:
            try:
                # Calculate scores
                similarity = self.calculate_similarity(target, candidate)
                deal_score = self.calculate_deal_score(candidate, market_vehicles)
                final_score = self.calculate_final_score(similarity, deal_score)
                
                results.append((candidate, similarity, deal_score, final_score))
                
            except Exception as e:
                logger.error(f"Error ranking candidate {candidate.get('id', 'unknown')}: {e}")
                continue
        
        # Sort by final score (descending)
        results.sort(key=lambda x: x[3], reverse=True)
        
        return results
    
    # ==================== Helper Methods ====================
    
    @staticmethod
    def _safe_match(target: Dict, candidate: Dict, key: str) -> bool:
        """Safely check if two values match"""
        target_val = target.get(key)
        candidate_val = candidate.get(key)
        
        if target_val is None or candidate_val is None:
            return False
        
        # Case-insensitive string comparison
        if isinstance(target_val, str) and isinstance(candidate_val, str):
            return target_val.strip().lower() == candidate_val.strip().lower()
        
        return target_val == candidate_val
    
    @staticmethod
    def _extract_year(vehicle: Dict[str, Any]) -> int:
        """Extract year from vehicle data"""
        # Try multiple fields
        year = vehicle.get('year')
        if year and isinstance(year, (int, float)):
            return int(year)
        
        # Try parsing from first_registration_raw
        first_reg = vehicle.get('first_registration_raw')
        if first_reg:
            try:
                year_str = str(first_reg)[:4]
                return int(year_str)
            except (ValueError, TypeError):
                pass
        
        return None
    
    @staticmethod
    def _extract_mileage(vehicle: Dict[str, Any]) -> float:
        """Extract mileage from vehicle data"""
        mileage = vehicle.get('mileage_km')
        if mileage is not None:
            try:
                return float(mileage)
            except (ValueError, TypeError):
                pass
        return None
    
    @staticmethod
    def _extract_price(vehicle: Dict[str, Any]) -> float:
        """Extract price from vehicle data"""
        price = vehicle.get('price') or vehicle.get('price_eur')
        if price is None:
            return None
        
        try:
            # Handle string prices like "€15,000"
            if isinstance(price, str):
                import re
                price_clean = re.sub(r'[^0-9,.]', '', price).replace(',', '.')
                return float(price_clean) if price_clean else None
            return float(price)
        except (ValueError, TypeError):
            return None
    
    def _calculate_age_similarity(
        self,
        target: Dict[str, Any],
        candidate: Dict[str, Any],
        max_diff: int = 10
    ) -> float:
        """
        Calculate similarity based on age difference
        
        Args:
            target: Target vehicle
            candidate: Candidate vehicle
            max_diff: Maximum year difference (normalized to 0)
            
        Returns:
            Similarity score 0.0 to 1.0
        """
        target_year = self._extract_year(target)
        candidate_year = self._extract_year(candidate)
        
        if target_year is None or candidate_year is None:
            return 0.5  # Neutral score if data missing
        
        age_diff = abs(target_year - candidate_year)
        
        # Normalize: 0 years diff = 1.0, max_diff years = 0.0
        similarity = max(0.0, 1.0 - (age_diff / max_diff))
        
        return similarity
    
    def _calculate_mileage_similarity(
        self,
        target: Dict[str, Any],
        candidate: Dict[str, Any],
        max_diff: float = 100000
    ) -> float:
        """
        Calculate similarity based on mileage difference
        
        Args:
            target: Target vehicle
            candidate: Candidate vehicle
            max_diff: Maximum mileage difference in km (normalized to 0)
            
        Returns:
            Similarity score 0.0 to 1.0
        """
        target_mileage = self._extract_mileage(target)
        candidate_mileage = self._extract_mileage(candidate)
        
        if target_mileage is None or candidate_mileage is None:
            return 0.5  # Neutral score if data missing
        
        mileage_diff = abs(target_mileage - candidate_mileage)
        
        # Normalize: 0 km diff = 1.0, max_diff km = 0.0
        similarity = max(0.0, 1.0 - (mileage_diff / max_diff))
        
        return similarity
    
    @staticmethod
    def _calculate_percentile(value: float, values: List[float]) -> float:
        """
        Calculate percentile rank of value in list of values
        
        Args:
            value: Value to rank
            values: List of values for comparison
            
        Returns:
            Percentile between 0.0 and 1.0
        """
        if not values:
            return 0.5
        
        # Count how many values are less than or equal to target
        count_below = sum(1 for v in values if v < value)
        
        # Percentile = proportion below
        percentile = count_below / len(values)
        
        return percentile
    
    def _calculate_mileage_adjustment(
        self,
        candidate: Dict[str, Any],
        market_vehicles: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate mileage adjustment factor
        
        Returns:
            Adjustment factor between -1.0 and 1.0
            Positive = lower than average mileage (better deal)
            Negative = higher than average mileage (worse deal)
        """
        candidate_mileage = self._extract_mileage(candidate)
        if candidate_mileage is None:
            return 0.0
        
        # Get market average mileage
        market_mileages = [
            self._extract_mileage(v)
            for v in market_vehicles
            if self._extract_mileage(v) is not None
        ]
        
        if not market_mileages:
            return 0.0
        
        avg_mileage = np.mean(market_mileages)
        
        if avg_mileage == 0:
            return 0.0
        
        # Calculate deviation
        deviation = (avg_mileage - candidate_mileage) / avg_mileage
        
        # Clip to [-1, 1]
        return max(-1.0, min(1.0, deviation))


# ==================== Convenience Functions ====================

def create_engine(
    similarity_weights: Dict[str, float] = None,
    final_weights: Dict[str, float] = None
) -> SimilarityEngine:
    """
    Create a new similarity engine instance
    
    Args:
        similarity_weights: Optional custom similarity weights
        final_weights: Optional custom final score weights
        
    Returns:
        Configured SimilarityEngine instance
    """
    return SimilarityEngine(
        similarity_weights=similarity_weights,
        final_weights=final_weights
    )


def quick_rank(
    target: Dict[str, Any],
    candidates: List[Dict[str, Any]],
    top_k: int = 10
) -> List[Dict[str, Any]]:
    """
    Quick ranking using default engine
    
    Args:
        target: Target vehicle
        candidates: Candidate vehicles
        top_k: Number of top results to return
        
    Returns:
        Top K ranked vehicles with scores
    """
    engine = create_engine()
    ranked = engine.rank_candidates(target, candidates)
    
    # Format results
    results = []
    for vehicle, similarity, deal_score, final_score in ranked[:top_k]:
        result = vehicle.copy()
        result['similarity_score'] = round(similarity, 3)
        result['deal_score'] = round(deal_score, 3)
        result['final_score'] = round(final_score, 3)
        results.append(result)
    
    return results


# ==================== Testing ====================

if __name__ == "__main__":
    # Example usage
    target_vehicle = {
        'id': 'target-123',
        'make': 'BMW',
        'model': '3 Series',
        'year': 2020,
        'mileage_km': 50000,
        'price': 25000,
        'fuel_type': 'Petrol',
        'transmission': 'Automatic'
    }
    
    candidate_vehicles = [
        {
            'id': 'candidate-1',
            'make': 'BMW',
            'model': '3 Series',
            'year': 2020,
            'mileage_km': 45000,
            'price': 24000,
            'fuel_type': 'Petrol',
            'transmission': 'Automatic'
        },
        {
            'id': 'candidate-2',
            'make': 'BMW',
            'model': '3 Series',
            'year': 2019,
            'mileage_km': 60000,
            'price': 22000,
            'fuel_type': 'Petrol',
            'transmission': 'Automatic'
        },
        {
            'id': 'candidate-3',
            'make': 'BMW',
            'model': '5 Series',
            'year': 2020,
            'mileage_km': 50000,
            'price': 30000,
            'fuel_type': 'Diesel',
            'transmission': 'Automatic'
        }
    ]
    
    # Test the engine
    print("Testing Similarity Engine...\n")
    results = quick_rank(target_vehicle, candidate_vehicles, top_k=3)
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['make']} {result['model']} ({result['year']})")
        print(f"   Price: €{result['price']:,} | Mileage: {result['mileage_km']:,} km")
        print(f"   Similarity: {result['similarity_score']:.2%}")
        print(f"   Deal Score: {result['deal_score']:.2%}")
        print(f"   Final Score: {result['final_score']:.2%}")
        print()

