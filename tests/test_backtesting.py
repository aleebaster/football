"""Tests for Backtesting Platform."""

import pytest

from app.backtesting.calibration import BacktestCalibration
from app.backtesting.comparison import BacktestComparison
from app.backtesting.dataset import BacktestDataset
from app.backtesting.evaluator import BacktestEvaluator
from app.backtesting.exceptions import BacktestDatasetError, BacktestValidationError
from app.backtesting.exporter import BacktestExporter
from app.backtesting.history import BacktestHistory
from app.backtesting.metrics import BacktestMetricsCalculator
from app.backtesting.models import (
    BacktestMetrics,
    BacktestRequest,
    BacktestResult,
    BacktestScope,
    BacktestStatus,
    BacktestSummary,
    CalibrationDataset,
    ComparisonResult,
    EvaluationResult,
    ExportFormat,
    MarketBreakdown,
)
from app.backtesting.persistence import BacktestPersistence
from app.backtesting.registry import BacktestRegistry
from app.backtesting.reporting import BacktestReporter
from app.backtesting.statistics import BacktestStatistics
from app.backtesting.validator import BacktestValidator
from app.prediction.models import PredictionMarket

# ===== Helper Functions =====


def _make_evaluation(
    fixture_id: int = 1000,
    predicted_outcome: str = "home",
    actual_outcome: str = "home",
    predicted_probability: float = 0.6,
    odds: float = 2.0,
    confidence: float = 0.7,
    risk_score: float = 0.3,
    market: PredictionMarket = PredictionMarket.MATCH_WINNER,
) -> EvaluationResult:
    """Create a test evaluation result."""
    return EvaluationResult(
        fixture_id=fixture_id,
        market=market,
        predicted_outcome=predicted_outcome,
        predicted_probability=predicted_probability,
        actual_outcome=actual_outcome,
        is_correct=(predicted_outcome == actual_outcome),
        odds=odds,
        confidence=confidence,
        risk_score=risk_score,
    )


def _make_correct_evaluations(count: int = 10) -> list[EvaluationResult]:
    """Create a list of correct evaluations."""
    return [
        _make_evaluation(
            fixture_id=1000 + i,
            predicted_outcome="home",
            actual_outcome="home",
            predicted_probability=0.7,
            odds=1.8,
        )
        for i in range(count)
    ]


def _make_mixed_evaluations(count: int = 10) -> list[EvaluationResult]:
    """Create a mix of correct and incorrect evaluations."""
    results = []
    for i in range(count):
        is_correct = i % 2 == 0
        results.append(
            _make_evaluation(
                fixture_id=1000 + i,
                predicted_outcome="home" if is_correct else "away",
                actual_outcome="home",
                predicted_probability=0.6 if is_correct else 0.4,
                odds=2.0,
            )
        )
    return results


def _make_backtest_request(
    scope: BacktestScope = BacktestScope.SINGLE_MATCH,
    fixture_id: int = 1000,
) -> BacktestRequest:
    """Create a test backtest request."""
    return BacktestRequest(scope=scope, fixture_id=fixture_id)


# ===== Model Tests =====


class TestBacktestModels:
    def test_backtest_request(self) -> None:
        req = _make_backtest_request()
        assert req.scope == BacktestScope.SINGLE_MATCH
        assert req.fixture_id == 1000
        assert req.max_matches == 1000

    def test_evaluation_result(self) -> None:
        eval_result = _make_evaluation()
        assert eval_result.fixture_id == 1000
        assert eval_result.is_correct is True
        assert eval_result.market == "match_winner"

    def test_evaluation_result_incorrect(self) -> None:
        eval_result = _make_evaluation(predicted_outcome="home", actual_outcome="away")
        assert eval_result.is_correct is False

    def test_backtest_metrics_defaults(self) -> None:
        metrics = BacktestMetrics()
        assert metrics.total_predictions == 0
        assert metrics.win_rate == 0.0

    def test_backtest_result(self) -> None:
        result = BacktestResult(
            request=_make_backtest_request(),
            status=BacktestStatus.COMPLETED,
        )
        assert result.status == BacktestStatus.COMPLETED
        assert len(result.evaluations) == 0

    def test_backtest_summary(self) -> None:
        summary = BacktestSummary(
            request=_make_backtest_request(),
            status=BacktestStatus.COMPLETED,
            metrics=BacktestMetrics(),
        )
        assert summary.status == BacktestStatus.COMPLETED

    def test_calibration_dataset(self) -> None:
        cal = CalibrationDataset(
            fixture_id=1000,
            market=PredictionMarket.MATCH_WINNER,
            predicted_probability=0.6,
            actual_outcome=True,
        )
        assert cal.fixture_id == 1000
        assert cal.actual_outcome is True

    def test_comparison_result(self) -> None:
        comp = ComparisonResult(
            version_a="1.0.0",
            version_b="2.0.0",
            metrics_a=BacktestMetrics(),
            metrics_b=BacktestMetrics(),
        )
        assert comp.version_a == "1.0.0"

    def test_market_breakdown(self) -> None:
        mb = MarketBreakdown(
            market=PredictionMarket.MATCH_WINNER,
            total=10,
            correct=7,
        )
        assert mb.total == 10

    def test_export_format(self) -> None:
        assert ExportFormat.CSV.value == "csv"
        assert ExportFormat.JSON.value == "json"


