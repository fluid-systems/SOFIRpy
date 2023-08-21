from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from typing_extensions import Self

import sofirpy
import sofirpy.rdm.db.deserialize_hdf5 as deserialize_hdf5
import sofirpy.rdm.db.hdf5 as h5
import sofirpy.rdm.db.serialize as serialize
import sofirpy.rdm.run as rdm_run


class HDF5FileMetaKey(str, Enum):
    CREATED_WITH_SOFIRPY = "created with"
    INITIALIZATION_DATE = "initialization date"
    SOFIRPY_VERSION = "sofirpy version"

    @classmethod
    def get_values(cls) -> set[str]:
        return {key.value for key in HDF5FileMetaKey}


class ModelStorageGroupName(str, Enum):
    MODELS = "models"
    FMUS = "fmus"
    PYTHON_MODELS = "python_models"
    INSTANCES = "instances"
    SOURCE_CODE = "source_code"

    @classmethod
    def absolute_paths(cls) -> set[str]:
        return {
            str(cls.MODELS),
            f"{cls.MODELS}/{cls.FMUS}",
            f"{cls.MODELS}/{cls.PYTHON_MODELS}",
            f"{cls.MODELS}/{cls.PYTHON_MODELS}/{cls.INSTANCES}",
            f"{cls.MODELS}/{cls.PYTHON_MODELS}/{cls.SOURCE_CODE}",
        }


class RunGroupName(Enum):
    SIMULATION_RESULTS = "simulation_results"
    MODELS = "models"
    FMUS = "fmus"
    PYTHON_MODELS = "python_models"


class RunDatasetName(Enum):
    CONFIG = "config"
    MODEL_REFERENCE = "reference"
    START_VALUES = "start_values"
    CONNECTIONS = "connections"


def init_hdf5(hdf5: h5.HDF5) -> None:
    if is_initialized(hdf5):
        return
    init_meta = generate_init_meta()
    hdf5.append_attributes(init_meta)
    (
        h5.Group("models")
        .append_group(h5.Group("fmus"))
        .append_group(
            h5.Group("python_models")
            .append_group(h5.Group("instances"))
            .append_group(h5.Group("source_code"))
        )
        .to_hdf5(hdf5)
    )


def is_initialized(hdf5: h5.HDF5) -> bool:
    init_meta = hdf5.read_attributes()
    init_meta_keys = set(init_meta.keys())
    if not init_meta_keys.issubset(HDF5FileMetaKey.get_values()):
        return False
    if not ModelStorageGroupName.absolute_paths() in hdf5:
        return False


def generate_init_meta() -> dict[str, str]:
    return {
        HDF5FileMetaKey.INITIALIZATION_DATE.value: datetime.now().strftime(
            "%d-%b-%Y %H:%M:%S"
        ),
        HDF5FileMetaKey.CREATED_WITH_SOFIRPY.value: "https://sofirpy.readthedocs.io",
        HDF5FileMetaKey.SOFIRPY_VERSION.value: sofirpy.__version__,
    }


def run_to_hdf5(run: rdm_run.Run, hdf5_path: Path) -> None:
    hdf5 = h5.HDF5(hdf5_path)
    init_hdf5(hdf5)


