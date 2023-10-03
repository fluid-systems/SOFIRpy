"""This module contains the function to create a run from a hdf5 file."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from pkg_resources import parse_version

import sofirpy
import sofirpy.rdm.hdf5.deserialize as deserialize
import sofirpy.rdm.hdf5.hdf5 as h5
import sofirpy.rdm.run as rdm_run
import sofirpy.utils as utils


def create_run_from_hdf5(hdf5_path: Path, run_name: str) -> rdm_run.Run:
    # TODO if loaded model is None because it could not be pickled.
    logging.basicConfig(
        format="HDF5ToRun::%(levelname)s::%(message)s", level=logging.INFO, force=True
    )
    if not hdf5_path.exists():
        raise FileNotFoundError(f"'{hdf5_path}' does not exist")
    hdf5 = h5.HDF5(hdf5_path)
    run_group = h5.Group.from_hdf5(hdf5, run_name)
    run_meta = deserialize.Deserializer.run_meta.deserialize(run_group)
    _check_compatibility(run_meta)
    results = deserialize.Deserializer.results.deserialize(run_group)
    simulation_config = deserialize.Deserializer.simulation_config.deserialize(
        run_group
    )
    models = deserialize.Models.deserialize(
        run_group,
        hdf5=hdf5,
    )
    run = rdm_run.Run(
        run_name=run_name,
        _run_meta=run_meta,
        _models=models,
        _simulation_config=simulation_config,
        _results=results,
    )
    logging.info(f"'{run_name}' successfully loaded from '{hdf5_path}'")
    return run


def _check_compatibility(run_meta: rdm_run.RunMeta) -> None:
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
    is_later_release = parse_version(run_meta.sofirpy_version) <= parse_version(
        sofirpy.__version__
    )
    if not is_later_release:
        logging.warning(
            f"Run was created with sofirpy version '{run_meta.sofirpy_version}'."
            f"This is sofirpy version '{sofirpy.__version__}', an earlier release."
        )
    if not same_os or not same_py_version:
        logging.warning(
            "The current environment is not fully compatible with the environment the "
            "Run was created with. It might not be possible to rerun the simulation."
        )
    _check_dependencies(run_meta)


def _check_dependencies(run_meta: rdm_run.RunMeta) -> None:
    run_dep = run_meta.dependencies
    cur_env_dep = utils.get_dependencies_of_current_env()
    dependencies_in_hdf5_but_not_in_current_env = set(run_dep).difference(cur_env_dep)
    if dependencies_in_hdf5_but_not_in_current_env:
        logging.warning(
            "The following dependencies were installed when storing the run in the "
            "hdf5 and are not installed in the current environment:\n"
            f"{', '.join(dependencies_in_hdf5_but_not_in_current_env)}"
        )
    difference_in_version_number: list[str] = []
    for dep_name in set(run_dep).intersection(cur_env_dep):
        if run_dep[dep_name] != cur_env_dep[dep_name]:
            difference_in_version_number.append(dep_name)
    if difference_in_version_number:
        logging.warning(
            "The following dependencies have a different version: "
            f"{', '.join(difference_in_version_number)}"
        )
