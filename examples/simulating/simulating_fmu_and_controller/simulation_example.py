import sys
import os
from pathlib import Path
from sofirpy import simulate

sys.path.append(os.path.join(os.path.dirname(__file__),'../../'))

from discrete_pid import PID # custom implemented pid controller

fmu_path = Path(__file__).parent.parent.parent / "DC_Motor.fmu"

fmu_info = [
    {
        "name": "DC_Motor",
        "path": str(fmu_path),
        "connections": [
            {
                "parameter name": "u",
                "connect to system": "pid",
                "connect to external parameter": "u",
            }
        ]
    }
]


control_infos = [
    {
        "name": "pid",
        "connections": [
            {
                "parameter name": "speed",
                "connect to system": "DC_Motor",
                "connect to external parameter": "y"
            }
        ]
    }
]
pid = PID(1e-3, 3, 20, 0.1, set_point=100, u_max=100, u_min=0)
control_class = {"pid": pid}
parameters_to_log = {"DC_Motor": ["y", "MotorTorque.tau"], "pid": ["u"]}

results, units = simulate(
    stop_time=10,
    step_size=1e-3,
    fmu_infos=fmu_info,
    model_infos=control_infos,
    model_classes=control_class,
    parameters_to_log=parameters_to_log,
    get_units=True,
)
