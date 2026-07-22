"""Consensus Engine — aggregates signals from AI analysis into a unified prediction."""

from collections import Counter

from app.ai.models import AnalysisResult, RuleResult
from app.logging import get_logger
from app.prediction.models import (
    ConsensusResult,
    PredictionMarket,
    ProbabilityDistribution,
)

logger = get_logger(__name__)


class ConsensusEngine:
    """Aggregates multiple analysis signals into a single consensus."""

    def aggregate(
        self,
        analysis: AnalysisResult,
        market: PredictionMarket = PredictionMarket.MATCH_WINNER,
    ) -> ConsensusResult:
        """Build a consensus from analysis result signals."""
        factors: list[str] = []
        source_count = 0

        # Rule engine agreement
        if analysis.rules:
            source_count += 1
            rules_agree = self._rules_agreement(analysis.rules)
            factors.append(
                f"Rules: {len(analysis.rules)} evaluated, {rules_agree:.0%} agreement"
            )

        # Confidence signal
        if analysis.confidence:
            source_count += 1
            factors.append(f"Confidence: {analysis.confidence.overall:.0%}")

        # Feature vector
        if analysis.features:
            source_count += 1
            feature_count = len(analysis.features.features)
            factors.append(f"Features: {feature_count} extracted")

        # AI prediction
        if analysis.prediction:
            source_count += 1
            factors.append(
                f"AI prediction: home {analysis.prediction.probability_home:.0%}, "
                f"draw {analysis.prediction.probability_draw:.0%}, "
                f"away {analysis.prediction.probability_away:.0%}"
            )

        # Agreement score
        agreement = self._compute_agreement(analysis)

        # Weighted probability
        weighted = self._compute_weighted_probability(analysis)

        # Signal strength
        signal_strength = min(1.0, source_count / 4.0) if source_count > 0 else 0.0

        return ConsensusResult(
            source_count=source_count,
            agreement_score=agreement,
            weighted_probability=weighted,
            signal_strength=signal_strength,
            factors=factors,
        )

    def _rules_agreement(self, rules: list[RuleResult]) -> float:
        """Calculate how much rules agree on the outcome."""
        if not rules:
            return 0.0
        outcomes = [r.outcome.value for r in rules]
        if not outcomes:
            return 0.0
        counts = Counter(outcomes)
        most_common = counts.most_common(1)[0][1]
        return float(most_common / len(outcomes))

    def _compute_agreement(self, analysis: AnalysisResult) -> float:
        """Compute overall agreement score across signals."""
        scores: list[float] = []

        if analysis.rules:
            scores.append(self._rules_agreement(analysis.rules))

        if analysis.prediction:
            # Check if prediction aligns with rules
            if analysis.rules:
                from app.ai.models import MatchOutcome

                home_rules = sum(
                    1 for r in analysis.rules if r.outcome == MatchOutcome.HOME_WIN
                )
                away_rules = sum(
                    1 for r in analysis.rules if r.outcome == MatchOutcome.AWAY_WIN
                )
                if home_rules + away_rules > 0:
                    dominant = max(home_rules, away_rules) / (home_rules + away_rules)
                    scores.append(dominant)

        if analysis.confidence:
            scores.append(analysis.confidence.overall)

        return sum(scores) / len(scores) if scores else 0.0

    def _compute_weighted_probability(
        self,
        analysis: AnalysisResult,
    ) -> ProbabilityDistribution | None:
        """Compute a weighted probability from all signals."""
        if not analysis.prediction:
            return None

        p = analysis.prediction
        weights = {
            "home": p.probability_home,
            "draw": p.probability_draw,
            "away": p.probability_away,
        }

        # Adjust weights by confidence
        if analysis.confidence:
            conf = analysis.confidence.overall
            total = sum(weights.values())
            if total > 0:
                weights = {k: v * conf + (1 - conf) / 3 for k, v in weights.items()}

        total = sum(weights.values())
        if total <= 0:
            return None

        return ProbabilityDistribution(
            market=PredictionMarket.MATCH_WINNER,
            outcomes={k: v / total for k, v in weights.items()},
        )
