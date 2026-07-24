"""Dashboard Presenters — transforms DTOs into dashboard-friendly ViewModels.

Pipeline:
    Application Service → DTO → Presenter → View

Presenters do not access Service Layer directly.
They receive pre-built DTOs and produce ViewModel dicts for the view layer.
"""

from __future__ import annotations

from typing import Any

from app.application.dto.backtest_dto import BacktestDTO
from app.application.dto.health_dto import HealthDTO
from app.application.dto.live_dto import (
    HeartbeatDTO,
    LiveEventDTO,
    LiveMatchDTO,
    LiveMetricsDTO,
    LiveStatusDTO,
    WorkerDTO,
)
from app.application.dto.prediction_dto import PredictionDTO
from app.application.dto.provider_dto import ProviderDTO, ProviderListDTO
from app.application.dto.signal_dto import SignalListDTO
from app.application.dto.statistics_dto import OverallStatisticsDTO


class DashboardPresenter:
    """Transforms DTOs into dashboard-friendly representations.

    This presenter receives DTOs from the Application Layer and
    produces ViewModels (dicts) consumed by the view/template layer.
    It does NOT access any service or engine directly.
    """

    @staticmethod
    def present_overview(
        health: HealthDTO,
        providers: ProviderListDTO,
        statistics: OverallStatisticsDTO,
    ) -> dict[str, Any]:
        """Build the overview ViewModel from DTOs."""
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
        """Build provider status ViewModels from DTO."""
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
        """Build a prediction ViewModel from DTO."""
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
        """Build signals ViewModel from DTO."""
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
        """Build a backtest summary ViewModel from DTO."""
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
        """Build a statistics ViewModel from DTO."""
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
        """Format a plain-text dashboard report from DTO."""
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


class LiveDashboardPresenter:
    """Transforms Live Engine DTOs into dashboard-friendly ViewModels.

    Pipeline:
        LiveService → LiveDTO → LiveDashboardPresenter → View

    This presenter receives DTOs from the Application Layer and
    produces ViewModel dicts consumed by the live dashboard pages.
    It does NOT access any Live Engine directly.
    """

    @staticmethod
    def present_live_matches(
        matches: list[LiveMatchDTO],
        active_count: int = 0,
    ) -> dict[str, Any]:
        """Build the Live Matches ViewModel from DTOs."""
        live_count = len(
            [m for m in matches if m.state in ("live", "half_time", "second_half")]
        )
        scheduled_count = len([m for m in matches if m.state == "scheduled"])

        return {
            "active_count": active_count,
            "live_count": live_count,
            "scheduled_count": scheduled_count,
            "total": len(matches),
            "matches": [
                {
                    "fixture_id": m.fixture_id,
                    "home_team": m.home_team,
                    "away_team": m.away_team,
                    "competition": m.competition_name or "N/A",
                    "state": m.state,
                    "score": f"{m.home_score if m.home_score is not None else '-'} - {m.away_score if m.away_score is not None else '-'}",
                    "status": m.status,
                }
                for m in matches
            ],
        }

    @staticmethod
    def present_workers(
        workers: list[WorkerDTO],
    ) -> dict[str, Any]:
        """Build the Workers ViewModel from DTOs."""
        total = len(workers)
        active = len([w for w in workers if w.status == "processing"])
        idle = len([w for w in workers if w.status == "idle"])
        errors = len([w for w in workers if w.status == "error"])

        return {
            "total": total,
            "active": active,
            "idle": idle,
            "errors": errors,
            "workers": [
                {
                    "worker_id": w.worker_id,
                    "status": w.status,
                    "current_fixture_id": w.current_fixture_id,
                    "processed_count": w.processed_count,
                    "error_count": w.error_count,
                    "last_active": w.last_active.isoformat()
                    if w.last_active
                    else "N/A",
                }
                for w in workers
            ],
        }

    @staticmethod
    def present_heartbeat(
        heartbeat: HeartbeatDTO,
    ) -> dict[str, Any]:
        """Build the Heartbeat ViewModel from DTOs."""
        scheduler_ok = heartbeat.scheduler_running
        provider_ok = heartbeat.provider_healthy
        workers_healthy = heartbeat.workers_healthy
        workers_total = heartbeat.workers_total

        return {
            "scheduler_status": "Running" if scheduler_ok else "Stopped",
            "scheduler_ok": scheduler_ok,
            "provider_status": "Healthy" if provider_ok else "Unhealthy",
            "provider_ok": provider_ok,
            "workers_healthy": workers_healthy,
            "workers_total": workers_total,
            "workers_ok": workers_healthy == workers_total,
            "uptime_seconds": heartbeat.uptime_seconds,
            "queue_size": heartbeat.queue_size,
        }

    @staticmethod
    def present_metrics(
        metrics: LiveMetricsDTO,
    ) -> dict[str, Any]:
        """Build the Live Metrics ViewModel from DTOs."""
        return {
            "active_matches": metrics.active_matches,
            "workers_active": metrics.workers_active,
            "workers_total": metrics.workers_total,
            "queue_size": metrics.queue_size,
            "events_published": metrics.events_published,
            "avg_prediction_time_ms": round(metrics.avg_prediction_time_ms, 1),
            "avg_signal_time_ms": round(metrics.avg_signal_time_ms, 1),
            "provider_latency_ms": round(metrics.provider_latency_ms, 1),
            "uptime_seconds": metrics.uptime_seconds,
        }

    @staticmethod
    def present_recent_events(
        events: list[LiveEventDTO],
    ) -> dict[str, Any]:
        """Build the Recent Events ViewModel from DTOs."""
        return {
            "total": len(events),
            "event_types": len({e.event_type for e in events}),
            "events": [
                {
                    "event_id": e.event_id[:12],
                    "event_type": e.event_type,
                    "fixture_id": e.fixture_id,
                    "correlation_id": e.correlation_id or "-",
                    "worker_id": e.worker_id or "-",
                    "timestamp": e.timestamp.isoformat(),
                }
                for e in events
            ],
        }

    @staticmethod
    def present_provider_health(
        providers: list[ProviderDTO],
    ) -> dict[str, Any]:
        """Build the Provider Health ViewModel from DTOs."""
        healthy = len([p for p in providers if p.status == "healthy"])
        total = len(providers)

        return {
            "healthy_count": healthy,
            "total_count": total,
            "all_healthy": healthy == total,
            "providers": [
                {
                    "name": p.name,
                    "status": p.status,
                    "success_rate": round(p.success_rate * 100, 1),
                    "avg_response_ms": round(p.avg_response_ms, 0),
                    "total_requests": p.total_requests,
                    "consecutive_failures": p.consecutive_failures,
                }
                for p in providers
            ],
        }

    @staticmethod
    def present_queue_status(
        status: LiveStatusDTO,
    ) -> dict[str, Any]:
        """Build the Queue Status ViewModel from DTOs."""
        return {
            "queue_size": status.queue_size,
            "active_matches": status.active_matches,
            "workers_active": status.workers_active,
            "workers_total": status.workers_total,
            "events_published": status.events_published,
            "uptime_seconds": status.uptime_seconds,
        }
