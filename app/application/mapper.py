"""Mapper Layer — converts internal engine models to DTOs.

Never return internal models directly to the API.
Always map through this layer.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.application.dto.backtest_dto import BacktestDTO, BacktestSummaryDTO
from app.application.dto.health_dto import (
    CacheHealthDTO,
    EngineHealthDTO,
    HealthDTO,
    ProviderHealthDTO,
)
from app.application.dto.live_dto import (
    HeartbeatDTO,
    LiveEventDTO,
    LiveMatchDTO,
    LiveMetricsDTO,
    LiveStatusDTO,
    WorkerDTO,
)
from app.application.dto.match_dto import MatchDTO, MatchListDTO
from app.application.dto.prediction_dto import (
    PredictionDTO,
    PredictionSummaryDTO,
    ValueBetDTO,
)
from app.application.dto.provider_dto import ProviderDTO
from app.application.dto.signal_dto import SignalDTO, SignalListDTO
from app.application.dto.statistics_dto import (
    LeagueStatisticsDTO,
    MarketStatisticsDTO,
    OverallStatisticsDTO,
    TeamStatisticsDTO,
)
from app.providers.models import Fixture

if TYPE_CHECKING:
    from app.live.events import LiveEvent
    from app.live.models import HeartbeatInfo, LiveMatch, LiveMetrics, WorkerInfo


class Mapper:
    """Converts internal engine models to API DTOs."""

    # ── Health ───────────────────────────────────────────────────────

    @staticmethod
    def to_health_dto(
        providers: list[dict[str, object]],
        cache_entries: int = 0,
        version: str = "0.1.0",
    ) -> HealthDTO:
        provider_dtos = [
            ProviderHealthDTO(
                name=str(p.get("name", "unknown")),
                status=str(p.get("status", "unknown")),
                success_rate=float(str(p.get("success_rate", 0.0))),
                avg_response_ms=float(str(p.get("avg_response_ms", 0.0))),
                consecutive_failures=int(str(p.get("consecutive_failures", 0))),
            )
            for p in providers
        ]
        engines = [
            EngineHealthDTO(name="AI Engine", status="ready"),
            EngineHealthDTO(name="Prediction Engine", status="ready"),
            EngineHealthDTO(name="Signal Engine", status="ready"),
            EngineHealthDTO(name="Backtest Engine", status="ready"),
            EngineHealthDTO(name="Live Engine", status="ready"),
        ]
        return HealthDTO(
            status="healthy",
            version=version,
            providers=provider_dtos,
            cache=CacheHealthDTO(entries=cache_entries),
            engines=engines,
        )

    # ── Live ─────────────────────────────────────────────────────────

    @staticmethod
    def to_live_match_dto(match: LiveMatch | None) -> LiveMatchDTO:
        if match is None:
            return LiveMatchDTO(fixture_id=0)
        return LiveMatchDTO(
            fixture_id=match.fixture_id,
            home_team=match.home_team,
            away_team=match.away_team,
            competition_name=match.competition_name,
            status=match.status,
            state=match.state.value,
            home_score=match.home_score,
            away_score=match.away_score,
            utc_date=match.utc_date,
            last_updated=match.last_updated,
        )

    @staticmethod
    def to_live_match_dtos(matches: list[LiveMatch]) -> list[LiveMatchDTO]:
        return [Mapper.to_live_match_dto(m) for m in matches]

    @staticmethod
    def to_live_event_dto(event: LiveEvent | None) -> LiveEventDTO:
        if event is None:
            return LiveEventDTO(
                event_id="",
                event_type="",
                fixture_id=0,
                timestamp=datetime.now(UTC),
            )
        return LiveEventDTO(
            event_id=event.event_id,
            event_type=event.event_type,
            fixture_id=event.fixture_id,
            timestamp=event.timestamp,
            data=event.data,
            correlation_id=event.correlation_id,
            worker_id=event.worker_id,
        )

    @staticmethod
    def to_live_event_dtos(events: list[LiveEvent]) -> list[LiveEventDTO]:
        return [Mapper.to_live_event_dto(e) for e in events]

    @staticmethod
    def to_worker_dto(worker: WorkerInfo | None) -> WorkerDTO:
        if worker is None:
            return WorkerDTO(worker_id="unknown")
        return WorkerDTO(
            worker_id=worker.worker_id,
            status=worker.status.value,
            current_fixture_id=worker.current_fixture_id,
            processed_count=worker.processed_count,
            error_count=worker.error_count,
            last_active=worker.last_active,
        )

    @staticmethod
    def to_worker_dtos(workers: list[WorkerInfo]) -> list[WorkerDTO]:
        return [Mapper.to_worker_dto(w) for w in workers]

    @staticmethod
    def to_heartbeat_dto(heartbeat: HeartbeatInfo | None) -> HeartbeatDTO:
        if heartbeat is None:
            return HeartbeatDTO(timestamp=datetime.now(UTC))
        return HeartbeatDTO(
            timestamp=heartbeat.timestamp,
            scheduler_running=heartbeat.scheduler_running,
            workers_healthy=heartbeat.workers_healthy,
            workers_total=heartbeat.workers_total,
            provider_healthy=heartbeat.provider_healthy,
            queue_size=heartbeat.queue_size,
            uptime_seconds=heartbeat.uptime_seconds,
        )

    @staticmethod
    def to_live_metrics_dto(metrics: LiveMetrics | None) -> LiveMetricsDTO:
        if metrics is None:
            return LiveMetricsDTO()
        return LiveMetricsDTO(
            active_matches=metrics.active_matches,
            workers_active=metrics.workers_active,
            workers_total=metrics.workers_total,
            queue_size=metrics.queue_size,
            events_published=metrics.events_published,
            provider_latency_ms=metrics.provider_latency_ms,
            avg_prediction_time_ms=metrics.avg_prediction_time_ms,
            avg_signal_time_ms=metrics.avg_signal_time_ms,
            uptime_seconds=metrics.uptime_seconds,
        )

    @staticmethod
    def to_live_status_dto(status: dict[str, object]) -> LiveStatusDTO:
        return LiveStatusDTO(
            running=bool(status.get("running", False)),
            active_matches=int(str(status.get("active_matches", 0))),
            workers_active=int(str(status.get("workers_active", 0))),
            workers_total=int(str(status.get("workers_total", 0))),
            queue_size=int(str(status.get("queue_size", 0))),
            events_published=int(str(status.get("events_published", 0))),
            uptime_seconds=float(str(status.get("uptime_seconds", 0.0))),
        )

    # ── Matches ──────────────────────────────────────────────────────

    @staticmethod
    def to_match_dto(fixture: Fixture) -> MatchDTO:
        return MatchDTO(
            fixture_id=fixture.id,
            home_team_id=fixture.home_team_id,
            home_team=fixture.home_team or "",
            home_team_crest=fixture.home_team_crest,
            away_team_id=fixture.away_team_id,
            away_team=fixture.away_team or "",
            away_team_crest=fixture.away_team_crest,
            competition_id=fixture.competition_id,
            competition_name=fixture.competition_name,
            status=fixture.status,
            utc_date=fixture.utc_date,
            home_score=fixture.home_score,
            away_score=fixture.away_score,
            venue=fixture.venue,
        )

    @staticmethod
    def to_match_list_dto(
        fixtures: list[Fixture],
        total: int = 0,
        page: int = 1,
        page_size: int = 20,
    ) -> MatchListDTO:
        return MatchListDTO(
            matches=[Mapper.to_match_dto(f) for f in fixtures],
            total=total or len(fixtures),
            page=page,
            page_size=page_size,
        )

    # ── Predictions ──────────────────────────────────────────────────

    @staticmethod
    def to_prediction_summary_dto(
        fixture_id: int,
        prediction: object,
        home_team: str = "",
        away_team: str = "",
    ) -> PredictionSummaryDTO:
        from app.prediction.models import PredictionResult

        pred = prediction if isinstance(prediction, PredictionResult) else None
        if pred is None:
            return PredictionSummaryDTO(
                fixture_id=fixture_id,
                home_team=home_team,
                away_team=away_team,
            )

        home_win_pct = 0.0
        draw_pct = 0.0
        away_win_pct = 0.0
        for mp in pred.predictions:
            if mp.market.value == "match_winner":
                home_win_pct = mp.distribution.outcomes.get("home", 0.0)
                draw_pct = mp.distribution.outcomes.get("draw", 0.0)
                away_win_pct = mp.distribution.outcomes.get("away", 0.0)
                break

        return PredictionSummaryDTO(
            fixture_id=fixture_id,
            home_team=home_team,
            away_team=away_team,
            home_win_pct=home_win_pct,
            draw_pct=draw_pct,
            away_win_pct=away_win_pct,
            confidence=pred.overall_confidence,
            risk_level=pred.overall_risk.level.value,
            computed_at=pred.computed_at,
        )

    @staticmethod
    def to_prediction_dto(
        prediction: object,
        home_team: str = "",
        away_team: str = "",
    ) -> PredictionDTO:
        from app.prediction.models import PredictionResult

        pred = prediction if isinstance(prediction, PredictionResult) else None
        if pred is None:
            return PredictionDTO(fixture_id=0)

        match_winner: dict[str, float] = {}
        over_under: dict[str, float] = {}
        btts: dict[str, float] = {}
        value_bets: list[ValueBetDTO] = []

        for mp in pred.predictions:
            outcomes = dict(mp.distribution.outcomes)
            if mp.market.value == "match_winner":
                match_winner = outcomes
            elif mp.market.value == "over_under_25":
                over_under = outcomes
            elif mp.market.value == "btts":
                btts = outcomes

            for vb in mp.value_bets:
                value_bets.append(
                    ValueBetDTO(
                        market=vb.market.value,
                        outcome=vb.outcome,
                        model_probability=vb.model_probability,
                        market_odds=vb.market_odds,
                        edge=vb.edge,
                        expected_value=vb.expected_value,
                        explanation=vb.explanation,
                    )
                )

        return PredictionDTO(
            fixture_id=pred.fixture_id,
            home_team=home_team,
            away_team=away_team,
            home_team_id=pred.home_team_id,
            away_team_id=pred.away_team_id,
            match_winner=match_winner,
            over_under_25=over_under,
            btts=btts,
            overall_confidence=pred.overall_confidence,
            overall_risk_level=pred.overall_risk.level.value,
            overall_risk_score=pred.overall_risk.score,
            value_bets=value_bets,
            summary=pred.explanation.summary if pred.explanation else "",
            key_factors=pred.explanation.key_factors if pred.explanation else [],
            warnings=pred.explanation.warnings if pred.explanation else [],
            model_version=pred.model_version,
            prediction_time_ms=pred.prediction_time_ms,
            computed_at=pred.computed_at,
        )

    # ── Signals ──────────────────────────────────────────────────────

    @staticmethod
    def to_signal_dto(
        signal: object,
        home_team: str = "",
        away_team: str = "",
    ) -> SignalDTO:
        from app.signals.models import Signal

        sig = signal if isinstance(signal, Signal) else None
        if sig is None:
            return SignalDTO(id="", fixture_id=0)

        return SignalDTO(
            id=sig.id,
            fixture_id=sig.fixture_id,
            home_team=home_team,
            away_team=away_team,
            signal_type=sig.signal_type.value,
            priority=sig.priority.value,
            status=sig.status.value,
            market=sig.market.value,
            outcome=sig.outcome,
            probability=sig.probability,
            confidence=sig.confidence,
            odds=sig.odds,
            overall_score=sig.score.overall,
            expected_value=sig.score.expected_value,
            value_category=sig.value_category.value,
            risk_level=sig.risk_level.value,
            risk_score=sig.risk_score,
            summary=sig.summary,
            key_factors=sig.key_factors,
            model_version=sig.model_version,
            created_at=sig.created_at,
            expires_at=sig.expires_at,
        )

    @staticmethod
    def to_signal_list_dto(
        signals: list[object],
        total: int = 0,
        page: int = 1,
        page_size: int = 20,
    ) -> SignalListDTO:
        return SignalListDTO(
            signals=[Mapper.to_signal_dto(s) for s in signals],
            total=total or len(signals),
            page=page,
            page_size=page_size,
        )

    # ── Backtests ────────────────────────────────────────────────────

    @staticmethod
    def to_backtest_summary_dto(result: object) -> BacktestSummaryDTO:
        from app.backtesting.models import BacktestResult

        res = result if isinstance(result, BacktestResult) else None
        if res is None:
            return BacktestSummaryDTO()

        return BacktestSummaryDTO(
            id=res.id,
            scope=res.request.scope.value,
            status=res.status.value,
            total_predictions=res.metrics.total_predictions,
            win_rate=res.metrics.win_rate,
            roi=res.metrics.roi,
            yield_pct=res.metrics.yield_pct,
            average_odds=res.metrics.average_odds,
            average_confidence=res.metrics.average_confidence,
            brier_score=res.metrics.brier_score,
            started_at=res.started_at,
            completed_at=res.completed_at,
            duration_seconds=res.duration_seconds,
        )

    @staticmethod
    def to_backtest_dto(result: object) -> BacktestDTO:
        from app.backtesting.models import BacktestResult

        res = result if isinstance(result, BacktestResult) else None
        if res is None:
            return BacktestDTO()

        return BacktestDTO(
            id=res.id,
            scope=res.request.scope.value,
            status=res.status.value,
            fixture_id=res.request.fixture_id,
            league_id=res.request.league_id,
            date_from=res.request.date_from,
            date_to=res.request.date_to,
            max_matches=res.request.max_matches,
            total_evaluations=len(res.evaluations),
            summary=Mapper.to_backtest_summary_dto(result),
            started_at=res.started_at,
            completed_at=res.completed_at,
            duration_seconds=res.duration_seconds,
            error=res.error,
        )

    # ── Providers ────────────────────────────────────────────────────

    @staticmethod
    def to_provider_dto(
        name: str,
        health: object,
    ) -> ProviderDTO:
        from app.providers.base import ProviderHealth

        h = health if isinstance(health, ProviderHealth) else None
        return ProviderDTO(
            name=name,
            status=h.status.value if h else "unknown",
            success_rate=h.success_rate / 100.0 if h else 0.0,
            avg_response_ms=h.average_response_time * 1000 if h else 0.0,
            total_requests=h.total_requests if h else 0,
            consecutive_failures=h.consecutive_failures if h else 0,
        )

    # ── Statistics ───────────────────────────────────────────────────

    @staticmethod
    def to_overall_statistics_dto(metrics: object) -> OverallStatisticsDTO:
        from app.backtesting.models import BacktestMetrics

        m = metrics if isinstance(metrics, BacktestMetrics) else None
        if m is None:
            return OverallStatisticsDTO()

        return OverallStatisticsDTO(
            total_predictions=m.total_predictions,
            win_rate=m.win_rate,
            roi=m.roi,
            yield_pct=m.yield_pct,
            average_odds=m.average_odds,
            average_confidence=m.average_confidence,
            average_risk=m.average_risk,
            brier_score=m.brier_score,
            calibration_error=m.calibration_error,
            signal_accuracy=m.signal_accuracy,
        )

    @staticmethod
    def to_league_statistics_dtos(
        league_stats: dict[str, dict[str, object]],
    ) -> list[LeagueStatisticsDTO]:
        result: list[LeagueStatisticsDTO] = []
        for name, stats in league_stats.items():
            result.append(
                LeagueStatisticsDTO(
                    league_id=0,
                    league_name=name,
                    total_predictions=int(str(stats.get("total", 0))),
                    win_rate=float(str(stats.get("win_rate", 0.0))),
                    roi=float(str(stats.get("roi", 0.0))),
                    average_confidence=float(str(stats.get("avg_confidence", 0.0))),
                )
            )
        return result

    @staticmethod
    def to_market_statistics_dtos(
        market_breakdowns: list[object],
    ) -> list[MarketStatisticsDTO]:
        from app.backtesting.models import MarketBreakdown

        dtos: list[MarketStatisticsDTO] = []
        for mb in market_breakdowns:
            if isinstance(mb, MarketBreakdown):
                dtos.append(
                    MarketStatisticsDTO(
                        market=mb.market.value,
                        total_predictions=mb.total,
                        win_rate=mb.win_rate,
                        roi=mb.roi,
                        average_odds=mb.average_odds,
                        average_confidence=mb.average_confidence,
                    )
                )
        return dtos

    @staticmethod
    def to_team_statistics_dtos(
        team_stats: dict[str, dict[str, object]],
    ) -> list[TeamStatisticsDTO]:
        result: list[TeamStatisticsDTO] = []
        for name, stats in team_stats.items():
            result.append(
                TeamStatisticsDTO(
                    team_id=0,
                    team_name=name,
                    total_predictions=int(str(stats.get("total", 0))),
                    win_rate=float(str(stats.get("win_rate", 0.0))),
                    roi=float(str(stats.get("roi", 0.0))),
                )
            )
        return result
