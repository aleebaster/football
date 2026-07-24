"""Tests for Dashboard — Presenter, Statistics, Widgets, Charts, Pages."""

from app.application.dto.backtest_dto import BacktestDTO, BacktestSummaryDTO
from app.application.dto.health_dto import HealthDTO
from app.application.dto.prediction_dto import PredictionDTO
from app.application.dto.provider_dto import ProviderDTO, ProviderListDTO
from app.application.dto.signal_dto import SignalDTO, SignalListDTO
from app.application.dto.statistics_dto import (
    MarketStatisticsDTO,
    OverallStatisticsDTO,
)
from app.dashboard.charts import ChartData, ChartDataset, ChartProvider
from app.dashboard.pages import DashboardPage, PageFactory
from app.dashboard.presenters import DashboardPresenter
from app.dashboard.statistics import DashboardStatistics
from app.dashboard.widgets import Widget, WidgetFactory

# ===== Presenter Tests =====


class TestDashboardPresenter:
    def test_present_overview(self) -> None:
        health = HealthDTO(status="healthy", version="1.0.0")
        providers = ProviderListDTO(total=3, healthy=2)
        stats = OverallStatisticsDTO(
            total_predictions=100,
            total_signals=50,
            win_rate=0.65,
            roi=0.12,
            brier_score=0.15,
        )
        vm = DashboardPresenter.present_overview(health, providers, stats)
        assert vm["health_status"] == "healthy"
        assert vm["version"] == "1.0.0"
        assert vm["providers_total"] == 3
        assert vm["providers_healthy"] == 2
        assert vm["total_predictions"] == 100
        assert vm["total_signals"] == 50
        assert vm["win_rate"] == 65.0
        assert vm["roi"] == 12.0
        assert vm["brier_score"] == 0.15

    def test_present_provider_status(self) -> None:
        providers = ProviderListDTO(
            providers=[
                ProviderDTO(
                    name="mock",
                    status="healthy",
                    success_rate=0.95,
                    avg_response_ms=42.5,
                    total_requests=100,
                    consecutive_failures=0,
                ),
            ],
            total=1,
            healthy=1,
        )
        result = DashboardPresenter.present_provider_status(providers)
        assert len(result) == 1
        assert result[0]["name"] == "mock"
        assert result[0]["status"] == "healthy"
        assert result[0]["success_rate"] == 95.0
        assert result[0]["avg_response_ms"] == 42.5
        assert result[0]["requests"] == 100

    def test_present_prediction(self) -> None:
        pred = PredictionDTO(
            fixture_id=123,
            home_team="Arsenal",
            away_team="Chelsea",
            match_winner={"home": 0.6, "draw": 0.25, "away": 0.15},
            over_under_25={"over": 0.55, "under": 0.45},
            btts={"yes": 0.7, "no": 0.3},
            overall_confidence=0.82,
            overall_risk_level="low",
            value_bets=[],
            summary="Strong home favorite",
        )
        vm = DashboardPresenter.present_prediction(pred)
        assert vm["fixture_id"] == 123
        assert vm["home_team"] == "Arsenal"
        assert vm["away_team"] == "Chelsea"
        assert vm["confidence"] == 82.0
        assert vm["risk_level"] == "low"
        assert vm["value_bets"] == 0
        assert vm["summary"] == "Strong home favorite"

    def test_present_signals(self) -> None:
        signals = SignalListDTO(
            signals=[
                SignalDTO(
                    id="sig-001-abcdef",
                    fixture_id=100,
                    market="match_winner",
                    outcome="home",
                    confidence=0.85,
                    overall_score=0.78,
                    value_category="STRONG_VALUE",
                    priority="high",
                    status="active",
                ),
                SignalDTO(
                    id="sig-002-123456",
                    fixture_id=200,
                    market="over_under_25",
                    outcome="over",
                    confidence=0.70,
                    overall_score=0.65,
                    value_category="VALUE",
                    priority="medium",
                    status="expired",
                ),
            ],
            total=2,
            page=1,
            page_size=20,
        )
        vm = DashboardPresenter.present_signals(signals)
        assert vm["total"] == 2
        assert vm["active"] == 1
        assert len(vm["signals"]) == 2
        # ID is truncated to 8 chars: "sig-001-abcdef"[:8] == "sig-001-"
        assert vm["signals"][0]["id"] == "sig-001-"
        assert vm["signals"][0]["market"] == "match_winner"
        assert vm["signals"][0]["confidence"] == 85.0
        assert vm["signals"][1]["market"] == "over_under_25"

    def test_present_backtest_summary(self) -> None:
        bt = BacktestDTO(
            id="bt-abc-123",
            scope="single_match",
            status="completed",
            total_evaluations=50,
            summary=BacktestSummaryDTO(win_rate=0.72, roi=0.18),
            duration_seconds=12.5,
        )
        vm = DashboardPresenter.present_backtest_summary(bt)
        assert vm["id"] == "bt-abc-1"
        assert vm["scope"] == "single_match"
        assert vm["status"] == "completed"
        assert vm["evaluations"] == 50
        assert vm["win_rate"] == 72.0
        assert vm["roi"] == 18.0
        assert vm["duration"] == 12.5

    def test_present_backtest_summary_no_summary(self) -> None:
        bt = BacktestDTO(id="bt-xyz", status="running")
        vm = DashboardPresenter.present_backtest_summary(bt)
        assert vm["win_rate"] == 0.0
        assert vm["roi"] == 0.0

    def test_present_statistics(self) -> None:
        stats = OverallStatisticsDTO(
            total_predictions=200,
            win_rate=0.60,
            roi=0.15,
            yield_pct=8.5,
            average_odds=2.1,
            average_confidence=0.72,
            brier_score=0.18,
            calibration_error=0.05,
            signal_accuracy=0.68,
        )
        vm = DashboardPresenter.present_statistics(stats)
        assert vm["total_predictions"] == 200
        assert vm["win_rate"] == 60.0
        assert vm["roi"] == 15.0
        assert vm["yield_pct"] == 8.5
        assert vm["average_odds"] == 2.1
        assert vm["average_confidence"] == 72.0
        assert vm["brier_score"] == 0.18
        assert vm["calibration_error"] == 0.05
        assert vm["signal_accuracy"] == 68.0

    def test_format_text_report(self) -> None:
        stats = OverallStatisticsDTO(
            total_predictions=100,
            total_signals=50,
            win_rate=0.65,
            roi=0.12,
            yield_pct=6.0,
            brier_score=0.15,
            calibration_error=0.03,
        )
        report = DashboardPresenter.format_text_report(stats)
        assert "FOOTBALL ANALYSIS DASHBOARD" in report
        assert "100" in report
        assert "65.00%" in report
        assert "12.00%" in report


