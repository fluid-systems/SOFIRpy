import os
import sys
from pathlib import Path

from sofirpy import BaseSimulator
from sofirpy.common import Connection

sys.path.append(os.path.join(os.path.dirname(__file__), "../"))

from discrete_pid import PID  # custom implemented pid controller

if sys.platform == "win32":
    fmu_path = Path(__file__).parent.parent / "DC_Motor.fmu"
elif sys.platform == "linux":
    fmu_path = Path(__file__).parent.parent / "DC_Motor_linux.fmu"
elif sys.platform == "darwin":
    fmu_path = Path(__file__).parent.parent / "DC_Motor_mac.fmu"

connections_config = {
    "DC_Motor": [
        Connection(
            parameter_name="u",
            connect_to_system="pid",
            connect_to_external_parameter="u",
        )
    ],
    "pid": [
        Connection(
            parameter_name="speed",
            connect_to_system="DC_Motor",
            connect_to_external_parameter="y",
        ),
    ],
}

fmu_paths = {"DC_Motor": str(fmu_path)}


model_classes = {"pid": PID}


init_configs = {
    "DC_Motor": {"start_values": {"inertia.J": 2, "damper.phi_rel.start": (1, "deg")}},
    "pid": {
        "start_values": {
            "step_size": 1e-3,
            "K_p": 3,
            "K_i": 20,
            "K_d": 0.1,
            "set_point": 100,
            "u_max": 100,
            "u_min": 0,
        },
    },
}

simulator = BaseSimulator(
    fmu_paths=fmu_paths,
    model_classes=model_classes,
    init_configs=init_configs,
    connections_config=connections_config,
)

stop_time = 100
step_size = 1
while simulator.time < stop_time:
    simulator.do_step(simulator.time, step_size)
    simulator.set_systems_inputs()
    simulator.time += step_size
simulator.conclude_simulation()