"""
Hybrid ranking engine for CARMA comparable vehicle search.

Combines hard-filtered retrieval with weighted similarity and deal scoring.
Uses only the Python standard library so it runs in lightweight Flask deployments.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import median
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _safe_lower(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip().lower()
    return str(value).lower()


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _exp_similarity(delta: Optional[float], tolerance: float, fallback: float = 0.5) -> float:
    if delta is None:
        return fallback
    if tolerance <= 0:
        return 1.0 if abs(delta) < 1e-9 else 0.0
    return float(math.exp(-abs(delta) / tolerance))


@dataclass(frozen=True)
class FilterLevel:
    """Encapsulates fallback filter configuration."""

    year_delta: int
    mileage_pct: float
    price_pct: float
    power_pct: float
    require_body_type: bool = True
    require_transmission: bool = True
    require_color: bool = False


class HybridRankingEngine:
    """
    Scores comparable vehicles using a blend of specification similarity,
    deal quality, and preference boosts.
    """

    def __init__(
        self,
        similarity_weight: float = 0.6,
        deal_weight: float = 0.35,
        preference_weight: float = 0.05,
    ) -> None:
        total = similarity_weight + deal_weight + preference_weight
        if total <= 0:
            raise ValueError("Ranking weights must sum to a positive value")

        self.weights = {
            "similarity": similarity_weight / total,
            "deal": deal_weight / total,
            "preference": preference_weight / total,
        }

        # Internal weights for similarity components (sum to 1)
        self.similarity_component_weights = {
            "age": 0.2,
            "mileage": 0.25,
            "power": 0.15,
            "body": 0.1,
            "transmission": 0.1,
            "fuel": 0.1,
            "color": 0.05,
            "drivetrain": 0.05,
        }

    # --------------------------------------------------------------------- #
    # Similarity scoring
    # --------------------------------------------------------------------- #
    def _score_similarity(
        self,
        target: Dict[str, Any],
        candidate: Dict[str, Any],
    ) -> Tuple[float, Dict[str, float]]:
        weights = self.similarity_component_weights
        components: Dict[str, float] = {}

        # Age similarity (years)
        t_year = target.get("year")
        c_year = candidate.get("year")
        age_delta = None
        if isinstance(t_year, (int, float)) and isinstance(c_year, (int, float)):
            age_delta = abs(t_year - c_year)

        components["age"] = _exp_similarity(age_delta, tolerance=2.5)

        # Mileage similarity
        t_mileage = target.get("mileage_km")
        c_mileage = candidate.get("mileage_km")
        mileage_delta = None
        tol_mileage = 15000.0
        if isinstance(t_mileage, (int, float)) and isinstance(c_mileage, (int, float)):
            mileage_delta = abs(t_mileage - c_mileage)
            tol_mileage = max(5000.0, abs(t_mileage) * 0.35)
        components["mileage"] = _exp_similarity(mileage_delta, tolerance=tol_mileage)

        # Power similarity
        t_power = target.get("power_kw")
        c_power = candidate.get("power_kw")
        power_delta = None
        if isinstance(t_power, (int, float)) and isinstance(c_power, (int, float)):
            power_delta = abs(t_power - c_power)
        components["power"] = _exp_similarity(power_delta, tolerance=8.0)

        # Body type match
        components["body"] = self._binary_match(target.get("body_type"), candidate.get("body_type"))

        # Transmission match
        components["transmission"] = self._binary_match(
            target.get("transmission"),
            candidate.get("transmission"),
        )

        # Fuel match
        components["fuel"] = self._binary_match(target.get("fuel_type"), candidate.get("fuel_type"))

        # Exterior color (soft bonus)
        components["color"] = self._soft_color_match(target.get("color"), candidate.get("color"))

        # Drivetrain (AWD/FWD/RWD) bonus if available
        components["drivetrain"] = self._binary_match(
            target.get("drive_train"), candidate.get("drive_train"), default=0.6
        )

        similarity = 0.0
        weight_sum = 0.0
        for key, weight in weights.items():
            component_score = components.get(key)
            if component_score is None:
                continue
            similarity += component_score * weight
            weight_sum += weight

        similarity = similarity / weight_sum if weight_sum else 0.0
        return clamp(similarity, 0.0, 1.0), components

    @staticmethod
    def _binary_match(
        target_value: Optional[Any],
        candidate_value: Optional[Any],
        default: float = 0.5,
    ) -> float:
        if target_value is None or candidate_value is None:
            return default
        return 1.0 if _safe_lower(target_value) == _safe_lower(candidate_value) else 0.0

    @staticmethod
    def _soft_color_match(
        target_color: Optional[str],
        candidate_color: Optional[str],
    ) -> float:
        if not target_color or not candidate_color:
            return 0.6
        if _safe_lower(target_color) == _safe_lower(candidate_color):
            return 1.0
        return 0.75

    # --------------------------------------------------------------------- #
    # Deal scoring
    # --------------------------------------------------------------------- #
    def _score_deal(
        self,
        candidate: Dict[str, Any],
        market_prices: Iterable[float],
        target_price: Optional[float],
        mileage_comparison: Tuple[Optional[float], Optional[float]],
    ) -> Tuple[float, Dict[str, float]]:
        price = candidate.get("price")
        if not isinstance(price, (int, float)) or price <= 0:
            return 0.5, {"price_position": 0.5, "percentile": 0.5, "mileage_adjustment": 0.0}

        prices = [p for p in market_prices if isinstance(p, (int, float)) and p > 0]
        if len(prices) < 3:
            prices = [price]

        market_median = float(median(prices))
        market_median = market_median if market_median > 0 else price

        # Relative savings against median
        relative_savings = (market_median - price) / market_median
        price_position_score = 0.5 + clamp(relative_savings * 1.4, -0.5, 0.5)

        # Percentile within market
        prices_sorted = sorted(prices)
        num_below = sum(1 for p in prices_sorted if p <= price)
        percentile = num_below / len(prices_sorted)
        percentile_score = 1.0 - percentile

        # Mileage adjustment
        target_mileage, candidate_mileage = mileage_comparison
        mileage_adjustment = 0.0
        if isinstance(target_mileage, (int, float)) and isinstance(candidate_mileage, (int, float)):
            if candidate_mileage < target_mileage:
                diff_pct = (target_mileage - candidate_mileage) / max(target_mileage, 1)
                mileage_adjustment = clamp(diff_pct * 0.4, 0.0, 0.12)
            else:
                diff_pct = (candidate_mileage - target_mileage) / max(target_mileage, 1)
                mileage_adjustment = -clamp(diff_pct * 0.3, 0.0, 0.12)

        # Target anchor (encourage lower than target price)
        anchor_score = 0.0
        if isinstance(target_price, (int, float)) and target_price > 0:
            anchor_diff = (target_price - price) / target_price
            anchor_score = clamp(anchor_diff * 1.2, -0.25, 0.25)

        raw = (
            0.55 * price_position_score
            + 0.35 * percentile_score
            + 0.1 * (0.5 + anchor_score)
        )
        adjusted = clamp(raw + mileage_adjustment, 0.0, 1.0)

        return adjusted, {
            "price_position": price_position_score,
            "percentile": percentile_score,
            "mileage_adjustment": mileage_adjustment,
            "median_price": market_median,
        }

    # --------------------------------------------------------------------- #
    # Preference scoring: currently color + drivetrain soft boosts
    # --------------------------------------------------------------------- #
    def _score_preferences(
        self,
        target: Dict[str, Any],
        candidate: Dict[str, Any],
    ) -> Tuple[float, Dict[str, float]]:
        score = 0.0
        components: Dict[str, float] = {}
        weight_sum = 0.0

        color_component = 1.0 if self._binary_match(target.get("preferred_color"), candidate.get("color"), default=0.0) else 0.0
        components["color_priority"] = color_component
        score += color_component * 0.6
        weight_sum += 0.6

        drivetrain_pref = target.get("preferred_drivetrain")
        if drivetrain_pref:
            drivetrain_component = self._binary_match(drivetrain_pref, candidate.get("drive_train"), default=0.0)
            components["drivetrain_priority"] = drivetrain_component
            score += drivetrain_component * 0.4
            weight_sum += 0.4

        if weight_sum == 0:
            return 0.0, components
        return clamp(score / weight_sum, 0.0, 1.0), components

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def rank_candidates(
        self,
        target: Dict[str, Any],
        candidates: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        prices = [c.get("price") for c in candidates]
        target_price = target.get("price")
        target_mileage = target.get("mileage_km")

        ranked_results = []
        for candidate in candidates:
            similarity_score, similarity_components = self._score_similarity(target, candidate)
            deal_score, deal_components = self._score_deal(
                candidate=candidate,
                market_prices=prices,
                target_price=target_price,
                mileage_comparison=(target_mileage, candidate.get("mileage_km")),
            )
            preference_score, preference_components = self._score_preferences(target, candidate)

            final_score = (
                similarity_score * self.weights["similarity"]
                + deal_score * self.weights["deal"]
                + preference_score * self.weights["preference"]
            )

            ranked_results.append(
                {
                    "vehicle": candidate,
                    "scores": {
                        "similarity": similarity_score,
                        "deal": deal_score,
                        "preference": preference_score,
                        "final": final_score,
                        "components": {
                            "similarity": similarity_components,
                            "deal": deal_components,
                            "preference": preference_components,
                            "weights": self.weights,
                        },
                    },
                }
            )

        ranked_results.sort(key=lambda item: item["scores"]["final"], reverse=True)
        return ranked_results