# ===== Validator Tests =====


class TestBacktestValidator:
    def test_validate_single_match(self) -> None:
        validator = BacktestValidator()
        req = _make_backtest_request(BacktestScope.SINGLE_MATCH, fixture_id=1000)
        assert validator.validate_request(req) is True

    def test_validate_single_match_no_fixture(self) -> None:
        validator = BacktestValidator()
        req = BacktestRequest(scope=BacktestScope.SINGLE_MATCH)
        with pytest.raises(BacktestValidationError):
            validator.validate_request(req)

    def test_validate_league_no_id(self) -> None:
        validator = BacktestValidator()
        req = BacktestRequest(scope=BacktestScope.LEAGUE)
        with pytest.raises(BacktestValidationError):
            validator.validate_request(req)

    def test_validate_season_no_value(self) -> None:
        validator = BacktestValidator()
        req = BacktestRequest(scope=BacktestScope.SEASON)
        with pytest.raises(BacktestValidationError):
            validator.validate_request(req)

    def test_validate_date_range_invalid(self) -> None:
        validator = BacktestValidator()
        req = BacktestRequest(
            scope=BacktestScope.DATE_RANGE,
            date_from="2024-12-01",
            date_to="2024-01-01",
        )
        with pytest.raises(BacktestValidationError):
            validator.validate_request(req)


# ===== Evaluator Tests =====


class TestBacktestEvaluator:
    @pytest.mark.asyncio
    async def test_evaluate_correct(self) -> None:
        evaluator = BacktestEvaluator()
        result = await evaluator.evaluate(
            fixture_id=1000,
            predicted_outcome="home",
            predicted_probability=0.7,
            actual_outcome="home",
            odds=2.0,
        )
        assert result.is_correct is True
        assert result.pnl > 0
        assert result.roi > 0

    @pytest.mark.asyncio
    async def test_evaluate_incorrect(self) -> None:
        evaluator = BacktestEvaluator()
        result = await evaluator.evaluate(
            fixture_id=1000,
            predicted_outcome="home",
            predicted_probability=0.7,
            actual_outcome="away",
            odds=2.0,
        )
        assert result.is_correct is False
        assert result.pnl < 0

    def test_brier_score(self) -> None:
        evaluator = BacktestEvaluator()
        score = evaluator.calculate_brier_score(0.7, True)
        assert 0 <= score <= 1

    def test_log_loss(self) -> None:
        evaluator = BacktestEvaluator()
        loss = evaluator.calculate_log_loss(0.7, True)
        assert loss >= 0


# ===== Metrics Tests =====


