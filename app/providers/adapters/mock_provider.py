"""Mock provider for testing and development.

Returns fake football data without API calls.
"""

import random
from datetime import UTC, datetime, timedelta

from app.logging import get_logger
from app.providers.base import BaseProvider
from app.providers.models import (
    Competition,
    Fixture,
    Odds,
    OddsMarket,
    OddsOutcome,
    ProviderStatus,
    Standing,
    Team,
)

logger = get_logger(__name__)

# Sample data
_COMPETITIONS = [
    Competition(
        id=1, name="Premier League", code="PL", country="England", country_code="GB"
    ),
    Competition(id=2, name="La Liga", code="LL", country="Spain", country_code="ES"),
    Competition(
        id=3, name="Bundesliga", code="BL", country="Germany", country_code="DE"
    ),
    Competition(id=4, name="Serie A", code="SA", country="Italy", country_code="IT"),
    Competition(id=5, name="Ligue 1", code="L1", country="France", country_code="FR"),
    Competition(
        id=6,
        name="Ukrainian Premier League",
        code="UPL",
        country="Ukraine",
        country_code="UA",
    ),
]

_TEAMS: dict[int, list[Team]] = {
    1: [
        Team(id=101, name="Arsenal", short_name="Arsenal", tla="ARS"),
        Team(id=102, name="Manchester City", short_name="Man City", tla="MCI"),
        Team(id=103, name="Liverpool", short_name="Liverpool", tla="LIV"),
        Team(id=104, name="Chelsea", short_name="Chelsea", tla="CHE"),
        Team(id=105, name="Manchester United", short_name="Man Utd", tla="MUN"),
    ],
    6: [
        Team(id=601, name="Shakhtar Donetsk", short_name="Shakhtar", tla="SHK"),
        Team(id=602, name="Dynamo Kyiv", short_name="Dynamo", tla="DKV"),
        Team(id=603, name="Zorya Luhansk", short_name="Zorya", tla="ZOR"),
    ],
}


class MockProvider(BaseProvider):
    """Mock provider returning fake football data."""

    def __init__(self, priority: int = 100) -> None:
        super().__init__(name="mock", api_key="", priority=priority)

    async def check_health(self) -> ProviderStatus:
        return ProviderStatus.HEALTHY

    async def competitions(self) -> list[Competition]:
        return list(_COMPETITIONS)

    async def teams(self, competition_id: int) -> list[Team]:
        return list(_TEAMS.get(competition_id, []))

    async def standings(
        self, competition_id: int, season: int | None = None
    ) -> list[Standing]:
        teams = _TEAMS.get(competition_id, [])
        standings = []
        for i, team in enumerate(teams):
            played = random.randint(10, 38)
            won = random.randint(0, played)
            draw = random.randint(0, played - won)
            lost = played - won - draw
            gf = random.randint(won, won * 3)
            ga = random.randint(0, lost * 2)
            standings.append(
                Standing(
                    position=i + 1,
                    team_id=team.id,
                    team=team.name,
                    played=played,
                    won=won,
                    draw=draw,
                    lost=lost,
                    points=won * 3 + draw,
                    goals_for=gf,
                    goals_against=ga,
                    goal_difference=gf - ga,
                )
            )
        standings.sort(key=lambda s: s.points, reverse=True)
        for i, s in enumerate(standings):
            s.position = i + 1
        return standings

    async def fixtures(
        self,
        competition_id: int | None = None,
        team_id: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[Fixture]:
        now = datetime.now(UTC)
        fixtures = []
        for i in range(min(limit, 10)):
            home = random.choice([101, 102, 103, 104, 105])
            away = random.choice([h for h in [101, 102, 103, 104, 105] if h != home])
            fixtures.append(
                Fixture(
                    id=1000 + i,
                    competition_id=competition_id or 1,
                    competition_name="Premier League",
                    matchday=random.randint(1, 38),
                    status="SCHEDULED",
                    utc_date=now + timedelta(days=random.randint(0, 30)),
                    home_team_id=home,
                    home_team=f"Team {home}",
                    away_team_id=away,
                    away_team=f"Team {away}",
                    home_score=None,
                    away_score=None,
                )
            )
        return fixtures

    async def fixture(self, fixture_id: int) -> Fixture | None:
        return Fixture(
            id=fixture_id,
            competition_id=1,
            competition_name="Premier League",
            matchday=15,
            status="SCHEDULED",
            utc_date=datetime.now(UTC) + timedelta(days=3),
            home_team_id=101,
            home_team="Arsenal",
            away_team_id=102,
            away_team="Manchester City",
        )

    async def live(self) -> list[Fixture]:
        return [
            Fixture(
                id=9999,
                competition_id=1,
                competition_name="Premier League",
                status="IN_PLAY",
                utc_date=datetime.now(UTC),
                home_team_id=101,
                home_team="Arsenal",
                away_team_id=103,
                away_team="Liverpool",
                home_score=1,
                away_score=0,
            )
        ]

    async def events(self, fixture_id: int) -> list[dict[str, object]]:
        return [
            {"type": "Goal", "player": "Saka", "elapsed": 23, "team": "Arsenal"},
            {
                "type": "YellowCard",
                "player": "Salah",
                "elapsed": 45,
                "team": "Liverpool",
            },
        ]

    async def statistics(self, fixture_id: int) -> list[dict[str, object]]:
        return [
            {"type": "Shots on Goal", "home": 5, "away": 3},
            {"type": "Ball Possession", "home": "62%", "away": "38%"},
        ]

    async def odds(self, fixture_id: int) -> Odds | None:
        return Odds(
            fixture_id=fixture_id,
            bookmaker="MockBook",
            markets=[
                OddsMarket(
                    name="Match Winner",
                    outcomes=[
                        OddsOutcome(name="Home", value=1.85),
                        OddsOutcome(name="Draw", value=3.50),
                        OddsOutcome(name="Away", value=4.20),
                    ],
                )
            ],
        )

    async def head_to_head(
        self, team_a_id: int, team_b_id: int, limit: int = 10
    ) -> list[Fixture]:
        return [
            Fixture(
                id=5000 + i,
                home_team_id=team_a_id,
                home_team=f"Team {team_a_id}",
                away_team_id=team_b_id,
                away_team=f"Team {team_b_id}",
                home_score=random.randint(0, 3),
                away_score=random.randint(0, 3),
                status="FINISHED",
                utc_date=datetime.now(UTC) - timedelta(days=30 * (i + 1)),
            )
            for i in range(min(limit, 5))
        ]

    async def search(self, query: str) -> list[dict[str, object]]:
        results = []
        for comp in _COMPETITIONS:
            if query.lower() in comp.name.lower():
                results.append(
                    {"type": "competition", "id": comp.id, "name": comp.name}
                )
        for teams in _TEAMS.values():
            for team in teams:
                if query.lower() in team.name.lower():
                    results.append({"type": "team", "id": team.id, "name": team.name})
        return results
