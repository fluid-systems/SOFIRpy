import sys
import os
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__),'../../'))

from sofirpy import simulate, SimulationEntity

class PID(SimulationEntity):
    """Simple implementation of a discrete pid controller"""

    def __init__(
        self, step_size, K_p=1, K_i=0, K_d=0, set_point=0, u_max=1000, u_min=-1000
    ):

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

    def compute_error(self):

        self.error[2] = self.error[1]
        self.error[1] = self.error[0]
        self.error[0] = self.set_point - self.inputs["speed"]

    def set_input(self, input_name, input_value):  # mandatory methode

        self.inputs[input_name] = input_value

    def do_step(self, _):  # mandatory methode

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

    def get_parameter_value(self, output_name):  # mandatory methode
        return self.outputs[output_name]

def test_simulation() -> None:

    fmu_path = Path(__file__).parent / "DC_Motor.fmu"

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
        get_units=True
    )
    assert units == {
        'DC_Motor.y': 'rad/s',
        'DC_Motor.MotorTorque.tau': 'N.m',
        'pid.u': None}

    test_results = pd.read_csv(Path(__file__).parent / "test_results.csv")
    test_results = test_results.to_numpy()
    results = results.to_numpy()
    assert np.isclose(results, test_results, atol=1e-6).all()