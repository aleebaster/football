"""Rule Engine - explainable rules for match outcome prediction."""

from collections.abc import Callable
from typing import Any

from app.ai.models import (
    FeatureVector,
    MatchOutcome,
    RuleResult,
)
from app.logging import get_logger

logger = get_logger(__name__)


class Rule:
    """Single rule definition."""

    def __init__(
        self,
        rule_id: str,
        name: str,
        weight: float,
        description: str,
        check: Callable[..., Any],
    ) -> None:
        self.rule_id = rule_id
        self.name = name
        self.weight = weight
        self.description = description
        self._check = check

    def evaluate(self, features: FeatureVector) -> RuleResult | None:
        """Evaluate the rule against features."""
        result = self._check(features)
        if result is None:
            return None
        outcome, impact, explanation, data_used = result
        return RuleResult(
            rule_id=self.rule_id,
            name=self.name,
            weight=self.weight,
            impact=impact,
            outcome=outcome,
            description=self.description,
            explanation=explanation,
            data_used=data_used,
        )


class RuleEngine:
    """Explainable rule engine that evaluates features against rules."""

    def __init__(self) -> None:
        self._rules: list[Rule] = []
        self._register_default_rules()

    def register(self, rule: Rule) -> None:
        self._rules.append(rule)

    def __len__(self) -> int:
        return len(self._rules)

    def evaluate(self, features: FeatureVector) -> list[RuleResult]:
        """Evaluate all rules and return results."""
        results = []
        for rule in self._rules:
            try:
                result = rule.evaluate(features)
                if result is not None:
                    results.append(result)
            except Exception as e:
                logger.warning(f"Rule {rule.rule_id} failed: {e}")

        # Sort by absolute impact (strongest rules first)
        results.sort(key=lambda r: abs(r.weight * r.impact), reverse=True)
        return results

    def _register_default_rules(self) -> None:
        """Register built-in rules."""

        def form_rule(
            fv: FeatureVector,
        ) -> tuple[MatchOutcome, float, str, list[str]] | None:
            hp = fv.get("home_form_points", 0)
            ap = fv.get("away_form_points", 0)
            if hp == 0 and ap == 0:
                return None
            diff = (hp - ap) / 15.0
            if abs(diff) < 0.07:
                return None
            outcome = MatchOutcome.HOME_WIN if diff > 0 else MatchOutcome.AWAY_WIN
            return (
                outcome,
                max(-1, min(1, diff * 1.5)),
                f"Home form ({hp}/15) vs Away form ({ap}/15)",
                ["home_form_points", "away_form_points"],
            )

        self.register(
            Rule(
                "form",
                "Team Form",
                0.20,
                "Recent form comparison over last 5 matches",
                form_rule,
            )
        )

        def standings_rule(
            fv: FeatureVector,
        ) -> tuple[MatchOutcome, float, str, list[str]] | None:
            adv = fv.get("standings_advantage", 0)
            if abs(adv) < 0.05:
                return None
            outcome = MatchOutcome.HOME_WIN if adv > 0 else MatchOutcome.AWAY_WIN
            return (
                outcome,
                max(-1, min(1, adv * 2)),
                f"League position advantage: home #{fv.get('home_position', '?')} vs away #{fv.get('away_position', '?')}",
                ["home_position", "away_position", "standings_advantage"],
            )

        self.register(
            Rule(
                "standings",
                "League Position",
                0.20,
                "Relative position in the league table",
                standings_rule,
            )
        )

        def venue_rule(
            fv: FeatureVector,
        ) -> tuple[MatchOutcome, float, str, list[str]] | None:
            adv = fv.get("venue_advantage", 0)
            if abs(adv) < 0.1:
                return None
            outcome = MatchOutcome.HOME_WIN if adv > 0 else MatchOutcome.AWAY_WIN
            return (
                outcome,
                max(-1, min(1, adv)),
                f"Home ppg {fv.get('home_home_ppg', 0):.2f} vs Away ppg {fv.get('away_away_ppg', 0):.2f} on the road",
                ["home_home_ppg", "away_away_ppg", "venue_advantage"],
            )

        self.register(
            Rule(
                "venue",
                "Home Advantage",
                0.15,
                "Historical home vs away performance",
                venue_rule,
            )
        )

        def h2h_rule(
            fv: FeatureVector,
        ) -> tuple[MatchOutcome, float, str, list[str]] | None:
            if not fv.get("h2h_available", False):
                return None
            adv = fv.get("h2h_advantage", 0)
            if abs(adv) < 0.15:
                return None
            outcome = MatchOutcome.HOME_WIN if adv > 0 else MatchOutcome.AWAY_WIN
            hw = fv.get("h2h_home_win_rate", 0)
            aw = fv.get("h2h_away_win_rate", 0)
            return (
                outcome,
                max(-1, min(1, adv)),
                f"H2H: home wins {hw:.0%}, away wins {aw:.0%}",
                ["h2h_home_win_rate", "h2h_away_win_rate"],
            )

        self.register(
            Rule(
                "h2h",
                "Head-to-Head",
                0.15,
                "Historical head-to-head results",
                h2h_rule,
            )
        )

        def goals_rule(
            fv: FeatureVector,
        ) -> tuple[MatchOutcome, float, str, list[str]] | None:
            hgd = fv.get("home_goal_diff_per_game", 0)
            agd = fv.get("away_goal_diff_per_game", 0)
            diff = hgd - agd
            if abs(diff) < 0.2:
                return None
            outcome = MatchOutcome.HOME_WIN if diff > 0 else MatchOutcome.AWAY_WIN
            return (
                outcome,
                max(-1, min(1, diff)),
                f"Goal difference per game: home {hgd:+.2f} vs away {agd:+.2f}",
                ["home_goal_diff_per_game", "away_goal_diff_per_game"],
            )

        self.register(
            Rule(
                "goals",
                "Goal Difference",
                0.15,
                "Goals scored minus conceded per game",
                goals_rule,
            )
        )

        def momentum_rule(
            fv: FeatureVector,
        ) -> tuple[MatchOutcome, float, str, list[str]] | None:
            hm = fv.get("home_momentum", 0)
            am = fv.get("away_momentum", 0)
            diff = hm - am
            if abs(diff) < 0.2:
                return None
            outcome = MatchOutcome.HOME_WIN if diff > 0 else MatchOutcome.AWAY_WIN
            return (
                outcome,
                max(-1, min(1, diff * 0.8)),
                f"Momentum: home {hm:.0%} wins last 3 vs away {am:.0%}",
                ["home_momentum", "away_momentum"],
            )

        self.register(
            Rule(
                "momentum",
                "Momentum",
                0.10,
                "Recent momentum and win streaks",
                momentum_rule,
            )
        )

        def odds_rule(
            fv: FeatureVector,
        ) -> tuple[MatchOutcome, float, str, list[str]] | None:
            if not fv.get("odds_available", False):
                return None
            fh = fv.get("odds_fair_home", 0)
            fa = fv.get("odds_fair_away", 0)
            if fh == 0 and fa == 0:
                return None
            diff = fh - fa
            if abs(diff) < 0.05:
                return None
            outcome = MatchOutcome.HOME_WIN if diff > 0 else MatchOutcome.AWAY_WIN
            return (
                outcome,
                max(-1, min(1, diff * 1.5)),
                f"Market implied: home {fh:.1%}, away {fa:.1%}",
                ["odds_fair_home", "odds_fair_away"],
            )

        self.register(
            Rule(
                "odds",
                "Market Odds",
                0.05,
                "Betting market implied probabilities",
                odds_rule,
            )
        )
