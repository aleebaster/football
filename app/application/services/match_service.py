"""Match Service — provides match data from providers."""

from app.application.dto.match_dto import MatchDTO, MatchListDTO
from app.application.mapper import Mapper
from app.core.container import get_container


class MatchService:
    """Provides match data through the provider layer."""

    async def get_matches(
        self,
        competition_id: int | None = None,
        limit: int = 20,
    ) -> MatchListDTO:
        container = get_container()
        manager = container.provider_manager
        try:
            fixtures = await manager.fixtures(
                competition_id=competition_id,
                limit=limit,
            )
            return Mapper.to_match_list_dto(
                fixtures, total=len(fixtures), page=1, page_size=limit
            )
        except Exception:
            return MatchListDTO()

    async def get_match(self, fixture_id: int) -> MatchDTO | None:
        container = get_container()
        manager = container.provider_manager
        try:
            fixture = await manager.fixture(fixture_id)
            if fixture is None:
                return None
            return Mapper.to_match_dto(fixture)
        except Exception:
            return None
