from __future__ import annotations

import json
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

from sofirpy import Run
from sofirpy.rdm.run import (
    _ConfigDict,
    _Fmu,
    _MetaConfigDict,
    _Model,
    _Models,
    _PythonModel,
    _Results,
    _RunMeta,
    _SimulationConfig,
)
from sofirpy.simulation.simulation import FmuPaths, ModelClasses


def test_store_run_in_hdf5(run: Run, tmp_path: str) -> None:
    temp_hdf5_path = Path(tmp_path) / "temp.hdf5"
    run.simulate()
    run.to_hdf5(temp_hdf5_path)


def test_loaded_hdf5_run_is_identical_to_run_from_config(
    run: Run, run_snapshot: SnapshotAssertion
) -> None:
    run.simulate()
    assert run == run_snapshot


def test_get_config(run: Run, config_path: Path) -> None:
    _compare_config(run.get_config(), json.load(config_path.open()))


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
    assert (
        this_run_fmu.fmu_path.open("rb").read()
        == other_run_fmu.fmu_path.open("rb").read()
    )


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
def config_path() -> Path:
    return Path(__file__).parent / "test_config.json"


@pytest.fixture
def run(config_path: Path, fmu_paths: FmuPaths, model_classes: ModelClasses) -> Run:
    return Run.from_config(
        run_name="test_run",
        config_path=config_path,
        fmu_paths=fmu_paths,
        model_classes=model_classes,
    )


def _compare_config(this_config: _ConfigDict, other_config: _ConfigDict) -> None:
    _compare_meta_config(
        this_config[_RunMeta.CONFIG_KEY], other_config[_RunMeta.CONFIG_KEY]
    )
    _compare_simulation_config_dict(
        this_config[_SimulationConfig.CONFIG_KEY],
        other_config[_SimulationConfig.CONFIG_KEY],
    )


def _compare_meta_config(
    this_meta_config: _MetaConfigDict, other_meta_config: _MetaConfigDict
) -> None:
    assert this_meta_config == other_meta_config


def _compare_simulation_config_dict(
    this_simulation_config: _SimulationConfig,
    other_simulation_config: _SimulationConfig,
) -> None:
    assert float(other_simulation_config["step_size"]) == pytest.approx(
        float(this_simulation_config["step_size"])
    )
    assert float(other_simulation_config["stop_time"]) == pytest.approx(
        float(this_simulation_config["stop_time"])
    )
    if not this_simulation_config["logging_step_size"]:
        assert (
            this_simulation_config["logging_step_size"]
            == other_simulation_config["logging_step_size"]
        )
    else:
        assert float(other_simulation_config["logging_step_size"]) == pytest.approx(
            float(this_simulation_config["logging_step_size"])
        )
