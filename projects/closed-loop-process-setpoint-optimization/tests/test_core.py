from closed_loop_setpoint import (
    Bounds,
    ConstrainedBayesianController,
    SyntheticProcess,
    run_closed_loop,
)


def test_recommendations_stay_inside_bounds():
    bounds = Bounds()
    process = SyntheticProcess(seed=3, drift_after=50)
    controller = ConstrainedBayesianController(
        bounds=bounds,
        seed=5,
        candidates=200,
    )

    for batch in range(10):
        x = controller.recommend()
        assert bounds.contains(x)
        controller.observe(process.evaluate(x, batch))


def test_closed_loop_is_reproducible():
    a = run_closed_loop(
        batches=12,
        process_seed=9,
        controller_seed=10,
        drift_after=6,
    )
    b = run_closed_loop(
        batches=12,
        process_seed=9,
        controller_seed=10,
        drift_after=6,
    )

    assert a["mean_utility"] == b["mean_utility"]
    assert a["quality_violations"] == b["quality_violations"]
    assert [o.x for o in a["observations"]] == [
        o.x for o in b["observations"]
    ]


def test_process_exposes_quality_penalty_at_extreme_setpoint():
    process = SyntheticProcess(seed=1, drift_after=100)
    near = process.evaluate((178.0, 4.8, 1.05), batch=0)
    extreme = process.evaluate((195.0, 6.5, 1.30), batch=1)

    assert extreme.quality_deviation > near.quality_deviation
