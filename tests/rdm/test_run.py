import json
import sys
from pathlib import Path

import numpy as np
import pytest

from sofirpy import HDF5, Run
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
    _SimulationConfigDict,
)
from sofirpy.simulation.simulation import FmuPaths, ModelInstances


@pytest.fixture
def hdf5() -> HDF5:
    ...


@pytest.fixture
def hdf5_path() -> Path:
    return Path(__file__).parent / "test_run.hdf5"


@pytest.fixture
def config_path() -> Path:
    return Path(__file__).parent / "test_config.json"


@pytest.fixture
def run(config_path: Path, fmu_paths: FmuPaths, model_instances: ModelInstances) -> Run:
    if sys.platform == "linux" or sys.platform == "linux2":
        run_name = "test_run_linux"
    elif sys.platform == "win32":
        run_name = "test_run_mac"
    elif sys.platform == "darwin":
        run_name = "test_run_mac"
    return Run.from_config(
        run_name=run_name,
        config_path=config_path,
        fmu_paths=fmu_paths,
        model_instances=model_instances,
    )


def test_get_config(run: Run, config_path: Path) -> None:
    compare_config(run.get_config(), json.load(config_path.open()))


def compare_config(this_config: _ConfigDict, other_config: _ConfigDict) -> None:
    compare_meta_config(
        this_config[_RunMeta.CONFIG_KEY], other_config[_RunMeta.CONFIG_KEY]
    )
    compare_simulation_config_dict(
        this_config[_SimulationConfig.CONFIG_KEY],
        other_config[_SimulationConfig.CONFIG_KEY],
    )


def compare_meta_config(
    this_meta_config: _MetaConfigDict, other_meta_config: _MetaConfigDict
) -> None:
    assert this_meta_config == other_meta_config


def compare_simulation_config_dict(
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


def test_loaded_hdf5_run_is_identical_to_run_from_config(
    run: Run, hdf5_path: Path
) -> None:
    # TODO do this with snapshots
    run.simulate()
    compare_runs(run, Run.from_hdf5(run.run_name, hdf5_path))


def compare_runs(this_run: Run, other_run: Run) -> None:
    compare_meta(this_run._run_meta, other_run._run_meta)
    compare_models(this_run._models, other_run._models)
    compare_simulation_config(this_run._simulation_config, other_run._simulation_config)
    compare_results(this_run._results, other_run._results)


def compare_meta(this_run_meta: _RunMeta, other_run_meta: _RunMeta) -> None:
    assert this_run_meta.description == other_run_meta.description
    assert this_run_meta.keywords == other_run_meta.keywords
    assert this_run_meta.sofirpy_version == other_run_meta.sofirpy_version


def compare_simulation_config(
    this_simulation_config: _SimulationConfig,
    other_simulation_config: _SimulationConfig,
) -> None:
    assert this_simulation_config.step_size == other_simulation_config.step_size
    assert this_simulation_config.stop_time == other_simulation_config.stop_time
    assert (
        this_simulation_config.logging_step_size
        == other_simulation_config.logging_step_size
    )


def compare_models(this_run_models: _Models, other_run_models: _Models) -> None:
    for fmu_name in this_run_models.fmus:
        compare_fmu(this_run_models.fmus[fmu_name], other_run_models.fmus[fmu_name])
    for python_model_name in this_run_models.python_models:
        compare_python_model(
            this_run_models.python_models[python_model_name],
            other_run_models.python_models[python_model_name],
        )


def compare_fmu(this_run_fmu: _Fmu, other_run_fmu: _Fmu) -> None:
    compare_model(this_run_fmu, other_run_fmu)
    assert (
        this_run_fmu.fmu_path.open("rb").read()
        == other_run_fmu.fmu_path.open("rb").read()
    )


def compare_python_model(
    this_run_python_model: _PythonModel, other_run_python_model: _PythonModel
) -> None:
    compare_model(this_run_python_model, other_run_python_model)


def compare_model(this_run_model: _Model, other_run_model: _Model) -> None:
    assert this_run_model.name == other_run_model.name
    assert this_run_model.connections == other_run_model.connections
    assert this_run_model.start_values == other_run_model.start_values
    assert this_run_model.parameters_to_log == other_run_model.parameters_to_log


def compare_results(this_run_results: _Results, other_run_results: _Results) -> None:
    assert np.isclose(
        this_run_results.time_series.to_numpy(),
        other_run_results.time_series.to_numpy(),
        atol=1e-6,
    ).all()
    assert this_run_results.units == other_run_results.units