class TestBacktestMetricsCalculator:
    @pytest.mark.asyncio
    async def test_calculate_empty(self) -> None:
        calc = BacktestMetricsCalculator()
        metrics = await calc.calculate([])
        assert metrics.total_predictions == 0

    @pytest.mark.asyncio
    async def test_calculate_all_correct(self) -> None:
        calc = BacktestMetricsCalculator()
        results = _make_correct_evaluations(10)
        metrics = await calc.calculate(results)
        assert metrics.total_predictions == 10
        assert metrics.correct_predictions == 10
        assert metrics.win_rate == 1.0

    @pytest.mark.asyncio
    async def test_calculate_mixed(self) -> None:
        calc = BacktestMetricsCalculator()
        results = _make_mixed_evaluations(10)
        metrics = await calc.calculate(results)
        assert metrics.total_predictions == 10
        assert metrics.correct_predictions == 5
        assert 0 < metrics.win_rate < 1

    def test_calibration_buckets(self) -> None:
        calc = BacktestMetricsCalculator()
        results = _make_correct_evaluations(10)
        buckets = calc.calculate_calibration_buckets(results)
        assert len(buckets) == 10

    def test_market_breakdown(self) -> None:
        calc = BacktestMetricsCalculator()
        results = _make_correct_evaluations(10)
        breakdown = calc.calculate_market_breakdown(results)
        assert len(breakdown) >= 1


# ===== Dataset Tests =====


class TestBacktestDataset:
    @pytest.mark.asyncio
    async def test_load_raises_without_provider(self) -> None:
        """Dataset raises BacktestDatasetError when no provider is available."""
        dataset = BacktestDataset()
        req = _make_backtest_request(BacktestScope.SINGLE_MATCH, fixture_id=1000)
        with pytest.raises(BacktestDatasetError):
            await dataset.load(req)

    @pytest.mark.asyncio
    async def test_count_returns_zero_without_provider(self) -> None:
        """Count returns 0 when no provider is available (safe behavior)."""
        dataset = BacktestDataset()
        req = _make_backtest_request(BacktestScope.SINGLE_MATCH, fixture_id=1000)
        count = await dataset.count(req)
        assert count == 0

    def test_dataset_requires_provider(self) -> None:
        """Dataset requires a provider manager for operations."""
        dataset = BacktestDataset()
        assert dataset._provider_manager is None


# ===== Persistence Tests =====


class TestBacktestPersistence:
    @pytest.mark.asyncio
    async def test_save_and_get(self) -> None:
        persistence = BacktestPersistence()
        result = BacktestResult(request=_make_backtest_request())
        result_id = await persistence.save(result)
        assert result_id is not None
        retrieved = await persistence.get(result_id)
        assert retrieved is not None

    @pytest.mark.asyncio
    async def test_get_all(self) -> None:
        persistence = BacktestPersistence()
        for _ in range(3):
            await persistence.save(BacktestResult(request=_make_backtest_request()))
        all_results = await persistence.get_all()
        assert len(all_results) == 3

    @pytest.mark.asyncio
    async def test_delete(self) -> None:
        persistence = BacktestPersistence()
        result_id = await persistence.save(
            BacktestResult(request=_make_backtest_request())
        )
        assert await persistence.delete(result_id) is True
        assert await persistence.get(result_id) is None


# ===== Calibration Tests =====


class TestBacktestCalibration:
    @pytest.mark.asyncio
    async def test_collect(self) -> None:
        cal = BacktestCalibration()
        result = BacktestResult(
            request=_make_backtest_request(),
            evaluations=_make_correct_evaluations(5),
        )
        entries = await cal.collect(result)
        assert len(entries) == 5

    def test_get_all(self) -> None:
        cal = BacktestCalibration()
        assert len(cal) == 0

    def test_clear(self) -> None:
        cal = BacktestCalibration()
        cal.clear()
        assert len(cal) == 0


# ===== Reporting Tests =====


class TestBacktestReporter:
    @pytest.mark.asyncio
    async def test_generate(self) -> None:
        reporter = BacktestReporter()
        result = BacktestResult(
            request=_make_backtest_request(),
            evaluations=_make_correct_evaluations(10),
        )
        summary = await reporter.generate(result)
        assert summary.total_evaluations == 10

    def test_format_text_report(self) -> None:
        reporter = BacktestReporter()
        summary = BacktestSummary(
            request=_make_backtest_request(),
            status=BacktestStatus.COMPLETED,
            metrics=BacktestMetrics(total_predictions=10, win_rate=0.7),
        )
        text = reporter.format_text_report(summary)
        assert "BACKTEST REPORT" in text
        assert "70.00%" in text


# ===== Comparison Tests =====


