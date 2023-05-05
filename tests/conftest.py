import sys
from pathlib import Path
from typing import Union

import pytest

from sofirpy.simulation.simulation import FmuPaths, ModelInstances
from sofirpy.simulation.simulation_entity import SimulationEntity


@pytest.fixture
def fmu_paths() -> FmuPaths:
    if sys.platform == "linux" or sys.platform == "linux2":
        fmu_path = Path(__file__).parent / "simulation" / "DC_Motor_linux.fmu"
    elif sys.platform == "win32":
        fmu_path = Path(__file__).parent / "simulation" / "DC_Motor_win.fmu"
    elif sys.platform == "darwin":
        fmu_path = Path(__file__).parent / "simulation" / "DC_Motor_mac.fmu"

    return {"DC_Motor": fmu_path}


class PID(SimulationEntity):
    """Simple implementation of a discrete pid controller"""

    def __init__(
        self, step_size, K_p=1, K_i=0, K_d=0, set_point=0, u_max=1000, u_min=-1000
    ) -> None:

        self.T_a = step_size
        self.K_p = K_p
        self.K_i = K_i
        self.K_d = K_d
        self.set_point = set_point
        self.inputs = {"speed": 0}
        self.outputs = {"u": 0}
        self.d_0 = K_p * (
            1 + (self.T_a * self.K_i / self.K_p) + self.K_d / (self.K_p * self.T_a)
        )
        self.d_1 = K_p * (-1 - 2 * self.K_d / (self.K_p * self.T_a))
        self.d_2 = K_p * self.K_d / (self.K_p * self.T_a)
        self.error = [0, 0, 0]
        self.u_max = u_max
        self.u_min = u_min

    def compute_error(self) -> None:

        self.error[2] = self.error[1]
        self.error[1] = self.error[0]
        self.error[0] = self.set_point - self.inputs["speed"]

    def set_parameter(self, parameter_name, parameter_value) -> None:

        self.inputs[parameter_name] = parameter_value

    def do_step(self, _) -> None:

        self.compute_error()
        u = (
            self.outputs["u"]
            + self.d_0 * self.error[0]
            + self.d_1 * self.error[1]
            + self.d_2 * self.error[2]
        )
        if u > self.u_max or u < self.u_min:
            if u > self.u_max:
                u = self.u_max
            if u < self.u_min:
                u = self.u_min

        self.outputs["u"] = u

    def get_parameter_value(self, output_name) -> Union[int, float]:
        return self.outputs[output_name]


@pytest.fixture
def model_instances() -> ModelInstances:
    return {"pid": PID(1e-3, 3, 20, 0.1, set_point=100, u_max=100, u_min=0)}
