from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional, cast

import numpy as np
import pytest
from syrupy import SnapshotAssertion
from syrupy.data import SnapshotCollection
from syrupy.extensions.single_file import SingleFileSnapshotExtension
from syrupy.location import PyTestLocation
from syrupy.types import (
    PropertyFilter,
    PropertyMatcher,
    SerializableData,
    SerializedData,
    SnapshotIndex,
)

from sofirpy import HDF5, Run
from sofirpy.rdm.hdf5.hdf5 import Group
from sofirpy.rdm.run import (
    _Fmu,
    _Model,
    _Models,
    _PythonModel,
    _Results,
    _RunMeta,
    _SimulationConfig,
)
from sofirpy.simulation.simulation import FmuPaths, ModelClasses, StartValues
from sofirpy.simulation.simulation_entity import SimulationEntity


class RunExtension(SingleFileSnapshotExtension):
    _file_extension = "hdf5"

    def matches(
        self,
        *,
        serialized_data: Run,
        snapshot_data: Run,
    ) -> bool:
        try:
            _compare_runs(serialized_data, snapshot_data)
        except Exception:
            return False
        return True

    def serialize(
        self,
        data: SerializableData,
        *,
        exclude: PropertyFilter | None = None,
        include: PropertyFilter | None = None,
        matcher: PropertyMatcher | None = None,
    ) -> SerializedData:
        return data

    @classmethod
    def get_snapshot_name(
        cls, *, test_location: PyTestLocation, index: SnapshotIndex = 0
    ) -> str:
        if sys.platform == "linux" or sys.platform == "linux2":
            return "test_run_linux"
        elif sys.platform == "win32":
            return "test_run_mac"
        elif sys.platform == "darwin":
            return "test_run_mac"
        raise ValueError("'Unknown platform")

    def _read_snapshot_data_from_location(
        self, *, snapshot_location: str, snapshot_name: str, session_id: str
    ) -> Optional[SerializableData]:
        try:
            return Run.from_hdf5("test_run", snapshot_location)
        except FileNotFoundError:
            return None

    @classmethod
    def _write_snapshot_collection(
        cls, *, snapshot_collection: SnapshotCollection
    ) -> None:
        filepath, data = (
            snapshot_collection.location,
            next(iter(snapshot_collection)).data,
        )
        run = cast(Run, data)
        run.to_hdf5(filepath)


@pytest.fixture
def run_snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    return snapshot.use_extension(RunExtension)


def _compare_runs(this_run: Run, other_run: Run) -> None:
    _compare_meta(this_run._run_meta, other_run._run_meta)
    _compare_models(this_run._models, other_run._models)
    _compare_simulation_config(
        this_run._simulation_config, other_run._simulation_config
    )
    _compare_results(this_run._results, other_run._results)


def _compare_meta(this_run_meta: _RunMeta, other_run_meta: _RunMeta) -> None:
    assert this_run_meta.description == other_run_meta.description
    assert this_run_meta.keywords == other_run_meta.keywords
    assert this_run_meta.sofirpy_version == other_run_meta.sofirpy_version


def _compare_simulation_config(
    this_simulation_config: _SimulationConfig,
    other_simulation_config: _SimulationConfig,
) -> None:
    assert this_simulation_config.step_size == other_simulation_config.step_size
    assert this_simulation_config.stop_time == other_simulation_config.stop_time
    assert (
        this_simulation_config.logging_step_size
        == other_simulation_config.logging_step_size
    )


def _compare_models(this_run_models: _Models, other_run_models: _Models) -> None:
    for fmu_name in this_run_models.fmus:
        _compare_fmu(this_run_models.fmus[fmu_name], other_run_models.fmus[fmu_name])
    for python_model_name in this_run_models.python_models:
        _compare_python_model(
            this_run_models.python_models[python_model_name],
            other_run_models.python_models[python_model_name],
        )


def _compare_fmu(this_run_fmu: _Fmu, other_run_fmu: _Fmu) -> None:
    compare_model(this_run_fmu, other_run_fmu)
    # TODO uncomment compare fmu binaries
    # assert (
    #     this_run_fmu.fmu_path.open("rb").read()
    #     == other_run_fmu.fmu_path.open("rb").read()
    # )


def _compare_python_model(
    this_run_python_model: _PythonModel, other_run_python_model: _PythonModel
) -> None:
    assert (
        this_run_python_model.get_source_code()
        == other_run_python_model.get_source_code()
    )
    compare_model(this_run_python_model, other_run_python_model)


def compare_model(this_run_model: _Model, other_run_model: _Model) -> None:
    assert this_run_model.name == other_run_model.name
    assert this_run_model.connections == other_run_model.connections
    assert this_run_model.start_values == other_run_model.start_values
    assert this_run_model.parameters_to_log == other_run_model.parameters_to_log


def _compare_results(this_run_results: _Results, other_run_results: _Results) -> None:
    assert np.isclose(
        this_run_results.time_series.to_numpy(),
        other_run_results.time_series.to_numpy(),
        atol=1e-6,
    ).all()
    assert this_run_results.units == other_run_results.units


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