class TestBacktestComparison:
    def test_compare(self) -> None:
        comparison = BacktestComparison()
        result_a = BacktestResult(
            request=_make_backtest_request(),
            metrics=BacktestMetrics(win_rate=0.6, roi=0.1),
        )
        result_b = BacktestResult(
            request=_make_backtest_request(),
            metrics=BacktestMetrics(win_rate=0.7, roi=0.15),
        )
        comp = comparison.compare(result_a, result_b)
        assert comp.version_a == "1.0.0"
        assert comp.version_b == "1.0.0"


# ===== Exporter Tests =====


class TestBacktestExporter:
    @pytest.mark.asyncio
    async def test_export_json(self, tmp_path: object) -> None:
        from pathlib import Path

        exporter = BacktestExporter()
        result = BacktestResult(
            request=_make_backtest_request(),
            evaluations=_make_correct_evaluations(3),
        )
        path = await exporter.export(
            result, str(Path(str(tmp_path)) / "test.json"), ExportFormat.JSON
        )
        assert path is not None

    @pytest.mark.asyncio
    async def test_export_csv(self, tmp_path: object) -> None:
        from pathlib import Path

        exporter = BacktestExporter()
        result = BacktestResult(
            request=_make_backtest_request(),
            evaluations=_make_correct_evaluations(3),
        )
        path = await exporter.export(
            result, str(Path(str(tmp_path)) / "test.csv"), ExportFormat.CSV
        )
        assert path is not None


# ===== Registry Tests =====


class TestBacktestRegistry:
    def test_register_and_get(self) -> None:
        registry = BacktestRegistry()
        registry.register("test", {"key": "value"})
        assert registry.get("test") == {"key": "value"}
        assert len(registry) == 1

    def test_unregister(self) -> None:
        registry = BacktestRegistry()
        registry.register("test", {"key": "value"})
        assert registry.unregister("test") is True
        assert registry.get("test") is None

    def test_contains(self) -> None:
        registry = BacktestRegistry()
        registry.register("test", {})
        assert "test" in registry


# ===== History Tests =====


class TestBacktestHistory:
    @pytest.mark.asyncio
    async def test_record_and_get(self) -> None:
        history = BacktestHistory()
        result = BacktestResult(
            request=_make_backtest_request(),
            status=BacktestStatus.COMPLETED,
        )
        await history.record_run(result)
        runs = await history.get_runs()
        assert len(runs) == 1

    @pytest.mark.asyncio
    async def test_get_latest(self) -> None:
        history = BacktestHistory()
        assert await history.get_latest() is None


# ===== Statistics Tests =====


class TestBacktestStatistics:
    def test_calculate_by_confidence_bucket(self) -> None:
        stats = BacktestStatistics()
        results = _make_mixed_evaluations(10)
        bucket_stats = stats.calculate_by_confidence_bucket(results)
        assert len(bucket_stats) > 0

    def test_calculate_by_risk_bucket(self) -> None:
        stats = BacktestStatistics()
        results = _make_mixed_evaluations(10)
        bucket_stats = stats.calculate_by_risk_bucket(results)
        assert len(bucket_stats) > 0

    def test_calculate_by_predictor(self) -> None:
        stats = BacktestStatistics()
        results = _make_mixed_evaluations(10)
        predictor_stats = stats.calculate_by_predictor(results)
        assert len(predictor_stats) > 0


# ===== Integration Tests =====


