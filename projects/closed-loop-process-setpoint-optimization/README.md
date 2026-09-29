# Closed-Loop Process Set-Point Optimization

A reproducible benchmark for adaptive process set-point recommendation under noisy observations, a safety/quality constraint and controlled process drift.

The project turns the broad idea of "AI process optimization" into an inspectable loop:

```text
set-point recommendation
  -> process response
  -> yield / energy / quality observation
  -> Gaussian-process surrogate update
  -> constrained acquisition
  -> next set-point
```

It is independent of C3 AI, modeFRONTIER, Siemens, DELMIA or any other commercial platform.

## Synthetic process

Each batch has three controllable set-points:

- temperature;
- pressure;
- feed rate.

The simulator returns:

- yield fraction;
- energy use;
- quality deviation;
- scalar operating utility.

The utility combines yield, energy and quality deviation:

```text
utility
= 100 * yield
- 0.25 * energy
- 45 * quality_deviation
```

A controlled optimum shift occurs after `drift_after` batches. This creates an adaptation problem rather than a one-shot black-box optimization exercise.

## Controller

`ConstrainedBayesianController` fits separate Gaussian-process models for:

1. operating utility;
2. quality deviation.

Candidate points are screened using a conservative quality estimate:

```text
predicted_quality_mean
+ safety_beta * predicted_quality_std
<= quality_limit
```

Among screened candidates, the controller maximizes an upper-confidence-bound utility acquisition. If no candidate passes the safety screen, it selects the candidate with the lowest conservative quality estimate.

The first few batches are random warm-up experiments because no useful surrogate exists initially.

## Why this is a decision-system benchmark

The project deliberately evaluates a sequence of **recommend -> observe -> update -> recommend** decisions. It therefore exposes several industrial questions that a one-shot optimizer hides:

- exploration versus exploitation;
- constraint violations;
- surrogate uncertainty;
- adaptation after process drift;
- reproducibility under fixed noise streams.

## Run

```bash
python -m pip install -e ".[dev]"
pytest
python examples/run_demo.py
```

The demo reports mean utility, post-drift utility, quality violations and the final set-point recommendations.

## Scope and limitations

- The plant is synthetic; coefficients are not calibrated to a named process.
- The quality screen is model-based, not a certified safety layer.
- Candidate optimization uses random candidate pools rather than continuous acquisition optimization.
- The GP assumes stationary covariance even though the process deliberately drifts.
- A production implementation should add hard engineering interlocks, time-varying models, operator approval, model-monitoring gates and rollback logic.
- Natural extensions include model predictive control, robust/constrained Bayesian optimization, multi-objective Pareto policies and online change-point detection.
