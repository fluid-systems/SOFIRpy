import sys
from pathlib import Path

import numpy as np
import pytest

from sofirpy import HDF5, Run
from sofirpy.rdm.run import Fmu, Model, Models, PythonModel, Results, RunMeta
from sofirpy.simulation.simulation import FmuPaths, ModelInstances


@pytest.fixture
def hdf5() -> HDF5:
    ...


@pytest.fixture
def hdf5_path() -> Path:
    return Path(__file__).parent / "test_run.hdf5"


@pytest.fixture
def run(fmu_paths: FmuPaths, model_instances: ModelInstances) -> Run:
    if sys.platform == "linux" or sys.platform == "linux2":
        run_name = "test_run_linux"
    elif sys.platform == "win32":
        run_name = "test_run_win"
    elif sys.platform == "darwin":
        run_name = "test_run_mac"
    return Run.from_config(
        run_name=run_name,
        config_path=Path(__file__).parent / "test_config.json",
        fmu_paths=fmu_paths,
        model_instances=model_instances,
    )


def test_loaded_hdf5_run_is_identical_to_run_from_config(
    run: Run, hdf5_path: Path
) -> None:
    run.simulate()
    compare_runs(run, Run.from_hdf5(run.run_name, hdf5_path))


def compare_runs(this_run: Run, other_run: Run) -> None:
    compare_meta(this_run._run_meta, other_run._run_meta)
    compare_models(this_run._models, other_run._models)
    compare_results(this_run._results, other_run._results)


def compare_meta(this_run_meta: RunMeta, other_run_meta: RunMeta) -> None:
    assert this_run_meta.description == other_run_meta.description
    assert this_run_meta.keywords == other_run_meta.keywords
    assert this_run_meta.sofirpy_version == other_run_meta.sofirpy_version


def compare_models(this_run_models: Models, other_run_models: Models) -> None:
    for fmu_name in this_run_models.fmus:
        compare_fmu(this_run_models.fmus[fmu_name], other_run_models.fmus[fmu_name])
    for python_model_name in this_run_models.python_models:
        compare_python_model(
            this_run_models.python_models[python_model_name],
            other_run_models.python_models[python_model_name],
        )


def compare_fmu(this_run_fmu: Fmu, other_run_fmu: Fmu) -> None:
    assert (
        this_run_fmu.fmu_path.open("rb").read()
        == other_run_fmu.fmu_path.open("rb").read()
    )
    compare_model(this_run_fmu, other_run_fmu)


def compare_python_model(
    this_run_python_model: PythonModel, other_run_python_model: PythonModel
) -> None:
    compare_model(this_run_python_model, other_run_python_model)


def compare_model(this_run_model: Model, other_run_model: Model) -> None:
    assert this_run_model.name == other_run_model.name
    assert this_run_model.connections == other_run_model.connections
    assert this_run_model.start_values == other_run_model.start_values
    assert this_run_model.parameters_to_log == other_run_model.parameters_to_log


def compare_results(this_run_results: Results, other_run_results: Results) -> None:
    assert np.isclose(
        this_run_results.time_series.to_numpy(),
        other_run_results.time_series.to_numpy(),
        atol=1e-6,
    ).all()
    assert this_run_results.units == other_run_results.units
