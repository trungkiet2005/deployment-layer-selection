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
from .altdynamics import basin_average_unsafe, best_response_field, logit_field
from .charges import CHANNELS, charge_thresholds, charged_matrices
from .noisy import REDUCED_DESIGNS, NoisyDesign, build_noisy_tables, generous, punisher
from .probes import probe_filter, probe_scores
from .race import (
    STRATEGIES,
    MatchupOutcome,
    RaceParams,
    RaceTables,
    build_race_tables,
    evaluate_matchup,
)

__all__ = [
    "CHANNELS",
    "REDUCED_DESIGNS",
    "STRATEGIES",
    "Functionals",
    "MatchupOutcome",
    "RaceParams",
    "RaceTables",
    "NoisyDesign",
    "aggregate_unsafe_frequency",
    "basin_average_unsafe",
    "best_response_field",
    "build_functionals",
    "build_noisy_tables",
    "build_race_tables",
    "charge_thresholds",
    "charged_matrices",
    "evaluate_matchup",
    "generous",
    "is_column_constant",
    "logit_field",
    "mean_social_payoff",
    "probe_filter",
    "probe_scores",
    "punisher",
    "strategic_distortion",
]

__version__ = "1.1.0"
