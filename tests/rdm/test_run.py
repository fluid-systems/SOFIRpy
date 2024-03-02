from __future__ import annotations

import json
import sys
from pathlib import Path

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
from sofirpy.common import FmuPaths, ModelClasses
from sofirpy.rdm.run import (
    ConfigDict,
    Fmu,
    MetaConfigDict,
    Model,
    Models,
    PythonModel,
    Results,
    RunMeta,
    SimulationConfig,
)


@pytest.fixture
def config_path() -> Path:
    return Path(__file__).parent / "test_config.json"


@pytest.fixture
def run(config_path: Path, fmu_paths: FmuPaths, model_classes: ModelClasses) -> Run:
    return Run.from_config_file(
        run_name="test_run",
        config_file_path=config_path,
        fmu_paths=fmu_paths,
        model_classes=model_classes,
    )


def test_init_run_from_config_file(config_path) -> None:
    Run.from_config_file(run_name="test_run", config_file_path=config_path)


def test_init_run_config(fmu_paths: FmuPaths, model_classes: ModelClasses) -> None:
    Run.from_config("test_run", 10, 0.1)
    Run.from_config(
        "test_run", 10, 0.1, fmu_paths=fmu_paths, model_classes=model_classes
    )


def test_store_run_in_hdf5(run: Run, tmp_path: str) -> None:
    temp_hdf5_path = Path(tmp_path) / "temp.hdf5"
    run.simulate()
    run.to_hdf5(temp_hdf5_path)


@pytest.mark.skipif(
    sys.version_info >= (3, 11),
    reason="Skip for snapshot test for python 3.11 or newer",
)
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
        except Exception:  # noqa: BLE001
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
        if sys.platform == "win32":
            return "test_run_win"
        if sys.platform == "darwin":
            return "test_run_mac"
        raise ValueError("'Unknown platform")

    def _read_snapshot_data_from_location(
        self, *, snapshot_location: str, snapshot_name: str, session_id: str
    ) -> SerializableData | None:
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
        run = data
        assert isinstance(run, Run)
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


def _compare_meta(this_run_meta: RunMeta, other_run_meta: RunMeta) -> None:
    assert this_run_meta.description == other_run_meta.description
    assert this_run_meta.keywords == other_run_meta.keywords


def _compare_simulation_config(
    this_simulation_config: SimulationConfig,
    other_simulation_config: SimulationConfig,
) -> None:
    assert this_simulation_config.step_size == other_simulation_config.step_size
    assert this_simulation_config.stop_time == other_simulation_config.stop_time
    assert (
        this_simulation_config.logging_step_size
        == other_simulation_config.logging_step_size
    )


def _compare_models(this_run_models: Models, other_run_models: Models) -> None:
    for fmu_name in this_run_models.fmus:
        _compare_fmu(this_run_models.fmus[fmu_name], other_run_models.fmus[fmu_name])
    for python_model_name in this_run_models.python_models:
        _compare_python_model(
            this_run_models.python_models[python_model_name],
            other_run_models.python_models[python_model_name],
        )


def _compare_fmu(this_run_fmu: Fmu, other_run_fmu: Fmu) -> None:
    compare_model(this_run_fmu, other_run_fmu)
    assert (
        this_run_fmu.fmu_path.open("rb").read()
        == other_run_fmu.fmu_path.open("rb").read()
    )


def _compare_python_model(
    this_run_python_model: PythonModel, other_run_python_model: PythonModel
) -> None:
    assert (
        this_run_python_model.get_source_code()
        == other_run_python_model.get_source_code()
    )
    compare_model(this_run_python_model, other_run_python_model)


def compare_model(this_run_model: Model, other_run_model: Model) -> None:
    assert this_run_model.name == other_run_model.name
    assert this_run_model.connections == other_run_model.connections
    assert this_run_model.start_values == other_run_model.start_values
    assert this_run_model.parameters_to_log == other_run_model.parameters_to_log


def _compare_results(this_run_results: Results, other_run_results: Results) -> None:
    assert np.isclose(
        this_run_results.time_series.to_numpy(),
        other_run_results.time_series.to_numpy(),
        atol=1e-6,
    ).all()
    assert this_run_results.units == other_run_results.units


def _compare_config(this_config: ConfigDict, other_config: ConfigDict) -> None:
    _compare_meta_config(
        this_config[RunMeta.CONFIG_KEY.value], other_config[RunMeta.CONFIG_KEY.value]
    )
    _compare_simulation_config_dict(
        this_config[SimulationConfig.CONFIG_KEY.value],
        other_config[SimulationConfig.CONFIG_KEY.value],
    )


def _compare_meta_config(
    this_meta_config: MetaConfigDict, other_meta_config: MetaConfigDict
) -> None:
    assert this_meta_config == other_meta_config


def _compare_simulation_config_dict(
    this_simulation_config: SimulationConfig,
    other_simulation_config: SimulationConfig,
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
