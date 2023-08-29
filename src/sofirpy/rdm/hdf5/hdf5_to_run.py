from __future__ import annotations

import logging
import sys
from pathlib import Path

import sofirpy
import sofirpy.rdm.hdf5.config as config
import sofirpy.rdm.hdf5.deserialize_hdf5 as deserialize_hdf5
import sofirpy.rdm.hdf5.hdf5 as h5
import sofirpy.rdm.run as rdm_run


def create_run_from_hdf5(hdf5_path: Path, run_name: str) -> rdm_run.Run:
    logging.basicConfig(
        format="Run::%(levelname)s::%(message)s",
        level=logging.INFO,
    )
    hdf5 = h5.HDF5(hdf5_path)
    run_group = h5.Group.from_hdf5(hdf5, run_name)
    run_meta = deserialize_hdf5.RunMeta.deserialize(run_group)
    can_simulate_fmu, can_load_python_model = check_compatibility(run_meta)
    results = deserialize_hdf5.Results.deserialize(run_group)
    simulation_config = deserialize_hdf5.SimulationConfig.deserialize(run_group)
    models = deserialize_hdf5.Models.deserialize(
        run_group, hdf5, can_simulate_fmu, can_load_python_model
    )
    run = rdm_run.Run(
        run_name=run_name,
        _run_meta=run_meta,
        _models=models,
        _simulation_config=simulation_config,
        _results=results,
    )
    return run


def check_compatibility(run_meta: rdm_run._RunMeta) -> tuple[bool, bool]:
    same_os = run_meta.os == sys.platform
    if not same_os:
        logging.warning(
            f"Run was created with os '{run_meta.os}'. This is '{sys.platform}'."
        )
    same_py_version = run_meta.python_version == sys.version
    if not same_py_version:
        logging.warning(
            f"Run was created with python version '{run_meta.python_version}'."
            f"This is python version '{sys.version}'."
        )
    is_later_release = run_meta.sofirpy_version <= sofirpy.__version__
    if not is_later_release:
        logging.warning(
            f"Run was created with sofirpy version '{run_meta.sofirpy_version}'."
            f"This is sofirpy version '{sofirpy.__version__}', an earlier release."
        )
    can_simulate_fmu = same_os
    can_load_python_models = same_py_version and same_os
    return can_simulate_fmu, can_load_python_models