# ===== Statistics Tests =====


class TestDashboardStatistics:
    def test_compute_market_summary_empty(self) -> None:
        result = DashboardStatistics.compute_market_summary([])
        assert result["markets"] == []
        assert result["best_market"] is None
        assert result["worst_market"] is None
        assert result["average_roi"] == 0.0

    def test_compute_market_summary(self) -> None:
        markets = [
            MarketStatisticsDTO(
                market="match_winner",
                total_predictions=100,
                win_rate=0.65,
                roi=0.15,
                average_odds=2.0,
                average_confidence=0.72,
            ),
            MarketStatisticsDTO(
                market="over_under_25",
                total_predictions=80,
                win_rate=0.55,
                roi=0.08,
                average_odds=1.9,
                average_confidence=0.68,
            ),
        ]
        result = DashboardStatistics.compute_market_summary(markets)
        assert len(result["markets"]) == 2
        assert result["best_market"] == "match_winner"
        assert result["worst_market"] == "over_under_25"
        assert result["average_roi"] == 11.5

    def test_compute_performance_summary(self) -> None:
        stats = OverallStatisticsDTO(win_rate=0.62, roi=0.12)
        result = DashboardStatistics.compute_performance_summary(stats)
        assert result["tier"] == "excellent"
        assert result["win_rate_pct"] == 62.0
        assert result["roi_pct"] == 12.0

    def test_compute_performance_summary_good(self) -> None:
        stats = OverallStatisticsDTO(win_rate=0.56, roi=0.06)
        result = DashboardStatistics.compute_performance_summary(stats)
        assert result["tier"] == "good"

    def test_compute_performance_summary_average(self) -> None:
        stats = OverallStatisticsDTO(win_rate=0.52, roi=0.01)
        result = DashboardStatistics.compute_performance_summary(stats)
        assert result["tier"] == "average"

    def test_compute_performance_summary_needs_improvement(self) -> None:
        stats = OverallStatisticsDTO(win_rate=0.40, roi=-0.05)
        result = DashboardStatistics.compute_performance_summary(stats)
        assert result["tier"] == "needs_improvement"

    def test_compute_health_indicator_green(self) -> None:
        stats = OverallStatisticsDTO(win_rate=0.60, roi=0.10, total_predictions=100)
        assert DashboardStatistics.compute_health_indicator(stats) == "green"

    def test_compute_health_indicator_yellow_no_data(self) -> None:
        stats = OverallStatisticsDTO(total_predictions=0)
        assert DashboardStatistics.compute_health_indicator(stats) == "yellow"

    def test_compute_health_indicator_yellow_moderate(self) -> None:
        stats = OverallStatisticsDTO(win_rate=0.50, roi=0.01, total_predictions=100)
        assert DashboardStatistics.compute_health_indicator(stats) == "yellow"

    def test_compute_health_indicator_red(self) -> None:
        stats = OverallStatisticsDTO(win_rate=0.35, roi=-0.10, total_predictions=100)
        assert DashboardStatistics.compute_health_indicator(stats) == "red"


