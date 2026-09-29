# Process Industries Optimization

<!-- portfolio-umbrella:start -->
## Portfolio role

This repository is the primary umbrella repository for this Jors Academy research area. Related projects have been consolidated under `projects/` so the methods, implementations, experiments, and case studies can be maintained and explored from one place.

### Included projects

- [`chemical-batch-process-design-minlp`](projects/chemical-batch-process-design-minlp/)
- [`crude-oil-pipeline-network-optimization`](projects/crude-oil-pipeline-network-optimization/)
- [`gas-processing-plant-milp-optimization-python`](projects/gas-processing-plant-milp-optimization-python/)
- [`oil-refinery-optimization-pulp`](projects/oil-refinery-optimization-pulp/)
- [`transco-germanium-optimization-refining`](projects/transco-germanium-optimization-refining/)
- [`world-aluminum-investment-optimization`](projects/world-aluminum-investment-optimization/)
- [`closed-loop-process-setpoint-optimization`](projects/closed-loop-process-setpoint-optimization/) — native constrained Bayesian optimization benchmark with process drift

Consolidated source projects keep their own files and a `SOURCE_REPOSITORY.md` provenance record. The native closed-loop set-point project is maintained directly in this umbrella repository. Source snapshots preserve the original default-branch files at consolidation time; repository-level history and metadata remain separate from the snapshots.
<!-- portfolio-umbrella:end -->

A compact linear programming model for a simplified petroleum refinery network using Python and PuLP.

The model represents crude distillation, naphtha reforming, oil cracking, residue allocation, final product blending, process capacities, lubricant production bounds, and product-value maximization.

## Why this version exists

An earlier formulation of this model contained several structural LP errors. The corrected version in this repository fixes those issues by enforcing material conservation throughout the refinery network.

The previous formulation could become unbounded because final petrol production was not linked to physical component flows. It also omitted several intermediate stream balances, applied reforming capacity separately to each naphtha grade instead of globally, and applied lubricant lower bounds to each residue-product pair instead of to final lubricant production.

This repository treats those issues as modeling errors, not solver issues.

## Model structure

The network contains:

- three crude feeds
- two naphtha streams
- two oil streams
- two residue streams
- two reformer products
- two cracker products
- two petrol products
- two fuel products
- two lubricant products

The principal flow is:

```text
Crude
  |
  v
Distillation
  |------------------|------------------|
  v                  v                  v
Naphtha              Oil                Residue
  |                   |                  |
  |--> direct petrol  |--> direct fuel   |--> lubricant
  |                   |                  |--> fuel
  v                   v
Reforming            Cracking
  |                   |-------> petrol
  v                   |-------> fuel
Petrol
```

## Corrections made to the original formulation

1. Added naphtha conservation constraints.
2. Replaced per-naphtha reformer limits with one global reformer-capacity constraint.
3. Linked reformer output to downstream petrol blending.
4. Added oil conservation constraints.
5. Linked cracker products to final petrol and fuel streams.
6. Linked final petrol variables to all contributing physical streams.
7. Linked final fuel variables to direct oil, cracked product, and residue streams.
8. Removed lubricant lower bounds from individual residue-to-lubricant component variables.
9. Applied lubricant lower and upper bounds only to final lubricant production.
10. Added residue conservation constraints.
11. Added solver-status validation so infeasible or unbounded models are not reported as valid solutions.

## Important modeling limitation

The supplied data does not include product-quality specifications such as octane, sulfur, viscosity, density, or minimum/maximum blending fractions.

Therefore the two petrol grades and two fuel grades are economically differentiated only by their objective coefficients. With no additional quality constraints, the optimizer is free to assign interchangeable components to the higher-value product. This is a limitation of the supplied data rather than a PuLP limitation.

The distillation coefficients should also be interpreted cautiously. For some crude types, the listed coefficients across all distillation products sum to more than 1.0. If these coefficients are intended to represent physical mass yields, that would be inconsistent. The repository preserves the supplied numerical data rather than inventing replacement yield values.

## Objective

The current objective maximizes the aggregate value of final petrol, fuel, and lubricant production:

```text
maximize
    petrol value
  + fuel value
  + lubricant value
```

No crude purchase costs, process operating costs, utility costs, or disposal costs were supplied. For that reason, the objective should be interpreted as maximum product value or contribution value rather than full refinery profit.

## Installation

```bash
python -m venv .venv
```

Activate the environment, then install dependencies:

```bash
pip install -r requirements.txt
```

## Run

```bash
python refinery_lp.py
```

The script checks the solver status before printing the objective and decision variables.

## Tests

Run:

```bash
pytest -q
```

The tests verify optimal solver status, bounded objective value, process capacities, material balances, final-product linkage, and lubricant production bounds.

## Main files

```text
.
├── README.md
├── NONCOMMERCIAL.md
├── requirements.txt
├── refinery_lp.py
└── tests/
    └── test_refinery_lp.py
```

## Use restriction

Commercial use is prohibited. See `NONCOMMERCIAL.md`.

The repository is source-available and should not be described as OSI-approved open-source software.

## Possible extensions

A more realistic refinery-planning model could add crude procurement costs, processing costs, product demand limits, blending-quality equations, sulfur and octane constraints, process losses, inventory, multiple planning periods, and marginal-value or sensitivity analysis.
