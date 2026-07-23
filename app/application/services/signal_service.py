"""Signal Service — provides signal data."""

from app.application.dto.signal_dto import SignalDTO, SignalListDTO
from app.application.mapper import Mapper
from app.core.container import get_container


class SignalService:
    """Provides signal data through the Signal Engine."""

    async def get_signals(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> SignalListDTO:
        container = get_container()
        history = container.signal_engine.history

        try:
            all_records = await history.get_all_records()
            # Extract unique signals from history records
            seen: set[str] = set()
            signals: list[object] = []
            for record in all_records:
                if record.signal.id not in seen:
                    seen.add(record.signal.id)
                    signals.append(record.signal)

            start = (page - 1) * page_size
            end = start + page_size
            page_signals = signals[start:end]

            return Mapper.to_signal_list_dto(
                page_signals, total=len(signals), page=page, page_size=page_size
            )
        except Exception:
            return SignalListDTO(page=page, page_size=page_size)

    async def get_signal(self, signal_id: str) -> SignalDTO | None:
        container = get_container()
        history = container.signal_engine.history

        try:
            record = await history.get_latest(signal_id)
            if record is None:
                return None
            return Mapper.to_signal_dto(record.signal)
        except Exception:
            return None
