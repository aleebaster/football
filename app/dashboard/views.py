"""Dashboard Views — presenters and widgets for the web interface."""

from __future__ import annotations

from typing import Any

from app.application.dto.backtest_dto import BacktestDTO
from app.application.dto.health_dto import HealthDTO
from app.application.dto.prediction_dto import PredictionDTO
from app.application.dto.provider_dto import ProviderListDTO
from app.application.dto.signal_dto import SignalListDTO
from app.application.dto.statistics_dto import OverallStatisticsDTO


class DashboardPresenter:
    """Transforms DTOs into dashboard-friendly representations."""

    @staticmethod
    def present_overview(
        health: HealthDTO,
        providers: ProviderListDTO,
        statistics: OverallStatisticsDTO,
    ) -> dict[str, Any]:
        return {
            "health_status": health.status,
            "version": health.version,
            "providers_total": providers.total,
            "providers_healthy": providers.healthy,
            "total_predictions": statistics.total_predictions,
            "total_signals": statistics.total_signals,
            "win_rate": round(statistics.win_rate * 100, 2),
            "roi": round(statistics.roi * 100, 2),
            "brier_score": round(statistics.brier_score, 4),
        }

    @staticmethod
    def present_provider_status(providers: ProviderListDTO) -> list[dict[str, Any]]:
        return [
            {
                "name": p.name,
                "status": p.status,
                "success_rate": round(p.success_rate * 100, 1),
                "avg_response_ms": round(p.avg_response_ms, 1),
                "requests": p.total_requests,
                "failures": p.consecutive_failures,
            }
            for p in providers.providers
        ]

    @staticmethod
    def present_prediction(prediction: PredictionDTO) -> dict[str, Any]:
        return {
            "fixture_id": prediction.fixture_id,
            "home_team": prediction.home_team,
            "away_team": prediction.away_team,
            "match_winner": prediction.match_winner,
            "over_under_25": prediction.over_under_25,
            "btts": prediction.btts,
            "confidence": round(prediction.overall_confidence * 100, 1),
            "risk_level": prediction.overall_risk_level,
            "value_bets": len(prediction.value_bets),
            "summary": prediction.summary,
        }

    @staticmethod
    def present_signals(signals: SignalListDTO) -> dict[str, Any]:
        return {
            "total": signals.total,
            "active": len([s for s in signals.signals if s.status == "active"]),
            "signals": [
                {
                    "id": s.id[:8],
                    "market": s.market,
                    "outcome": s.outcome,
                    "confidence": round(s.confidence * 100, 1),
                    "score": round(s.overall_score * 100, 1),
                    "value": s.value_category,
                    "priority": s.priority,
                }
                for s in signals.signals
            ],
        }

    @staticmethod
    def present_backtest_summary(
        backtest: BacktestDTO,
    ) -> dict[str, Any]:
        return {
            "id": backtest.id[:8] if backtest.id else "N/A",
            "scope": backtest.scope,
            "status": backtest.status,
            "evaluations": backtest.total_evaluations,
            "win_rate": round(
                (backtest.summary.win_rate if backtest.summary else 0) * 100, 1
            ),
            "roi": round((backtest.summary.roi if backtest.summary else 0) * 100, 2),
            "duration": round(backtest.duration_seconds, 1),
        }

    @staticmethod
    def present_statistics(stats: OverallStatisticsDTO) -> dict[str, Any]:
        return {
            "total_predictions": stats.total_predictions,
            "win_rate": round(stats.win_rate * 100, 2),
            "roi": round(stats.roi * 100, 2),
            "yield_pct": round(stats.yield_pct, 2),
            "average_odds": round(stats.average_odds, 2),
            "average_confidence": round(stats.average_confidence * 100, 1),
            "brier_score": round(stats.brier_score, 4),
            "calibration_error": round(stats.calibration_error, 4),
            "signal_accuracy": round(stats.signal_accuracy * 100, 2),
        }

    @staticmethod
    def format_text_report(stats: OverallStatisticsDTO) -> str:
        lines = [
            "═══════════════════════════════════════════",
            "         FOOTBALL ANALYSIS DASHBOARD       ",
            "═══════════════════════════════════════════",
            "",
            f"  Predictions:   {stats.total_predictions}",
            f"  Signals:       {stats.total_signals}",
            f"  Win Rate:      {stats.win_rate * 100:.2f}%",
            f"  ROI:           {stats.roi * 100:.2f}%",
            f"  Yield:         {stats.yield_pct:.2f}%",
            f"  Brier Score:   {stats.brier_score:.4f}",
            f"  Calibration:   {stats.calibration_error:.4f}",
            "",
            "═══════════════════════════════════════════",
        ]
        return "\n".join(lines)