# ===== Widget Tests =====


class TestWidget:
    def test_widget_defaults(self) -> None:
        w = Widget(title="Test")
        assert w.title == "Test"
        assert w.value == ""
        assert w.color == "blue"
        assert w.metadata == {}

    def test_widget_with_values(self) -> None:
        w = Widget(title="Win Rate", value="65%", color="green")
        assert w.value == "65%"
        assert w.color == "green"

    def test_widget_serialization(self) -> None:
        w = Widget(title="Test", value=42, icon="chart")
        data = w.model_dump()
        assert data["title"] == "Test"
        assert data["value"] == 42
        assert data["icon"] == "chart"

    def test_widget_json_roundtrip(self) -> None:
        w = Widget(title="Test", value=3.14, color="purple")
        json_str = w.model_dump_json()
        w2 = Widget.model_validate_json(json_str)
        assert w2.title == w.title
        assert w2.value == w.value


class TestWidgetFactory:
    def test_stat_widget(self) -> None:
        w = WidgetFactory.stat_widget(
            "Predictions", 100, subtitle="Total", icon="chart"
        )
        assert w.title == "Predictions"
        assert w.value == 100
        assert w.subtitle == "Total"

    def test_health_widget_healthy(self) -> None:
        w = WidgetFactory.health_widget("API", "healthy", details="All OK")
        assert w.color == "green"
        assert w.icon == "heart"

    def test_health_widget_degraded(self) -> None:
        w = WidgetFactory.health_widget("API", "degraded")
        assert w.color == "yellow"

    def test_health_widget_unhealthy(self) -> None:
        w = WidgetFactory.health_widget("API", "unhealthy")
        assert w.color == "red"
        assert w.icon == "alert"

    def test_health_widget_unknown(self) -> None:
        w = WidgetFactory.health_widget("API", "unknown")
        assert w.color == "gray"

    def test_provider_widget(self) -> None:
        w = WidgetFactory.provider_widget("Mock", "healthy", 95.5, 42.0)
        assert w.title == "Mock"
        assert w.value == "95.5%"
        assert w.subtitle == "42ms avg"
        assert w.color == "green"

    def test_provider_widget_unhealthy(self) -> None:
        w = WidgetFactory.provider_widget("Mock", "unhealthy", 50.0, 200.0)
        assert w.color == "red"

    def test_overview_widgets(self) -> None:
        widgets = WidgetFactory.overview_widgets(
            total_predictions=100,
            total_signals=50,
            win_rate=65.0,
            roi=12.5,
        )
        assert len(widgets) == 4
        assert widgets[0].title == "Predictions"
        assert widgets[1].title == "Signals"
        assert widgets[2].title == "Win Rate"
        assert widgets[3].title == "ROI"
        assert widgets[2].value == "65.0%"
        assert widgets[3].value == "12.50%"


