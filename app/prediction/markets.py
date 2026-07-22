"""Markets module — extracts market-specific inputs from feature vectors."""

from typing import Any

from app.prediction.models import PredictionMarket


class MarketMapper:
    """Maps feature keys to market-specific input dictionaries."""

    @staticmethod
    def get_winner_inputs(features: dict[str, Any]) -> dict[str, float]:
        """Extract inputs for match winner prediction."""
        return {
            "home_form_points": float(features.get("home_form_points", 0)),
            "away_form_points": float(features.get("away_form_points", 0)),
            "home_goal_diff_per_game": float(
                features.get("home_goal_diff_per_game", 0)
            ),
            "away_goal_diff_per_game": float(
                features.get("away_goal_diff_per_game", 0)
            ),
            "standings_advantage": float(features.get("standings_advantage", 0)),
            "venue_advantage": float(features.get("venue_advantage", 0)),
            "h2h_advantage": float(features.get("h2h_advantage", 0)),
            "home_momentum": float(features.get("home_momentum", 0)),
            "away_momentum": float(features.get("away_momentum", 0)),
            "odds_fair_home": float(features.get("odds_fair_home", 0)),
            "odds_fair_away": float(features.get("odds_fair_away", 0)),
        }

    @staticmethod
    def get_btts_inputs(features: dict[str, Any]) -> dict[str, float]:
        """Extract inputs for BTTS prediction."""
        return {
            "home_avg_scored": float(features.get("home_avg_scored", 0)),
            "away_avg_scored": float(features.get("away_avg_scored", 0)),
            "home_avg_conceded": float(features.get("home_avg_conceded", 0)),
            "away_avg_conceded": float(features.get("away_avg_conceded", 0)),
            "total_expected_goals": float(features.get("total_expected_goals", 0)),
        }

    @staticmethod
    def get_over_under_inputs(features: dict[str, Any]) -> dict[str, float]:
        """Extract inputs for Over/Under prediction."""
        return {
            "total_expected_goals": float(features.get("total_expected_goals", 0)),
            "home_avg_scored": float(features.get("home_avg_scored", 0)),
            "away_avg_scored": float(features.get("away_avg_scored", 0)),
            "home_avg_conceded": float(features.get("home_avg_conceded", 0)),
            "away_avg_conceded": float(features.get("away_avg_conceded", 0)),
        }

    @staticmethod
    def get_double_chance_inputs(features: dict[str, Any]) -> dict[str, float]:
        """Extract inputs for Double Chance prediction."""
        return {
            "home_form_points": float(features.get("home_form_points", 0)),
            "away_form_points": float(features.get("away_form_points", 0)),
            "standings_advantage": float(features.get("standings_advantage", 0)),
            "venue_advantage": float(features.get("venue_advantage", 0)),
            "h2h_advantage": float(features.get("h2h_advantage", 0)),
        }

    @staticmethod
    def get_odds_inputs(features: dict[str, Any]) -> dict[str, float]:
        """Extract odds data for value bet comparison."""
        return {
            "home": float(
                features.get("odds_home", 0) or features.get("odds_fair_home", 0)
            ),
            "draw": float(features.get("odds_draw", 0)),
            "away": float(
                features.get("odds_away", 0) or features.get("odds_fair_away", 0)
            ),
        }

    @classmethod
    def for_market(
        cls, market: PredictionMarket, features: dict[str, Any]
    ) -> dict[str, float]:
        """Get inputs for a specific market."""
        mapping = {
            PredictionMarket.MATCH_WINNER: cls.get_winner_inputs,
            PredictionMarket.DOUBLE_CHANCE: cls.get_double_chance_inputs,
            PredictionMarket.OVER_UNDER_25: cls.get_over_under_inputs,
            PredictionMarket.BTTS: cls.get_btts_inputs,
        }
        extractor = mapping.get(market)
        if extractor:
            return extractor(features)
        return {k: float(v) for k, v in features.items()}
