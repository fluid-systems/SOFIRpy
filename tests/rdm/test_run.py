import json
import sys
from pathlib import Path

import numpy as np
import pytest
from syrupy import SnapshotAssertion

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
    _SimulationConfigDict,
)
from sofirpy.simulation.simulation import FmuPaths, ModelClasses


@pytest.fixture
def hdf5_path() -> Path:
    return Path(__file__).parent / "test_run.hdf5"


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


# TODO compare two hdf5s
# def test_store_run_in_hdf5(run: Run, hdf5_path: Path) -> None:
#     run.simulate()
#     run.to_hdf5(hdf5_path)


def test_loaded_hdf5_run_is_identical_to_run_from_config(
    run: Run, run_snapshot: SnapshotAssertion
) -> None:
    run.simulate()
    assert run == run_snapshot


def test_get_config(run: Run, config_path: Path) -> None:
    _compare_config(run.get_config(), json.load(config_path.open()))


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