# ===== Chart Tests =====


class TestChartData:
    def test_chart_data_defaults(self) -> None:
        cd = ChartData()
        assert cd.labels == []
        assert cd.datasets == []

    def test_chart_data_serialization(self) -> None:
        cd = ChartData(
            labels=["Jan", "Feb"],
            datasets=[ChartDataset(label="ROI", data=[1.0, 2.0])],
        )
        data = cd.model_dump()
        assert data["labels"] == ["Jan", "Feb"]
        assert len(data["datasets"]) == 1
        assert data["datasets"][0]["label"] == "ROI"


class TestChartProvider:
    def test_roi_chart(self) -> None:
        chart = ChartProvider.roi_chart(["Jan", "Feb"], [5.0, 8.0])
        assert chart.labels == ["Jan", "Feb"]
        assert len(chart.datasets) == 1
        assert chart.datasets[0].label == "ROI %"
        assert chart.datasets[0].data == [5.0, 8.0]

    def test_yield_chart(self) -> None:
        chart = ChartProvider.yield_chart(["Q1", "Q2"], [3.0, 6.0])
        assert chart.datasets[0].label == "Yield %"

    def test_accuracy_chart(self) -> None:
        chart = ChartProvider.accuracy_chart(["v1", "v2"], [60.0, 72.0])
        assert chart.datasets[0].label == "Accuracy %"

    def test_win_rate_chart(self) -> None:
        chart = ChartProvider.win_rate_chart(["A", "B"], [55.0, 65.0])
        assert chart.datasets[0].label == "Win Rate %"

    def test_confidence_distribution(self) -> None:
        chart = ChartProvider.confidence_distribution(
            ["0-20%", "20-40%", "40-60%", "60-80%", "80-100%"],
            [10, 25, 40, 15, 10],
        )
        assert len(chart.labels) == 5
        assert chart.datasets[0].data == [10.0, 25.0, 40.0, 15.0, 10.0]

    def test_risk_distribution(self) -> None:
        chart = ChartProvider.risk_distribution(["low", "medium", "high"], [50, 30, 20])
        assert len(chart.labels) == 3

    def test_market_comparison(self) -> None:
        chart = ChartProvider.market_comparison(
            ["winner", "over_under"],
            [65.0, 58.0],
            [12.0, 8.0],
        )
        assert len(chart.datasets) == 2
        assert chart.datasets[0].label == "Win Rate %"
        assert chart.datasets[1].label == "ROI %"

    def test_calibration_chart(self) -> None:
        chart = ChartProvider.calibration_chart(
            [0.2, 0.4, 0.6, 0.8], [0.18, 0.42, 0.55, 0.85]
        )
        assert len(chart.datasets) == 2
        assert chart.datasets[0].label == "Expected"
        assert chart.datasets[1].label == "Observed"


# ===== Page Tests =====


class TestDashboardPage:
    def test_page_defaults(self) -> None:
        page = DashboardPage(title="Test")
        assert page.title == "Test"
        assert page.description == ""
        assert page.widgets == []
        assert page.charts == []
        assert page.tables == []

    def test_page_serialization(self) -> None:
        page = DashboardPage(
            title="Overview",
            description="System overview",
            widgets=[Widget(title="A", value=1)],
        )
        data = page.model_dump()
        assert data["title"] == "Overview"
        assert len(data["widgets"]) == 1


