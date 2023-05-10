import sys
from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd
import pytest

from sofirpy.simulation.simulation import (
    ConnectionsConfig,
    FmuPaths,
    ModelInstances,
    ParametersToLog,
    StartValues,
    _validate_input,
    _validate_parameters_to_log,
    simulate,
)


@pytest.fixture
def connections_config() -> ConnectionsConfig:
    return {
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


@pytest.fixture
def parameters_to_log() -> ParametersToLog:
    return {"DC_Motor": ["y", "MotorTorque.tau"], "pid": ["u"]}


@pytest.fixture
def system_names() -> dict:
    return ["DC_Motor", "pid"]


@pytest.fixture
def result_path() -> Path:
    return Path(__file__).parent / "test_results.csv"


def test_simulation(
    connections_config: ConnectionsConfig,
    fmu_paths: FmuPaths,
    model_instances: ModelInstances,
    start_values: StartValues,
    result_path: Path,
    parameters_to_log: ParametersToLog,
) -> None:

    results, units = simulate(
        stop_time=2,
        step_size=1e-3,
        fmu_paths=fmu_paths,
        model_instances=model_instances,
        connections_config=connections_config,
        start_values=start_values,
        parameters_to_log=parameters_to_log,
        get_units=True,
    )
    assert units == {
        "DC_Motor.y": None,
        "DC_Motor.MotorTorque.tau": "N.m",
        "pid.u": None,
    }
    test_results = pd.read_csv(result_path)
    test_results = test_results.to_numpy()
    results = results.to_numpy()
    assert np.isclose(results, test_results, atol=1e-6).all()


def test_simulate_with_no_parameters_to_log(
    connections_config: ConnectionsConfig,
    fmu_paths: FmuPaths,
    model_instances: ModelInstances,
    start_values: StartValues,
    result_path: Path,
) -> None:

    results = simulate(
        stop_time=2,
        step_size=1e-3,
        fmu_paths=fmu_paths,
        model_instances=model_instances,
        start_values=start_values,
        connections_config=connections_config,
    )

    test_results = pd.read_csv(result_path, usecols=["time"])
    test_results = test_results.to_numpy()
    results = results.to_numpy()
    assert np.isclose(results, test_results, atol=1e-6).all()


@pytest.mark.parametrize("logging_step_size", [1e-3, 1e-2, 1e-1, 1.0])
def test_simulate_with_bigger_log_step_size(
    connections_config: ConnectionsConfig,
    fmu_paths: FmuPaths,
    model_instances: ModelInstances,
    start_values: StartValues,
    result_path: Path,
    parameters_to_log: ParametersToLog,
    logging_step_size: float,
) -> None:

    step_size = 1e-3
    results = simulate(
        stop_time=2,
        step_size=step_size,
        fmu_paths=fmu_paths,
        model_instances=model_instances,
        start_values=start_values,
        connections_config=connections_config,
        parameters_to_log=parameters_to_log,
        logging_step_size=logging_step_size,
    )

    test_results = pd.read_csv(result_path).to_numpy()
    results = results.to_numpy()

    assert np.isclose(
        results, test_results[:: int(logging_step_size / step_size)], atol=1e-6
    ).all()


def test_validate_input_duplicate_name_value_error(
    fmu_paths: FmuPaths, model_instances: ModelInstances
) -> None:
    fmu_paths[list(model_instances.keys())[0]] = ""
    with pytest.raises(ValueError, match="Duplicate names in system infos."):
        _validate_input(1, 0.1, fmu_paths, model_instances, None, None, None, None)


def test_validate_parameters_to_log_raises_type_error(
    parameters_to_log: ParametersToLog, system_names: list[str]
) -> None:

    parameters_to_log["DC_Motor"] = "var"
    with pytest.raises(TypeError):
        _validate_parameters_to_log(parameters_to_log, system_names)


def test_validate_parameters_to_log_raises_value_error(
    parameters_to_log: ParametersToLog, system_names: list[str]
) -> None:

    system_names.pop(0)
    with pytest.raises(ValueError):
        _validate_parameters_to_log(parameters_to_log, system_names)
