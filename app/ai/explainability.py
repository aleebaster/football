"""Explainability module - generates human-readable explanations."""

from app.ai.models import (
    Explanation,
    FeatureVector,
    MatchOutcome,
    RuleResult,
)
from app.logging import get_logger

logger = get_logger(__name__)


class ExplainabilityEngine:
    """Generates human-readable explanations from analysis results."""

    def explain(
        self,
        features: FeatureVector,
        rules: list[RuleResult],
    ) -> Explanation:
        """Generate explanation from features and rule results."""
        key_factors: list[str] = []
        home_advantages: list[str] = []
        away_advantages: list[str] = []
        warnings: list[str] = []

        for rule in rules:
            if rule.impact > 0:
                if rule.outcome == MatchOutcome.HOME_WIN:
                    home_advantages.append(rule.explanation)
                else:
                    away_advantages.append(rule.explanation)
            elif rule.impact < 0:
                if rule.outcome == MatchOutcome.HOME_WIN:
                    home_advantages.append(rule.explanation)
                else:
                    away_advantages.append(rule.explanation)

            if abs(rule.weight * rule.impact) > 0.08:
                key_factors.append(f"{rule.name}: {rule.explanation}")

        # Generate warnings
        if not features.get("h2h_available", False):
            warnings.append("No head-to-head data available")
        if not features.get("odds_available", False):
            warnings.append("No betting odds data available")
        if (features.get("home_played", 0) or 0) < 5:
            warnings.append("Insufficient home team match data")
        if (features.get("away_played", 0) or 0) < 5:
            warnings.append("Insufficient away team match data")

        summary = self._generate_summary(features, rules)

        return Explanation(
            summary=summary,
            key_factors=key_factors[:5],
            home_advantages=home_advantages[:5],
            away_advantages=away_advantages[:5],
            warnings=warnings,
        )

    def _generate_summary(
        self, features: FeatureVector, rules: list[RuleResult]
    ) -> str:
        """Generate a concise summary."""
        if not rules:
            return "Insufficient data to make a confident prediction."

        # Count outcomes
        home_wins = sum(1 for r in rules if r.outcome == MatchOutcome.HOME_WIN)
        away_wins = sum(1 for r in rules if r.outcome == MatchOutcome.AWAY_WIN)
        draws = sum(1 for r in rules if r.outcome == MatchOutcome.DRAW)

        total = len(rules)
        if home_wins > away_wins and home_wins > draws:
            return f"Home team favored by {home_wins}/{total} indicators."
        elif away_wins > home_wins and away_wins > draws:
            return f"Away team favored by {away_wins}/{total} indicators."
        elif draws > 0:
            return (
                f"Mixed signals: {home_wins} home, {away_wins} away, {draws} neutral."
            )
        else:
            return "Analysis complete with balanced indicators."