class TestPageFactory:
    def test_overview_page(self) -> None:
        widgets = [Widget(title="A", value=1)]
        page = PageFactory.overview_page(widgets)
        assert page.title == "Overview"
        assert "overview" in page.description.lower()
        assert len(page.widgets) == 1

    def test_overview_page_with_charts(self) -> None:
        charts = [ChartData(labels=["a"], datasets=[])]
        page = PageFactory.overview_page([], charts=charts)
        assert len(page.charts) == 1

    def test_providers_page(self) -> None:
        page = PageFactory.providers_page([Widget(title="Mock", value="healthy")])
        assert page.title == "Providers"
        assert "provider" in page.description.lower()

    def test_predictions_page(self) -> None:
        page = PageFactory.predictions_page([])
        assert page.title == "Predictions"

    def test_signals_page(self) -> None:
        page = PageFactory.signals_page([])
        assert page.title == "Signals"

    def test_backtesting_page(self) -> None:
        page = PageFactory.backtesting_page([])
        assert page.title == "Backtesting"

    def test_statistics_page(self) -> None:
        page = PageFactory.statistics_page([])
        assert page.title == "Statistics"

    def test_health_page(self) -> None:
        page = PageFactory.health_page([])
        assert page.title == "Health"

    def test_configuration_page(self) -> None:
        page = PageFactory.configuration_page([])
        assert page.title == "Configuration"


# ===== LiveDashboardPresenter Tests =====


