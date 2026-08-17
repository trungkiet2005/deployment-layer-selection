"""Deployment-layer selection in evolutionary AI-race dynamics.

The package separates the layer at which an AI design *acts* from the layer at
which it is *selected*, and studies the resulting evolutionary dynamics.
"""

from .functionals import (
    Functionals,
    aggregate_unsafe_frequency,
    build_functionals,
    is_column_constant,
    mean_social_payoff,
    strategic_distortion,
)
from .race import (
    STRATEGIES,
    MatchupOutcome,
    RaceParams,
    RaceTables,
    build_race_tables,
    evaluate_matchup,
)

__all__ = [
    "STRATEGIES",
    "Functionals",
    "MatchupOutcome",
    "RaceParams",
    "RaceTables",
    "aggregate_unsafe_frequency",
    "build_functionals",
    "build_race_tables",
    "evaluate_matchup",
    "is_column_constant",
    "mean_social_payoff",
    "strategic_distortion",
]

__version__ = "1.0.0"
