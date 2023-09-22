from __future__ import annotations

import sys
from pathlib import Path

import pytest

from sofirpy.simulation.simulation import FmuPaths, ModelClasses, StartValues
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

    def __init__(self):
        self.parameters = {
            "step_size": 1e-3,
            "K_p": 1,
            "K_i": 0,
            "K_d": 0,
            "set_point": 0,
            "u_max": 1000,
            "u_min": -1000,
        }  # TODO change step_size to Abtastrate
        self.inputs = {"speed": 0}
        self.outputs = {"u": 0}

    def compute_error(self):
        self.error[2] = self.error[1]
        self.error[1] = self.error[0]
        self.error[0] = self.parameters["set_point"] - self.inputs["speed"]

    def set_input(self, input_name, input_value):
        self.parameters[input_name] = input_value

    def do_step(self, _):
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

    def set_parameter(self, parameter_name, parameter_value) -> None:
        self.inputs[parameter_name] = parameter_value

    def get_parameter_value(self, output_name):
        return self.outputs[output_name]

    def initialize(self, start_values) -> None:
        self.apply_start_values(start_values)
        K_p = self.parameters["K_p"]
        K_i = self.parameters["K_i"]
        K_d = self.parameters["K_d"]
        T_a = self.parameters["step_size"]
        self.d_0 = K_p * (1 + (T_a * K_i / K_p) + K_d / (K_p * T_a))
        self.d_1 = K_p * (-1 - 2 * K_d / (K_p * T_a))
        self.d_2 = K_p * K_d / (K_p * T_a)
        self.error = [0, 0, 0]
        self.u_max = self.parameters["u_max"]
        self.u_min = self.parameters["u_min"]

    def apply_start_values(self, start_values: StartValues) -> None:
        for name, value in start_values.items():
            self.parameters[name] = value


@pytest.fixture
def start_values() -> StartValues:
    return {
        "pid": {
            "step_size": 1e-3,
            "K_p": 3,
            "K_i": 20,
            "K_d": 0.1,
            "set_point": 100,
            "u_max": 100,
            "u_min": 0,
        }
    }


@pytest.fixture
def model_classes() -> ModelClasses:
    return {"pid": PID}
