from pathlib import Path

import numpy as np
import pandas as pd


def test_simulation_example():
    from simulation_example import results, units

    test_results = pd.read_csv(Path(__file__).parent / "test_data.csv").to_numpy()
    results = results.to_numpy()
    assert np.isclose(results, test_results, atol=1e-6).all()
    test_units = {
        "DC_Motor.y": None,
        "DC_Motor.MotorTorque.tau": "N.m",
        "DC_Motor.inertia.J": "kg.m2",
        "DC_Motor.dC_PermanentMagnet.Jr": "kg.m2",
        "pid.u": None,
    }
    assert units == test_units