class TestLiveDashboardPresenter:
    def test_present_live_matches(self) -> None:
        from app.application.dto.live_dto import LiveMatchDTO
        from app.dashboard.presenters import LiveDashboardPresenter

        matches = [
            LiveMatchDTO(
                fixture_id=1,
                home_team="Arsenal",
                away_team="Chelsea",
                state="live",
                status="IN_PLAY",
                home_score=2,
                away_score=1,
            ),
            LiveMatchDTO(
                fixture_id=2,
                home_team="Barcelona",
                away_team="Real Madrid",
                state="scheduled",
                status="TIMED",
            ),
        ]
        vm = LiveDashboardPresenter.present_live_matches(matches, active_count=2)
        assert vm["active_count"] == 2
        assert vm["live_count"] == 1
        assert vm["scheduled_count"] == 1
        assert vm["total"] == 2
        assert len(vm["matches"]) == 2
        assert vm["matches"][0]["home_team"] == "Arsenal"
        assert vm["matches"][0]["score"] == "2 - 1"

    def test_present_workers(self) -> None:
        from app.application.dto.live_dto import WorkerDTO
        from app.dashboard.presenters import LiveDashboardPresenter

        workers = [
            WorkerDTO(worker_id="w1", status="processing", processed_count=5),
            WorkerDTO(worker_id="w2", status="idle", processed_count=3),
            WorkerDTO(worker_id="w3", status="error", error_count=1),
        ]
        vm = LiveDashboardPresenter.present_workers(workers)
        assert vm["total"] == 3
        assert vm["active"] == 1
        assert vm["idle"] == 1
        assert vm["errors"] == 1
        assert len(vm["workers"]) == 3
        assert vm["workers"][0]["worker_id"] == "w1"
        assert vm["workers"][0]["status"] == "processing"

    def test_present_heartbeat(self) -> None:
        from datetime import UTC, datetime

        from app.application.dto.live_dto import HeartbeatDTO
        from app.dashboard.presenters import LiveDashboardPresenter

        hb = HeartbeatDTO(
            timestamp=datetime.now(UTC),
            scheduler_running=True,
            workers_healthy=3,
            workers_total=3,
            provider_healthy=True,
            queue_size=5,
            uptime_seconds=3600.0,
        )
        vm = LiveDashboardPresenter.present_heartbeat(hb)
        assert vm["scheduler_status"] == "Running"
        assert vm["scheduler_ok"] is True
        assert vm["provider_status"] == "Healthy"
        assert vm["provider_ok"] is True
        assert vm["workers_healthy"] == 3
        assert vm["workers_total"] == 3
        assert vm["workers_ok"] is True
        assert vm["uptime_seconds"] == 3600.0

    def test_present_heartbeat_unhealthy(self) -> None:
        from datetime import UTC, datetime

        from app.application.dto.live_dto import HeartbeatDTO
        from app.dashboard.presenters import LiveDashboardPresenter

        hb = HeartbeatDTO(
            timestamp=datetime.now(UTC),
            scheduler_running=False,
            workers_healthy=1,
            workers_total=3,
            provider_healthy=False,
        )
        vm = LiveDashboardPresenter.present_heartbeat(hb)
        assert vm["scheduler_status"] == "Stopped"
        assert vm["scheduler_ok"] is False
        assert vm["provider_status"] == "Unhealthy"
        assert vm["provider_ok"] is False
        assert vm["workers_ok"] is False

    def test_present_metrics(self) -> None:
        from app.application.dto.live_dto import LiveMetricsDTO
        from app.dashboard.presenters import LiveDashboardPresenter

        metrics = LiveMetricsDTO(
            active_matches=5,
            workers_active=2,
            workers_total=3,
            queue_size=10,
            events_published=100,
            avg_prediction_time_ms=45.2,
            avg_signal_time_ms=12.8,
            provider_latency_ms=30.5,
            uptime_seconds=7200.0,
        )
        vm = LiveDashboardPresenter.present_metrics(metrics)
        assert vm["active_matches"] == 5
        assert vm["events_published"] == 100
        assert vm["avg_prediction_time_ms"] == 45.2
        assert vm["provider_latency_ms"] == 30.5
        assert vm["uptime_seconds"] == 7200.0

    def test_present_recent_events(self) -> None:
        from datetime import UTC, datetime

        from app.application.dto.live_dto import LiveEventDTO
        from app.dashboard.presenters import LiveDashboardPresenter

        events = [
            LiveEventDTO(
                event_id="evt_001",
                event_type="prediction_updated",
                fixture_id=100,
                timestamp=datetime.now(UTC),
                correlation_id="corr_1",
            ),
            LiveEventDTO(
                event_id="evt_002",
                event_type="signal_created",
                fixture_id=200,
                timestamp=datetime.now(UTC),
            ),
        ]
        vm = LiveDashboardPresenter.present_recent_events(events)
        assert vm["total"] == 2
        assert vm["event_types"] == 2
        assert len(vm["events"]) == 2
        assert vm["events"][0]["event_type"] == "prediction_updated"
        assert vm["events"][0]["correlation_id"] == "corr_1"

    def test_present_provider_health(self) -> None:
        from app.application.dto.provider_dto import ProviderDTO
        from app.dashboard.presenters import LiveDashboardPresenter

        providers = [
            ProviderDTO(
                name="mock",
                status="healthy",
                success_rate=0.95,
                avg_response_ms=42.0,
                total_requests=100,
                consecutive_failures=0,
            ),
            ProviderDTO(
                name="api_football",
                status="degraded",
                success_rate=0.70,
                avg_response_ms=200.0,
                total_requests=50,
                consecutive_failures=3,
            ),
        ]
        vm = LiveDashboardPresenter.present_provider_health(providers)
        assert vm["healthy_count"] == 1
        assert vm["total_count"] == 2
        assert vm["all_healthy"] is False
        assert len(vm["providers"]) == 2
        assert vm["providers"][0]["name"] == "mock"
        assert vm["providers"][0]["success_rate"] == 95.0

    def test_present_queue_status(self) -> None:
        from app.application.dto.live_dto import LiveStatusDTO
        from app.dashboard.presenters import LiveDashboardPresenter

        status = LiveStatusDTO(
            running=True,
            active_matches=3,
            workers_active=2,
            workers_total=3,
            queue_size=5,
            events_published=50,
            uptime_seconds=1800.0,
        )
        vm = LiveDashboardPresenter.present_queue_status(status)
        assert vm["queue_size"] == 5
        assert vm["active_matches"] == 3
        assert vm["workers_active"] == 2
        assert vm["workers_total"] == 3
        assert vm["events_published"] == 50
        assert vm["uptime_seconds"] == 1800.0


# ===== LivePage Tests =====


