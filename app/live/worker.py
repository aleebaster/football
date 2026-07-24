"""Live Engine — Worker processes a single match through the full pipeline.

Pipeline:
    Match → Provider Update → AI Analysis → Prediction → Signal → Event
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable, Coroutine
from typing import Any

from app.live.events import EventFactory, LiveEvent
from app.live.interfaces import WorkerInterface
from app.live.models import LiveMatch, MatchState, WorkerStatus
from app.live.state import StateRegistry
from app.logging import get_logger
from app.prediction.models import PredictionRequest
from app.providers.manager import ProviderManager

logger = get_logger(__name__)

# Type alias for the processing pipeline callback
ProcessCallback = Callable[[LiveMatch, list[LiveEvent]], Coroutine[Any, Any, None]]


class LiveWorker(WorkerInterface):
    """Processes a single match through the full Live Engine pipeline.

    Pipeline:
        1. Fetch latest match data from Provider
        2. Run AI Analysis (via container)
        3. Run Prediction Engine (via container)
        4. Run Signal Engine (via container)
        5. Emit events for each meaningful change
    """

    def __init__(
        self,
        worker_id: str | None = None,
        provider_manager: ProviderManager | None = None,
        state_registry: StateRegistry | None = None,
    ) -> None:
        self._worker_id = worker_id or f"worker_{uuid.uuid4().hex[:8]}"
        self._provider_manager = provider_manager
        self._state_registry = state_registry
        self._busy = False
        self._current_fixture: int | None = None
        self._processed_count = 0
        self._error_count = 0
        self._callbacks: list[ProcessCallback] = []

    @property
    def worker_id(self) -> str:
        return self._worker_id

    @property
    def is_busy(self) -> bool:
        return self._busy

    @property
    def processed_count(self) -> int:
        return self._processed_count

    @property
    def error_count(self) -> int:
        return self._error_count

    def on_events(self, callback: ProcessCallback) -> None:
        """Register a callback for when events are produced."""
        self._callbacks.append(callback)

    async def start(self) -> None:
        """Start the worker."""
        if self._state_registry:
            await self._state_registry.register_worker(self._worker_id)
            await self._state_registry.update_worker_status(
                self._worker_id, WorkerStatus.IDLE
            )
        logger.info(f"Worker {self._worker_id} started")

    async def stop(self) -> None:
        """Stop the worker."""
        if self._state_registry:
            await self._state_registry.update_worker_status(
                self._worker_id, WorkerStatus.STOPPED
            )
        self._busy = False
        logger.info(f"Worker {self._worker_id} stopped")

    async def process(self, match: LiveMatch) -> list[LiveEvent]:
        """Process a single match through the full pipeline.

        Returns a list of events generated during processing.
        """
        self._busy = True
        self._current_fixture = match.fixture_id
        events: list[LiveEvent] = []

        if self._state_registry:
            await self._state_registry.update_worker_status(
                self._worker_id, WorkerStatus.PROCESSING, match.fixture_id
            )

        start_time = time.perf_counter()
        correlation_id = f"corr_{uuid.uuid4().hex[:8]}"

        try:
            # Step 1: Update match state to PREPARING
            if self._state_registry:
                await self._state_registry.update_match_state(
                    match.fixture_id, MatchState.PREPARING
                )

            # Step 2: Fetch latest data from Provider
            updated_match = await self._fetch_latest_data(match)

            # Step 3: Run AI Analysis + Prediction + Signal
            prediction_events = await self._run_pipeline(updated_match, correlation_id)
            events.extend(prediction_events)

            # Step 4: Update state based on provider status
            new_state = self._determine_state(updated_match)
            if self._state_registry:
                await self._state_registry.update_match_state(
                    updated_match.fixture_id, new_state
                )

            self._processed_count += 1

        except Exception as e:
            self._error_count += 1
            logger.warning(
                f"Worker {self._worker_id} failed processing fixture {match.fixture_id}: {e}"
            )
            if self._state_registry:
                await self._state_registry.update_worker_status(
                    self._worker_id, WorkerStatus.ERROR, match.fixture_id
                )
        finally:
            elapsed = time.perf_counter() - start_time
            self._busy = False
            self._current_fixture = None

            if self._state_registry:
                await self._state_registry.update_worker_status(
                    self._worker_id, WorkerStatus.IDLE
                )

            logger.debug(
                f"Worker {self._worker_id} processed fixture {match.fixture_id} "
                f"in {elapsed:.2f}s ({len(events)} events)"
            )

        # Notify callbacks
        for callback in self._callbacks:
            try:
                await callback(match, events)
            except Exception as e:
                logger.warning(f"Callback failed: {e}")

        return events

    async def _fetch_latest_data(self, match: LiveMatch) -> LiveMatch:
        """Fetch latest match data from Provider Layer."""
        if self._provider_manager is None:
            return match

        try:
            fixture = await self._provider_manager.fixture(match.fixture_id)
            if fixture:
                return LiveMatch(
                    fixture_id=fixture.id,
                    home_team_id=fixture.home_team_id or match.home_team_id,
                    home_team=fixture.home_team or match.home_team,
                    away_team_id=fixture.away_team_id or match.away_team_id,
                    away_team=fixture.away_team or match.away_team,
                    competition_id=fixture.competition_id,
                    competition_name=fixture.competition_name,
                    utc_date=fixture.utc_date,
                    status=fixture.status,
                    home_score=fixture.home_score,
                    away_score=fixture.away_score,
                )
        except Exception as e:
            logger.debug(
                f"Failed to fetch latest data for fixture {match.fixture_id}: {e}"
            )

        return match

    async def _run_pipeline(
        self, match: LiveMatch, correlation_id: str
    ) -> list[LiveEvent]:
        """Run AI → Prediction → Signal pipeline and collect events."""
        events: list[LiveEvent] = []
        from app.core.container import get_container

        container = get_container()

        # Run Prediction
        try:
            request = PredictionRequest(
                fixture_id=match.fixture_id,
                home_team_id=match.home_team_id,
                away_team_id=match.away_team_id,
                force_refresh=True,
            )
            prediction = await container.prediction_engine.predict(request)

            events.append(
                EventFactory.prediction_updated(
                    fixture_id=match.fixture_id,
                    confidence=prediction.overall_confidence,
                    correlation_id=correlation_id,
                )
            )

            # Run Signal Engine
            try:
                signals = await container.signal_engine.process(prediction)
                for signal in signals:
                    events.append(
                        EventFactory.signal_created(
                            fixture_id=match.fixture_id,
                            signal_id=signal.id,
                            market=signal.market.value,
                            outcome=signal.outcome,
                            correlation_id=correlation_id,
                        )
                    )
            except Exception as e:
                logger.debug(
                    f"Signal generation failed for fixture {match.fixture_id}: {e}"
                )

        except Exception as e:
            logger.debug(f"Prediction failed for fixture {match.fixture_id}: {e}")

        return events

    @staticmethod
    def _determine_state(match: LiveMatch) -> MatchState:
        """Determine match state from provider status."""
        status = match.status.upper()
        if status in ("IN_PLAY",):
            return MatchState.LIVE
        elif status in ("PAUSED", "HALFTIME"):
            return MatchState.HALF_TIME
        elif status in ("FINISHED", "AWARDED"):
            return MatchState.FINISHED
        elif status in ("POSTPONED",):
            return MatchState.POSTPONED
        elif status in ("CANCELLED",):
            return MatchState.CANCELLED
        elif status in ("SUSPENDED",):
            return MatchState.INTERRUPTED
        else:
            return MatchState.SCHEDULED
