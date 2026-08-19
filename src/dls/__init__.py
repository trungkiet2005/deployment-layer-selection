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
from .assortment import assorted_tables, assortment_thresholds, closing_assortment
from .charges import CHANNELS, charge_thresholds, charged_matrices
from .noisy import (
    REDUCED_DESIGNS,
    NoisyDesign,
    build_noisy_tables,
    generous,
    grim,
    punisher,
)
from .observation import (
    MeasurementModel,
    attribution_thresholds,
    delayed_replicator,
    measured_tables,
    measurement_is_inert,
)
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
    "Functionals",
    "MatchupOutcome",
    "MeasurementModel",
    "NoisyDesign",
    "REDUCED_DESIGNS",
    "RaceParams",
    "RaceTables",
    "STRATEGIES",
    "aggregate_unsafe_frequency",
    "assorted_tables",
    "assortment_thresholds",
    "attribution_thresholds",
    "basin_average_unsafe",
    "best_response_field",
    "build_functionals",
    "build_noisy_tables",
    "build_race_tables",
    "charge_thresholds",
    "charged_matrices",
    "closing_assortment",
    "delayed_replicator",
    "evaluate_matchup",
    "generous",
    "grim",
    "is_column_constant",
    "logit_field",
    "mean_social_payoff",
    "measured_tables",
    "measurement_is_inert",
    "probe_filter",
    "probe_scores",
    "punisher",
    "strategic_distortion",
]

__version__ = "1.2.0"
