"""Football-Data.org adapter.

Normalizes football-data.org responses to internal models.
"""

import time
from typing import Any

from app.logging import get_logger
from app.providers.base import BaseProvider
from app.providers.http_client import HttpClient, HttpClientConfig
from app.providers.models import (
    Competition,
    Fixture,
    Odds,
    ProviderStatus,
    Standing,
    Team,
)

logger = get_logger(__name__)

_BASE_URL = "https://api.football-data.org/v4"


class FootballDataProvider(BaseProvider):
    """Football-Data.org data provider."""

    def __init__(self, api_key: str, priority: int = 20) -> None:
        super().__init__(name="football_data", api_key=api_key, priority=priority)
        self._http = HttpClient(
            HttpClientConfig(
                base_url=_BASE_URL,
                api_key=api_key,
                timeout=30.0,
                rate_limit=5.0,
                rate_burst=10,
                user_agent="FootballAnalytics/1.0 (football-data.org)",
            )
        )

    async def start(self) -> None:
        await self._http.start()

    async def stop(self) -> None:
        await self._http.stop()

    def _normalize_competition(self, data: dict[str, Any]) -> Competition:
        area = data.get("area", {})
        return Competition(
            id=data.get("id", 0),
            name=data.get("name", ""),
            code=data.get("code"),
            country=area.get("name"),
            country_code=area.get("code"),
            emblem=data.get("emblem"),
            current_season=data.get("currentSeason", {}).get("id"),
            current_matchday=data.get("currentSeason", {}).get("currentMatchday"),
        )

    def _normalize_team(self, data: dict[str, Any]) -> Team:
        return Team(
            id=data.get("id", 0),
            name=data.get("name", ""),
            short_name=data.get("shortName"),
            tla=data.get("tla"),
            founded=data.get("founded"),
            venue=data.get("venue"),
            club_colors=data.get("clubColors"),
            crest=data.get("crest"),
        )

    def _normalize_fixture(self, data: dict[str, Any]) -> Fixture:
        home_team = data.get("homeTeam", {})
        away_team = data.get("awayTeam", {})
        score = data.get("score", {})
        ft = score.get("fullTime", {})

        return Fixture(
            id=data.get("id", 0),
            competition_id=data.get("competition", {}).get("id"),
            competition_name=data.get("competition", {}).get("name"),
            matchday=data.get("matchday"),
            stage=data.get("stage"),
            status=data.get("status", "TBD"),
            home_team_id=home_team.get("id"),
            home_team=home_team.get("name"),
            home_team_crest=home_team.get("crest"),
            away_team_id=away_team.get("id"),
            away_team=away_team.get("name"),
            away_team_crest=away_team.get("crest"),
            home_score=ft.get("home"),
            away_score=ft.get("away"),
        )

    def _normalize_standing(self, data: dict[str, Any]) -> Standing:
        team = data.get("team", {})
        record = data.get("record", {})
        goals = data.get("goals", {})
        return Standing(
            position=data.get("position", 0),
            team_id=team.get("id", 0),
            team=team.get("name", ""),
            team_crest=team.get("crest"),
            played=record.get("played", 0),
            won=record.get("wins", 0),
            draw=record.get("draws", 0),
            lost=record.get("losses", 0),
            points=data.get("points", 0),
            goals_for=goals.get("for", 0),
            goals_against=goals.get("against", 0),
            goal_difference=data.get("goalDifference", 0),
            form=data.get("form"),
        )

    async def check_health(self) -> ProviderStatus:
        try:
            start = time.perf_counter()
            resp = await self._http.get("/status")
            elapsed = time.perf_counter() - start
            self._health.record_success(elapsed)
            if resp.status_code == 200:
                return ProviderStatus.HEALTHY
            return ProviderStatus.DEGRADED
        except Exception:
            self._health.record_failure()
            return ProviderStatus.UNHEALTHY

    async def competitions(self) -> list[Competition]:
        resp = await self._http.get("/competitions")
        data = resp.json().get("competitions", [])
        return [
            self._normalize_competition(item)
            for item in data
            if item.get("plan") == "TIER_ONE"
        ]

    async def teams(self, competition_id: int) -> list[Team]:
        resp = await self._http.get(f"/competitions/{competition_id}/teams")
        data = resp.json().get("teams", [])
        return [self._normalize_team(item) for item in data]

    async def standings(
        self, competition_id: int, season: int | None = None
    ) -> list[Standing]:
        path = f"/competitions/{competition_id}/standings"
        if season:
            path += f"?season={season}"
        resp = await self._http.get(path)
        standings_data = resp.json().get("standings", [])
        if not standings_data:
            return []
        table = standings_data[0].get("table", [])
        return [self._normalize_standing(item) for item in table]

    async def fixtures(
        self,
        competition_id: int | None = None,
        team_id: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[Fixture]:
        if competition_id:
            path = f"/competitions/{competition_id}/matches?limit={limit}"
        else:
            path = f"/matches?limit={limit}"
        params: list[str] = []
        if date_from:
            params.append(f"dateFrom={date_from}")
        if date_to:
            params.append(f"dateTo={date_to}")
        if params:
            path += "&" + "&".join(params)
        resp = await self._http.get(path)
        data = resp.json().get("matches", [])
        return [self._normalize_fixture(item) for item in data[:limit]]

    async def fixture(self, fixture_id: int) -> Fixture | None:
        resp = await self._http.get(f"/matches/{fixture_id}")
        data = resp.json()
        if "id" in data:
            return self._normalize_fixture(data)
        return None

    async def live(self) -> list[Fixture]:
        resp = await self._http.get("/matches?status=LIVE,IN_PLAY,PAUSED")
        data = resp.json().get("matches", [])
        return [self._normalize_fixture(item) for item in data]

    async def events(self, fixture_id: int) -> list[dict[str, Any]]:
        resp = await self._http.get(f"/matches/{fixture_id}")
        data: list[dict[str, Any]] = resp.json().get("events", [])
        return data

    async def statistics(self, fixture_id: int) -> list[Any]:
        return []

    async def odds(self, fixture_id: int) -> Odds | None:
        return None

    async def head_to_head(
        self, team_a_id: int, team_b_id: int, limit: int = 10
    ) -> list[Fixture]:
        resp = await self._http.get(
            f"/teams/{team_a_id}/matches?against={team_b_id}&limit={limit}"
        )
        data = resp.json().get("matches", [])
        return [self._normalize_fixture(item) for item in data]

    async def search(self, query: str) -> list[dict[str, Any]]:
        resp = await self._http.get(f"/teams?name={query}")
        data: list[dict[str, Any]] = resp.json().get("teams", [])
        return data