def create_run_group_from_run(run: rdm_run.Run, hdf5: h5.HDF5) -> h5.Group:
    run_group = (
        h5.Group(name=run.run_name)
        .append_attribute(h5.Attribute(attributes=serialize.RunMeta.serialize(run)))
        .append_dataset(h5.Dataset(name="config", data=serialize.Config.serialize(run)))
        .append_group(
            h5.Group("simulation_results")
            .append_attribute(
                h5.Attribute(attributes=serialize.SimulationConfig.serialize(run))
            )
            .append_dataset(
                h5.Dataset(
                    name="time_series", data=serialize.TimeSeries.serialize(run)
                ).append_attribute(
                    h5.Attribute(attributes=serialize.Units.serialize(run))
                )
            )
        )
        .append_group(
            h5.Group("models")
            .append_group(h5.Group("fmus"))
            .append_group(h5.Group("python_models"))
        )
    )

    model_storage_group = h5.Group.from_hdf5(hdf5, "models", read_data=False)
    fmu_storage_group = model_storage_group.get_group("fmus")
    run_fmus_group = run_group.get_group("models/fmus")
    for fmu_name in run._models.fmus:
        run_fmus_group.append_group(
            h5.Group(fmu_name)
            .append_dataset(
                h5.Dataset(
                    name="connections",
                    data=serialize.Connections.serialize(run, fmu_name),
                )
            )
            .append_dataset(
                h5.Dataset(
                    name="start_values",
                    data=serialize.StartValues.serialize(run, fmu_name),
                )
            )
            .append_dataset(
                h5.Dataset(
                    name="parameters_to_log",
                    data=serialize.ParametersToLog.serialize(run, fmu_name),
                )
            )
        )
        fmu_reference_dataset = h5.Dataset(
            name="reference", data=serialize.FmuReference.serialize(run, fmu_name)
        )
        fmu_hash = fmu_reference_dataset.data
        try:
            fmu_storage_group.get_dataset(fmu_hash)
        except KeyError:
            fmu_storage_dataset = h5.Dataset(
                name=fmu_hash, data=serialize.FmuStorage.serialize(run, fmu_name)
            )
            fmu_storage_group.append_dataset(fmu_storage_dataset)

    run_python_models_group = run_group.get_group("models/python_models")
    python_model_instances_storage_group = model_storage_group.get_group(
        "python_models/instances"
    )
    python_model_source_code_storage_group = model_storage_group.get_group(
        "python_models/source_code"
    )
    for python_model_name in run._models.python_models:
        run_python_models_group.append_group(
            h5.Group(python_model_name)
            .append_dataset(
                h5.Dataset(
                    name="connections",
                    data=serialize.Connections.serialize(run, python_model_name),
                )
            )
            .append_dataset(
                h5.Dataset(
                    name="start_values",
                    data=serialize.StartValues.serialize(run, python_model_name),
                )
            )
            .append_dataset(
                h5.Dataset(
                    name="parameters_to_log",
                    data=serialize.ParametersToLog.serialize(run, python_model_name),
                )
            )
        )
        python_model_instance_reference_dataset = h5.Dataset(
            name="reference_model_instance",
            data=serialize.PythonModelInstanceReference.serialize(
                run, python_model_name
            ),
        )
        model_instance_hash = python_model_instance_reference_dataset.data
        try:
            python_model_instances_storage_group.get_dataset(model_instance_hash)
        except KeyError:
            python_model_instance_storage_dataset = h5.Dataset(
                name=model_instance_hash,
                data=serialize.PythonModelInstanceStorage.serialize(
                    run, python_model_name
                ),
            )
            python_model_instances_storage_group.append_dataset(
                python_model_instance_storage_dataset
            )
        python_model_source_code_reference_dataset = h5.Dataset(
            name="reference_source_code",
            data=serialize.PythonModelSourceCodeReference.serialize(
                run, python_model_name
            ),
        )
        model_source_code_hash = python_model_source_code_reference_dataset.data
        try:
            python_model_source_code_storage_group.get_dataset(model_source_code_hash)
        except KeyError:
            python_model_source_code_storage_dataset = h5.Dataset(
                name=model_source_code_hash,
                data=serialize.PythonModelSourceCodeStorage.serialize(
                    run, python_model_name
                ),
            )
            python_model_source_code_storage_group.append_dataset(
                python_model_source_code_storage_dataset
            )
    return run_group


def create_run_from_hdf5(hdf5: h5.HDF5, run_name: str) -> h5.Group:
    run_group = h5.Group.from_hdf5(hdf5, run_name)
    model_storage_group = h5.Group.from_hdf5(hdf5, "models", read_data=False)
    run_meta = deserialize_hdf5.RunMeta.deserialize(run_group)
    results = deserialize_hdf5.Results.deserialize(run_group)
    simulation_config = deserialize_hdf5.SimulationConfig.deserialize(run_group)
    models = deserialize_hdf5.Models.deserialize(run_group, model_storage_group)
    run = rdm_run.Run(
        run_name=run_name,
        _run_meta=run_meta,
        _models=models,
        _simulation_config=simulation_config,
        _results=results,
    )
    return run
