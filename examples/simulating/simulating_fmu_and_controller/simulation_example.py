import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt

from sofirpy import plot_results, simulate

sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from discrete_pid import PID  # custom implemented pid controller

if sys.platform == "win32":
    fmu_path = Path(__file__).parent.parent.parent / "DC_Motor.fmu"
elif sys.platform == "darwin":
    fmu_path = Path(__file__).parent.parent.parent / "DC_Motor_mac.fmu"


connections_config = {
    "DC_Motor": [
        {
            "parameter_name": "u",
            "connect_to_system": "pid",
            "connect_to_external_parameter": "u",
        }
    ],
    "pid": [
        {
            "parameter_name": "speed",
            "connect_to_system": "DC_Motor",
            "connect_to_external_parameter": "y",
        }
    ],
}

fmu_paths = {"DC_Motor": str(fmu_path)}


model_classes = {"pid": PID}

parameters_to_log = {
    "DC_Motor": ["y", "MotorTorque.tau", "inertia.J", "dC_PermanentMagnet.Jr"],
    "pid": ["u"],
}

start_values = {
    "DC_Motor": {"inertia.J": 2, "damper.phi_rel.start": (1, "deg")},
    "pid": {
        "step_size": 1e-3,
        "K_p": 3,
        "K_i": 20,
        "K_d": 0.1,
        "set_point": 100,
        "u_max": 100,
        "u_min": 0,
    },
}

results, units = simulate(
    stop_time=10,
    step_size=1e-3,
    fmu_paths=fmu_paths,
    model_classes=model_classes,
    connections_config=connections_config,
    start_values=start_values,
    parameters_to_log=parameters_to_log,
    logging_step_size=1e-3,
    get_units=True,
)

ax, fig = plot_results(
    results,
    "time",
    "DC_Motor.y",
    x_label="time in s",
    y_label="speed in rad/s",
    title="Speed over Time",
)
