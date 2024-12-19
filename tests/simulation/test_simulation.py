from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from sofirpy.common import (
    ConnectionsConfig,
    FmuPaths,
    InitConfigs,
    ModelClasses,
    ParametersToLog,
)
from sofirpy.simulation.simulation import BaseSimulator, VariableSizeRecorder, simulate


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
    model_classes: ModelClasses,
    init_configs: InitConfigs,
    result_path: Path,
    parameters_to_log: ParametersToLog,
) -> None:
    results, units = simulate(
        stop_time=2,
        step_size=1e-3,
        fmu_paths=fmu_paths,
        model_classes=model_classes,
        connections_config=connections_config,
        init_configs=init_configs,
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
    model_classes: ModelClasses,
    init_configs: InitConfigs,
    result_path: Path,
) -> None:
    results = simulate(
        stop_time=2,
        step_size=1e-3,
        fmu_paths=fmu_paths,
        model_classes=model_classes,
        init_configs=init_configs,
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
    model_classes: ModelClasses,
    init_configs: InitConfigs,
    result_path: Path,
    parameters_to_log: ParametersToLog,
    logging_step_size: float,
) -> None:
    step_size = 1e-3
    results = simulate(
        stop_time=2,
        step_size=step_size,
        fmu_paths=fmu_paths,
        model_classes=model_classes,
        init_configs=init_configs,
        connections_config=connections_config,
        parameters_to_log=parameters_to_log,
        logging_step_size=logging_step_size,
    )

    test_results = pd.read_csv(result_path).to_numpy()
    results = results.to_numpy()

    assert np.isclose(
        results, test_results[:: int(logging_step_size / step_size)], atol=1e-6
    ).all()


def test_custom_simulation_loop_with_variable_logger(
    connections_config: ConnectionsConfig,
    fmu_paths: FmuPaths,
    model_classes: ModelClasses,
    init_configs: InitConfigs,
    result_path: Path,
    parameters_to_log: ParametersToLog,
) -> None:
    simulator = BaseSimulator(
        fmu_paths=fmu_paths,
        model_classes=model_classes,
        init_configs=init_configs,
        connections_config=connections_config,
        parameters_to_log=parameters_to_log,
        recorder=VariableSizeRecorder,
    )
    stop_time = 2
    step_size = 1e-3
    steps = int(stop_time / step_size)
    while (
        simulator.step < steps
    ):  # use steps instead of stop time to avoid floating point errors
        simulator.recorder.record(simulator.time, simulator.step)
        simulator.do_step(simulator.time, step_size)
        simulator.set_systems_inputs()
        simulator.time += step_size
        simulator.step += 1
    simulator.recorder.record(simulator.time, simulator.step)
    simulator.conclude_simulation()
    results = simulator.recorder.to_pandas()
    assert simulator.get_units() == {
        "DC_Motor.y": None,
        "DC_Motor.MotorTorque.tau": "N.m",
        "pid.u": None,
    }
    test_results = pd.read_csv(result_path)
    test_results = test_results.to_numpy()
    results = results.to_numpy()
    assert np.isclose(results, test_results, atol=1e-6).all()
