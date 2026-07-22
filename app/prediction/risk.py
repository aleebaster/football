"""Risk Engine — evaluates and quantifies prediction risk."""

from app.ai.models import AnalysisResult
from app.logging import get_logger
from app.prediction.models import PredictionRiskAssessment, RiskLevel

logger = get_logger(__name__)


class RiskEngine:
    """Evaluates prediction risk based on multiple factors."""

    def assess(
        self,
        analysis: AnalysisResult,
    ) -> PredictionRiskAssessment:
        """Compute risk assessment from analysis result."""
        factors: list[str] = []
        risk_score: float = 0.0
        total_factors: float = 0.0

        # Data completeness
        data_comp = self._assess_data_completeness(analysis)
        total_factors += 1.0
        if data_comp < 0.5:
            risk_score += 0.3
            factors.append("Low data completeness")

        # Provider reliability
        provider_rel = self._assess_provider_reliability(analysis)
        total_factors += 1.0
        if provider_rel < 0.5:
            risk_score += 0.2
            factors.append("Low provider reliability")

        # Confidence signal
        conf_risk = self._assess_confidence_risk(analysis)
        total_factors += 1.0
        risk_score += conf_risk * 0.3
        if conf_risk > 0.5:
            factors.append("Low confidence score")

        # Volatility
        volatility = self._assess_volatility(analysis)

        # Stability
        stability = self._assess_stability(analysis)

        # Normalize risk score
        risk_score = min(1.0, risk_score / max(total_factors, 1.0))

        # Determine level
        level = self._risk_level(risk_score)

        return PredictionRiskAssessment(
            level=level,
            score=round(risk_score, 3),
            volatility=round(volatility, 3),
            data_completeness=round(data_comp, 3),
            provider_reliability=round(provider_rel, 3),
            stability=round(stability, 3),
            factors=factors,
        )

    def _assess_data_completeness(self, analysis: AnalysisResult) -> float:
        if not analysis.features:
            return 0.2
        sources = analysis.features.sources
        if not sources:
            return 0.2
        completeness = sum(s.data_completeness for s in sources) / len(sources)
        return completeness

    def _assess_provider_reliability(self, analysis: AnalysisResult) -> float:
        if not analysis.confidence:
            return 0.5
        return analysis.confidence.provider_quality

    def _assess_confidence_risk(self, analysis: AnalysisResult) -> float:
        if not analysis.confidence:
            return 0.7
        return 1.0 - analysis.confidence.overall

    def _assess_volatility(self, analysis: AnalysisResult) -> float:
        if not analysis.rules:
            return 0.5
        impacts = [abs(r.impact) for r in analysis.rules]
        if not impacts:
            return 0.5
        avg_impact = sum(impacts) / len(impacts)
        return min(1.0, avg_impact)

    def _assess_stability(self, analysis: AnalysisResult) -> float:
        if not analysis.confidence:
            return 0.3
        return analysis.confidence.stability

    @staticmethod
    def _risk_level(score: float) -> RiskLevel:
        if score < 0.25:
            return RiskLevel.LOW
        elif score < 0.5:
            return RiskLevel.MEDIUM
        elif score < 0.75:
            return RiskLevel.HIGH
        return RiskLevel.VERY_HIGH
