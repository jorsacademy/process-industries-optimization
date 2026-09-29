from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence
import warnings

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel


@dataclass(frozen=True)
class Bounds:
    lower: tuple[float, float, float] = (160.0, 3.5, 0.80)
    upper: tuple[float, float, float] = (195.0, 6.5, 1.30)

    def contains(self, x: Sequence[float]) -> bool:
        return all(
            lo <= float(v) <= hi
            for v, lo, hi in zip(x, self.lower, self.upper)
        )


@dataclass(frozen=True)
class Observation:
    batch: int
    x: tuple[float, float, float]
    yield_fraction: float
    energy: float
    quality_deviation: float
    utility: float


class SyntheticProcess:
    """Noisy three-set-point process with a controlled post-drift optimum shift."""

    def __init__(self, seed: int = 2026, drift_after: int = 15) -> None:
        self.rng = np.random.default_rng(seed)
        self.drift_after = int(drift_after)

    def evaluate(self, x: Sequence[float], batch: int) -> Observation:
        temp, pressure, feed = map(float, x)
        drift = 1.0 if batch >= self.drift_after else 0.0

        opt_t = 178.0 + 5.0 * drift
        opt_p = 4.8 + 0.35 * drift
        opt_f = 1.05 - 0.05 * drift

        yield_fraction = (
            0.955
            - 0.00032 * (temp - opt_t) ** 2
            - 0.020 * (pressure - opt_p) ** 2
            - 0.35 * (feed - opt_f) ** 2
            + self.rng.normal(0.0, 0.003)
        )
        energy = (
            20.0
            + 0.16 * temp
            + 2.5 * pressure
            + 7.0 * feed
            + self.rng.normal(0.0, 0.25)
        )
        quality_deviation = max(
            0.0,
            0.012
            + 0.0010 * abs(temp - (opt_t + 1.0))
            + 0.018 * abs(pressure - opt_p)
            + 0.11 * abs(feed - opt_f)
            + self.rng.normal(0.0, 0.002),
        )

        utility = (
            100.0 * yield_fraction
            - 0.25 * energy
            - 45.0 * quality_deviation
        )
        return Observation(
            batch=int(batch),
            x=(temp, pressure, feed),
            yield_fraction=float(yield_fraction),
            energy=float(energy),
            quality_deviation=float(quality_deviation),
            utility=float(utility),
        )


class ConstrainedBayesianController:
    def __init__(
        self,
        bounds: Bounds | None = None,
        quality_limit: float = 0.065,
        seed: int = 7,
        candidates: int = 1500,
        warmup: int = 6,
        exploration_beta: float = 1.25,
        safety_beta: float = 1.0,
    ) -> None:
        self.bounds = bounds or Bounds()
        self.quality_limit = float(quality_limit)
        self.rng = np.random.default_rng(seed)
        self.candidates = int(candidates)
        self.warmup = int(warmup)
        self.exploration_beta = float(exploration_beta)
        self.safety_beta = float(safety_beta)
        self.observations: list[Observation] = []

    def _sample_candidates(self) -> np.ndarray:
        lo = np.array(self.bounds.lower)
        hi = np.array(self.bounds.upper)
        return self.rng.uniform(lo, hi, size=(self.candidates, 3))

    @staticmethod
    def _kernel():
        return (
            ConstantKernel(1.0, (1e-2, 1e2))
            * Matern(length_scale=np.ones(3), nu=2.5)
            + WhiteKernel(
                noise_level=1e-3,
                noise_level_bounds=(1e-6, 1e-1),
            )
        )

    def recommend(self) -> tuple[float, float, float]:
        candidates = self._sample_candidates()
        if len(self.observations) < self.warmup:
            return tuple(map(float, candidates[0]))

        X = np.array([o.x for o in self.observations], dtype=float)
        utility = np.array([o.utility for o in self.observations], dtype=float)
        quality = np.array(
            [o.quality_deviation for o in self.observations],
            dtype=float,
        )

        gp_utility = GaussianProcessRegressor(
            kernel=self._kernel(),
            normalize_y=True,
            random_state=0,
            n_restarts_optimizer=0,
        )
        gp_quality = GaussianProcessRegressor(
            kernel=self._kernel(),
            normalize_y=True,
            random_state=1,
            n_restarts_optimizer=0,
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ConvergenceWarning)
            gp_utility.fit(X, utility)
            gp_quality.fit(X, quality)

        mu_u, std_u = gp_utility.predict(candidates, return_std=True)
        mu_q, std_q = gp_quality.predict(candidates, return_std=True)

        conservative_quality = mu_q + self.safety_beta * std_q
        feasible = conservative_quality <= self.quality_limit
        acquisition = mu_u + self.exploration_beta * std_u

        if np.any(feasible):
            feasible_indices = np.flatnonzero(feasible)
            idx = feasible_indices[int(np.argmax(acquisition[feasible]))]
        else:
            idx = int(np.argmin(conservative_quality))

        return tuple(map(float, candidates[idx]))

    def observe(self, observation: Observation) -> None:
        if not self.bounds.contains(observation.x):
            raise ValueError("observation is outside controller bounds")
        self.observations.append(observation)


def run_closed_loop(
    batches: int = 30,
    process_seed: int = 2026,
    controller_seed: int = 7,
    drift_after: int = 15,
    quality_limit: float = 0.065,
) -> dict[str, float | int | list[Observation]]:
    process = SyntheticProcess(
        seed=process_seed,
        drift_after=drift_after,
    )
    controller = ConstrainedBayesianController(
        quality_limit=quality_limit,
        seed=controller_seed,
    )

    observations: list[Observation] = []
    for batch in range(batches):
        x = controller.recommend()
        observation = process.evaluate(x, batch=batch)
        controller.observe(observation)
        observations.append(observation)

    utilities = np.array([o.utility for o in observations])
    violations = sum(
        o.quality_deviation > quality_limit
        for o in observations
    )
    post = (
        utilities[drift_after:]
        if drift_after < batches
        else utilities[-1:]
    )

    return {
        "mean_utility": float(np.mean(utilities)),
        "mean_post_drift_utility": float(np.mean(post)),
        "quality_violations": int(violations),
        "batches": int(batches),
        "observations": observations,
    }
