from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from sofirpy.simulation.simulation import (
    SimulationEntity,
    simulate,
    _validate_fmu_infos,
    _validate_input
    )


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

    def set_input(self, input_name, input_value):

        self.inputs[input_name] = input_value

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

    def get_parameter_value(self, output_name):
        return self.outputs[output_name]

@pytest.fixture
def fmu_info() -> dict:
    return [
        {
            "name": "DC_Motor",
            "path": str(Path(__file__).parent / "DC_Motor.fmu"),
            "connections": [
                {
                    "parameter name": "u",
                    "connect to system": "pid",
                    "connect to external parameter": "u",
                }
            ],
        }
    ]

@pytest.fixture
def model_info() -> dict:
    return [
        {
            "name": "pid",
            "connections": [
                {
                    "parameter name": "speed",
                    "connect to system": "DC_Motor",
                    "connect to external parameter": "y",
                }
            ],
        }
    ]

@pytest.fixture
def pid() -> PID:
    return PID(1e-3, 3, 20, 0.1, set_point=100, u_max=100, u_min=0)

def test_simulation(fmu_info: list[dict], model_info: list[dict], pid: PID) -> None:

    control_class = {"pid": pid}
    parameters_to_log = {"DC_Motor": ["y", "MotorTorque.tau"], "pid": ["u"]}
    results, units = simulate(
        stop_time=2,
        step_size=1e-3,
        fmu_infos=fmu_info,
        model_infos=model_info,
        model_classes=control_class,
        parameters_to_log=parameters_to_log,
        get_units=True,
    )
    assert units == {
        "DC_Motor.y": "rad/s",
        "DC_Motor.MotorTorque.tau": "N.m",
        "pid.u": None,
    }

    test_results = pd.read_csv(Path(__file__).parent / "test_results.csv")
    test_results = test_results.to_numpy()
    results = results.to_numpy()
    assert np.isclose(results, test_results, atol=1e-6).all()

def test_validate_input_duplicate_name_value_error(fmu_info: list[dict], model_info: list[dict]) -> None:

    model_info[0]["name"] = fmu_info[0]["name"]
    with pytest.raises(ValueError, match= "Duplicate names in system infos."):
        _validate_input(
            1,
            0.1,
            fmu_info,
            model_info
        )



def test_simulate_with_no_parameters_to_log(fmu_info: list[dict], model_info: list[dict], pid: PID) -> None:

    control_class = {"pid": pid}

    results = simulate(
        stop_time=2,
        step_size=1e-3,
        fmu_infos=fmu_info,
        model_infos=model_info,
        model_classes=control_class,
    )

    test_results = pd.read_csv(Path(__file__).parent / "test_results.csv", usecols = ["time"])
    test_results = test_results.to_numpy()
    results = results.to_numpy()
    assert np.isclose(results, test_results, atol=1e-6).all()

@pytest.mark.parametrize(
    "fmu_info", [
        [
        {
            "path": str(Path(__file__).parent / "DC_Motor.fmu"),
            "connections": [
                {
                    "parameter name": "u",
                    "connect to system": "pid",
                    "connect to external parameter": "u",
                }
            ],
        }
        ],
        [
        {
            "name": "DC_Motor",
            "path": str(Path(__file__).parent / "DC_Motor.fmu"),
            "connections": [
                {
                    "parameter name": "u",
                    "connect to system": "pid",
                    "connect to external parameter": "u",
                }
            ],
        },
        {
            "name": "DC_Motor",
            "connections": [
                {
                    "parameter name": "u",
                    "connect to system": "pid",
                    "connect to external parameter": "u",
                }
            ],
        }
        ],
        [
        {
            "path": str(Path(__file__).parent / "DC_Motor.fmu"),
            "connections": [
                {
                    "connect to system": "pid",
                    "connect to external parameter": "u",
                }
            ],
        },
    ],
    [
        {
            "path": str(Path(__file__).parent / "DC_Motor.fmu"),
            "connections": [
                {
                    "parameter name": "u",
                    "connect to external parameter": "u",
                }
            ],
        },
    ],
    [
        {
            "path": str(Path(__file__).parent / "DC_Motor.fmu"),
            "connections": [
                {
                    "parameter name": "u",
                    "connect to system": "pid"
                }
            ],
        },
    ]
    ]
    )
def test_validate_fmu_info_key_error(fmu_info: list[dict]) -> None:

    with pytest.raises(KeyError):
        _validate_fmu_infos(fmu_info)