class TestLivePage:
    def test_live_page_defaults(self) -> None:
        from app.dashboard.pages_live import LivePage

        page = LivePage(title="Test")
        assert page.title == "Test"
        assert page.description == ""
        assert page.widgets == []
        assert page.tables == []

    def test_live_page_serialization(self) -> None:
        from app.dashboard.pages_live import LivePage
        from app.dashboard.widgets import Widget

        page = LivePage(
            title="Live Matches",
            description="Current matches",
            widgets=[Widget(title="Active", value=5)],
        )
        data = page.model_dump()
        assert data["title"] == "Live Matches"
        assert len(data["widgets"]) == 1


class TestLivePageFactory:
    def test_live_matches_page(self) -> None:
        from app.dashboard.pages_live import LivePageFactory

        matches = [
            {
                "home_team": "A",
                "away_team": "B",
                "state": "live",
                "competition_name": "PL",
            },
            {
                "home_team": "C",
                "away_team": "D",
                "state": "scheduled",
                "competition_name": "LL",
            },
        ]
        page = LivePageFactory.live_matches_page(matches, active_count=2)
        assert page.title == "Live Matches"
        assert len(page.widgets) >= 1
        assert len(page.tables) == 2

    def test_workers_page(self) -> None:
        from app.dashboard.pages_live import LivePageFactory

        workers = [
            {"worker_id": "w1", "status": "idle"},
            {"worker_id": "w2", "status": "processing"},
        ]
        page = LivePageFactory.workers_page(workers)
        assert page.title == "Workers"
        assert len(page.widgets) >= 1
        assert len(page.tables) == 2

    def test_heartbeat_page(self) -> None:
        from app.dashboard.pages_live import LivePageFactory

        hb = {
            "scheduler_running": True,
            "provider_healthy": True,
            "workers_healthy": 3,
            "workers_total": 3,
            "uptime_seconds": 3600.0,
        }
        page = LivePageFactory.heartbeat_page(hb)
        assert page.title == "Heartbeat"
        assert len(page.widgets) == 4

    def test_live_metrics_page(self) -> None:
        from app.dashboard.pages_live import LivePageFactory

        metrics = {
            "active_matches": 5,
            "events_published": 100,
            "avg_prediction_time_ms": 45.0,
            "avg_signal_time_ms": 12.0,
            "provider_latency_ms": 30.0,
            "uptime_seconds": 7200.0,
        }
        page = LivePageFactory.live_metrics_page(metrics)
        assert page.title == "Live Metrics"
        assert len(page.widgets) == 6

    def test_recent_events_page(self) -> None:
        from app.dashboard.pages_live import LivePageFactory

        events = [
            {"event_id": "evt_1", "event_type": "prediction_updated", "fixture_id": 1},
        ]
        page = LivePageFactory.recent_events_page(events)
        assert page.title == "Recent Events"
        assert len(page.tables) == 1

    def test_provider_health_page(self) -> None:
        from app.dashboard.pages_live import LivePageFactory

        providers = [
            {
                "name": "mock",
                "status": "healthy",
                "success_rate": 95.0,
                "avg_response_ms": 42.0,
                "total_requests": 100,
                "consecutive_failures": 0,
            },
        ]
        page = LivePageFactory.provider_health_page(providers)
        assert page.title == "Provider Health"
        assert len(page.tables) == 1

    def test_queue_status_page(self) -> None:
        from app.dashboard.pages_live import LivePageFactory

        queue_stats = {"total": 10, "priority": 3, "normal": 7, "processed": 50}
        page = LivePageFactory.queue_status_page(queue_stats)
        assert page.title == "Queue Status"
        assert len(page.widgets) == 4


# ===== Backward Compatibility Test =====


class TestBackwardCompatibility:
    def test_views_reexports_presenter(self) -> None:
        from app.dashboard.presenters import DashboardPresenter as PresenterPresenter
        from app.dashboard.views import DashboardPresenter as ViewPresenter

        assert ViewPresenter is PresenterPresenter

    def test_dashboard_init_imports_router(self) -> None:
        from app.dashboard import router

        assert router is not None
