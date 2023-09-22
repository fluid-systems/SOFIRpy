import json
from pathlib import Path

import pytest
from syrupy import SnapshotAssertion

from sofirpy import HDF5, Run
from sofirpy.rdm.hdf5.config import RunDatasetName, RunGroupName
from sofirpy.rdm.hdf5.hdf5 import Dataset, Group
from sofirpy.rdm.run import _ConfigDict, _MetaConfigDict, _RunMeta, _SimulationConfig
from sofirpy.simulation.simulation import FmuPaths, ModelClasses


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
