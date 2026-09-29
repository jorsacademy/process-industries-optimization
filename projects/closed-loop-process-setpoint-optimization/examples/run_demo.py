from __future__ import annotations

import json

from closed_loop_setpoint import run_closed_loop

result = run_closed_loop(
    batches=30,
    process_seed=2026,
    controller_seed=17,
    drift_after=15,
)

print(
    json.dumps(
        {
            "mean_utility": result["mean_utility"],
            "mean_post_drift_utility": result["mean_post_drift_utility"],
            "quality_violations": result["quality_violations"],
            "batches": result["batches"],
            "last_five_setpoints": [
                {
                    "batch": o.batch,
                    "temperature": o.x[0],
                    "pressure": o.x[1],
                    "feed_rate": o.x[2],
                    "quality_deviation": o.quality_deviation,
                    "utility": o.utility,
                }
                for o in result["observations"][-5:]
            ],
        },
        indent=2,
    )
)
