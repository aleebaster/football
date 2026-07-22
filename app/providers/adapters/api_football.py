"""API-Football adapter (api-football.com).

Normalizes API-Football responses to internal models.
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

_BASE_URL = "https://v3.football.api-sports.io"


class ApiFootballProvider(BaseProvider):
    """API-Football data provider."""

    def __init__(self, api_key: str, priority: int = 10) -> None:
        super().__init__(name="api_football", api_key=api_key, priority=priority)
        self._http = HttpClient(
            HttpClientConfig(
                base_url=_BASE_URL,
                api_key=api_key,
                timeout=30.0,
                rate_limit=7.0,
                rate_burst=10,
                user_agent="FootballAnalytics/1.0 (api-football)",
            )
        )

    async def start(self) -> None:
        await self._http.start()

    async def stop(self) -> None:
        await self._http.stop()

    def _normalize_competition(self, data: dict[str, Any]) -> Competition:
        league = data.get("league", {})
        country = data.get("country", {})
        return Competition(
            id=league.get("id", 0),
            name=league.get("name", ""),
            code=league.get("type", None),
            country=country.get("name"),
            country_code=country.get("code"),
            emblem=league.get("logo"),
        )

    def _normalize_team(self, data: dict[str, Any]) -> Team:
        team = data.get("team", {})
        venue = data.get("venue", {})
        return Team(
            id=team.get("id", 0),
            name=team.get("name", ""),
            short_name=team.get("name"),
            tla=team.get("code"),
            country=team.get("country"),
            founded=team.get("founded"),
            venue=venue.get("name"),
            crest=team.get("logo"),
        )

    def _normalize_fixture(self, data: dict[str, Any]) -> Fixture:
        fixture_data = data.get("fixture", {})
        teams = data.get("teams", {})
        goals = data.get("goals", {})
        home_team = teams.get("home", {})
        away_team = teams.get("away", {})

        return Fixture(
            id=fixture_data.get("id", 0),
            competition_id=data.get("league", {}).get("id"),
            competition_name=data.get("league", {}).get("name"),
            matchday=data.get("league", {}).get("round"),
            status=fixture_data.get("status", {}).get("short", "TBD"),
            utc_date=None,
            home_team_id=home_team.get("id"),
            home_team=home_team.get("name"),
            home_team_crest=home_team.get("logo"),
            away_team_id=away_team.get("id"),
            away_team=away_team.get("name"),
            away_team_crest=away_team.get("logo"),
            home_score=goals.get("home"),
            away_score=goals.get("away"),
        )

    def _normalize_standing(self, data: dict[str, Any]) -> Standing:
        team = data.get("team", {})
        goals = data.get("goals", {})
        points_data = data.get("points", {})
        return Standing(
            position=data.get("rank", 0),
            team_id=team.get("id", 0),
            team=team.get("name", ""),
            team_crest=team.get("logo"),
            played=data.get("all", {}).get("played", 0),
            won=data.get("all", {}).get("win", 0),
            draw=data.get("all", {}).get("draw", 0),
            lost=data.get("all", {}).get("lose", 0),
            points=points_data.get("total", 0),
            goals_for=goals.get("for", 0),
            goals_against=goals.get("against", 0),
            goal_difference=goals.get("diff", 0),
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
        resp = await self._http.get("/leagues", params={"type": "league"})
        data = resp.json().get("response", [])
        return [self._normalize_competition(item) for item in data]

    async def teams(self, competition_id: int) -> list[Team]:
        resp = await self._http.get("/teams", params={"league": str(competition_id)})
        data = resp.json().get("response", [])
        return [self._normalize_team(item) for item in data]

    async def standings(
        self, competition_id: int, season: int | None = None
    ) -> list[Standing]:
        params: dict[str, str] = {"league": str(competition_id)}
        if season:
            params["season"] = str(season)
        resp = await self._http.get("/standings", params=params)
        data = resp.json().get("response", [])
        if not data:
            return []
        league_data = data[0].get("league", {}).get("standings", [[]])
        raw_standings = league_data[0] if league_data else []
        return [self._normalize_standing(item) for item in raw_standings]

    async def fixtures(
        self,
        competition_id: int | None = None,
        team_id: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[Fixture]:
        params: dict[str, str] = {"limit": str(limit)}
        if competition_id:
            params["league"] = str(competition_id)
        if team_id:
            params["team"] = str(team_id)
        if date_from and date_to:
            params["from"] = date_from
            params["to"] = date_to
        resp = await self._http.get("/fixtures", params=params)
        data = resp.json().get("response", [])
        return [self._normalize_fixture(item) for item in data]

    async def fixture(self, fixture_id: int) -> Fixture | None:
        resp = await self._http.get("/fixtures", params={"id": str(fixture_id)})
        data = resp.json().get("response", [])
        if not data:
            return None
        return self._normalize_fixture(data[0])

    async def live(self) -> list[Fixture]:
        resp = await self._http.get("/fixtures", params={"live": "all"})
        data = resp.json().get("response", [])
        return [self._normalize_fixture(item) for item in data]

    async def events(self, fixture_id: int) -> list[dict[str, Any]]:
        resp = await self._http.get(
            "/fixtures/events", params={"fixture": str(fixture_id)}
        )
        data: list[dict[str, Any]] = resp.json().get("response", [])
        return data

    async def statistics(self, fixture_id: int) -> list[dict[str, Any]]:
        resp = await self._http.get(
            "/fixtures/statistics", params={"fixture": str(fixture_id)}
        )
        data: list[dict[str, Any]] = resp.json().get("response", [])
        return data

    async def odds(self, fixture_id: int) -> Odds | None:
        try:
            resp = await self._http.get("/odds", params={"fixture": str(fixture_id)})
            data = resp.json().get("response", [])
            if not data:
                return None
            return Odds(
                fixture_id=fixture_id,
                bookmaker=data[0].get("bookmakers", [{}])[0].get("name"),
                last_updated=None,
            )
        except Exception:
            return None

    async def head_to_head(
        self, team_a_id: int, team_b_id: int, limit: int = 10
    ) -> list[Fixture]:
        h2h = f"{team_a_id}-{team_b_id}"
        resp = await self._http.get("/fixtures/headtohead", params={"h2h": h2h})
        data = resp.json().get("response", [])
        return [self._normalize_fixture(item) for item in data[:limit]]

    async def search(self, query: str) -> list[dict[str, Any]]:
        resp = await self._http.get("/teams", params={"search": query})
        data: list[dict[str, Any]] = resp.json().get("response", [])
        return data
