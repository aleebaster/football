"""Confidence Engine - calculates confidence scores for analysis."""

from app.ai.models import (
    ConfidenceResult,
    FeatureVector,
    RiskAssessment,
    RuleResult,
)
from app.logging import get_logger

logger = get_logger(__name__)


class ConfidenceEngine:
    """Calculates confidence, risk, and stability scores."""

    def calculate(
        self,
        features: FeatureVector,
        rules: list[RuleResult],
    ) -> tuple[ConfidenceResult, RiskAssessment]:
        """Calculate confidence and risk from features and rules."""
        data_quality = self._assess_data_quality(features)
        provider_quality = self._assess_feature_coverage(features)
        stability = self._assess_stability(features, rules)
        risk_score = self._assess_risk(features, rules)

        factors: list[str] = []
        if data_quality < 0.5:
            factors.append("Insufficient data availability")
        if provider_quality < 0.5:
            factors.append("Low provider data quality")
        if stability < 0.3:
            factors.append("Unstable feature signals")

        # Weighted overall confidence
        overall = (
            data_quality * 0.3
            + provider_quality * 0.2
            + stability * 0.3
            + (1.0 - risk_score) * 0.2
        )
        overall = max(0.0, min(1.0, overall))

        confidence = ConfidenceResult(
            overall=round(overall, 3),
            risk=round(risk_score, 3),
            stability=round(stability, 3),
            data_quality=round(data_quality, 3),
            provider_quality=round(provider_quality, 3),
            factors=factors,
        )

        risk = self._build_risk_assessment(risk_score, features, rules)
        return confidence, risk

    def _assess_data_quality(self, features: FeatureVector) -> float:
        """Assess quality of source data."""
        if not features.sources:
            return 0.3
        completeness_values = [s.data_completeness for s in features.sources]
        avg_completeness = sum(completeness_values) / len(completeness_values)
        return avg_completeness

    def _assess_feature_coverage(self, features: FeatureVector) -> float:
        """Assess feature coverage from analyzers."""
        # Check how many analyzers contributed features
        unique_analyzers = len({s.analyzer for s in features.sources})
        total_expected = 8  # core analyzers
        return min(1.0, unique_analyzers / total_expected)

    def _assess_stability(
        self, features: FeatureVector, rules: list[RuleResult]
    ) -> float:
        """Assess signal stability."""
        if not rules:
            return 0.3
        # Check if rules agree on outcome
        outcomes = [r.outcome.value for r in rules]
        if not outcomes:
            return 0.3
        from collections import Counter

        counts = Counter(outcomes)
        most_common = counts.most_common(1)[0][1]
        agreement = most_common / len(outcomes)
        return agreement

    def _assess_risk(self, features: FeatureVector, rules: list[RuleResult]) -> float:
        """Assess prediction risk (0=low risk, 1=high risk)."""
        risk_factors: float = 0
        total: float = 0

        # Small sample size
        total += 1
        hp = features.get("home_played", 0) or 0
        ap = features.get("away_played", 0) or 0
        if hp < 5 or ap < 5:
            risk_factors += 1

        # No H2H data
        total += 1
        if not features.get("h2h_available", False):
            risk_factors += 1

        # No odds data
        total += 1
        if not features.get("odds_available", False):
            risk_factors += 0.5

        # Conflicting signals
        total += 1
        if rules:
            outcomes = {r.outcome.value for r in rules}
            if len(outcomes) >= 3:
                risk_factors += 1
            elif len(outcomes) == 2:
                risk_factors += 0.5

        return min(1.0, risk_factors / max(total, 1))

    def _build_risk_assessment(
        self, risk_score: float, features: FeatureVector, rules: list[RuleResult]
    ) -> RiskAssessment:
        """Build detailed risk assessment."""
        if risk_score < 0.25:
            level = "low"
        elif risk_score < 0.5:
            level = "medium"
        elif risk_score < 0.75:
            level = "high"
        else:
            level = "very_high"

        factors: list[str] = []
        hp = features.get("home_played", 0) or 0
        ap = features.get("away_played", 0) or 0
        if hp < 5 or ap < 5:
            factors.append("Small sample size")
        if not features.get("h2h_available", False):
            factors.append("No head-to-head data")

        return RiskAssessment(
            level=level,
            score=round(risk_score, 3),
            factors=factors,
        )