class TestBacktestIntegration:
    """Integration tests for the full backtesting pipeline."""

    @pytest.mark.asyncio
    async def test_statistics_delegates_to_metrics(self) -> None:
        """Verify Statistics delegates to MetricsCalculator."""
        from app.backtesting.metrics import BacktestMetricsCalculator

        metrics_calc = BacktestMetricsCalculator()
        stats = BacktestStatistics(metrics_calculator=metrics_calc)
        results = _make_mixed_evaluations(10)

        # Both should produce the same confidence buckets
        cal_buckets = metrics_calc.calculate_calibration_buckets(results)
        stat_buckets = stats.calculate_by_confidence_bucket(results)
        assert len(stat_buckets) == len(cal_buckets)

    @pytest.mark.asyncio
    async def test_full_pipeline_metrics_and_reporting(self) -> None:
        """Test full pipeline: evaluations → metrics → reporting."""
        calc = BacktestMetricsCalculator()
        reporter = BacktestReporter()
        results = _make_mixed_evaluations(20)

        # Calculate metrics
        metrics = await calc.calculate(results)
        assert metrics.total_predictions == 20
        assert 0 < metrics.win_rate < 1

        # Create result and generate report
        backtest_result = BacktestResult(
            request=_make_backtest_request(),
            evaluations=results,
            metrics=metrics,
        )
        summary = await reporter.generate(backtest_result)
        assert summary.total_evaluations == 20
        assert summary.metrics.win_rate == metrics.win_rate

    @pytest.mark.asyncio
    async def test_full_pipeline_calibration_and_persistence(self) -> None:
        """Test full pipeline: evaluations → calibration → persistence."""
        calc = BacktestMetricsCalculator()
        cal = BacktestCalibration()
        persistence = BacktestPersistence()
        results = _make_correct_evaluations(5)

        # Calculate metrics
        metrics = await calc.calculate(results)

        # Create and persist result
        backtest_result = BacktestResult(
            request=_make_backtest_request(),
            evaluations=results,
            metrics=metrics,
        )
        result_id = await persistence.save(backtest_result)
        assert result_id is not None

        # Collect calibration data
        entries = await cal.collect(backtest_result)
        assert len(entries) == 5

        # Retrieve persisted result
        retrieved = await persistence.get(result_id)
        assert retrieved is not None
        assert len(retrieved.evaluations) == 5

    @pytest.mark.asyncio
    async def test_pipeline_metrics_statistics_reporting(self) -> None:
        """Test: evaluations → metrics → statistics → reporting."""
        calc = BacktestMetricsCalculator()
        stats = BacktestStatistics(metrics_calculator=calc)
        reporter = BacktestReporter()
        results = _make_mixed_evaluations(15)

        # Calculate metrics
        metrics = await calc.calculate(results)
        assert metrics.total_predictions == 15

        # Calculate statistics
        market_stats = stats.calculate_by_market(results)
        assert len(market_stats) >= 1

        predictor_stats = stats.calculate_by_predictor(results)
        assert len(predictor_stats) >= 1

        # Generate report
        backtest_result = BacktestResult(
            request=_make_backtest_request(),
            evaluations=results,
            metrics=metrics,
        )
        summary = await reporter.generate(backtest_result)
        assert summary.total_evaluations == 15

        # Format report text
        text = reporter.format_text_report(summary)
        assert "BACKTEST REPORT" in text


# ===== Property-Based Tests =====


class TestPropertyBased:
    def test_brier_score_always_non_negative(self) -> None:
        evaluator = BacktestEvaluator()
        for prob in [0.0, 0.3, 0.5, 0.7, 1.0]:
            for outcome in [True, False]:
                score = evaluator.calculate_brier_score(prob, outcome)
                assert score >= 0

    def test_log_loss_always_non_negative(self) -> None:
        evaluator = BacktestEvaluator()
        for prob in [0.1, 0.3, 0.5, 0.7, 0.9]:
            for outcome in [True, False]:
                loss = evaluator.calculate_log_loss(prob, outcome)
                assert loss >= 0

    @pytest.mark.asyncio
    async def test_metrics_win_rate_in_range(self) -> None:
        calc = BacktestMetricsCalculator()
        for results in [
            _make_correct_evaluations(5),
            _make_mixed_evaluations(10),
            [],
        ]:
            metrics = await calc.calculate(results)
            assert 0 <= metrics.win_rate <= 1

    def test_calibration_buckets_count(self) -> None:
        calc = BacktestMetricsCalculator()
        results = _make_mixed_evaluations(20)
        buckets = calc.calculate_calibration_buckets(results)
        assert len(buckets) == 10

    @pytest.mark.asyncio
    async def test_export_roundtrip_json(self, tmp_path: object) -> None:
        """Test that JSON export produces valid data."""
        import json

        exporter = BacktestExporter()
        result = BacktestResult(
            request=_make_backtest_request(),
            evaluations=_make_correct_evaluations(5),
            metrics=BacktestMetrics(win_rate=1.0, total_predictions=5),
        )
        from pathlib import Path

        path = str(Path(str(tmp_path)) / "test.json")
        await exporter.export(result, path, ExportFormat.JSON)
        with open(path) as f:
            data = json.load(f)
        assert data["total_evaluations"] == 5
        assert data["metrics"]["win_rate"] == 1.0
