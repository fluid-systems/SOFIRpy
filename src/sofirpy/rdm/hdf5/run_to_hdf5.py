from __future__ import annotations

from datetime import datetime
from pathlib import Path

import sofirpy
import sofirpy.rdm.hdf5.config as config
import sofirpy.rdm.hdf5.hdf5 as h5
import sofirpy.rdm.hdf5.serialize as serialize
import sofirpy.rdm.run as rdm_run


def init_hdf5(hdf5: h5.HDF5) -> None:
    if is_initialized(hdf5):
        return
    init_meta = generate_init_meta()
    hdf5.append_attributes(init_meta)
    (
        h5.Group(config.ModelStorageGroupName.MODELS.value)
        .append_group(h5.Group(config.ModelStorageGroupName.FMUS.value))
        .append_group(
            h5.Group(config.ModelStorageGroupName.PYTHON_MODELS.value)
            .append_group(h5.Group(config.ModelStorageGroupName.CLASSES.value))
            .append_group(h5.Group(config.ModelStorageGroupName.SOURCE_CODE.value))
        )
        .to_hdf5(hdf5)
    )


def is_initialized(hdf5: h5.HDF5) -> bool:
    init_meta = hdf5.read_attributes()
    init_meta_keys = set(init_meta.keys())
    if not init_meta_keys.issubset(config.HDF5FileMetaKey.get_values()):
        return False
    for path in config.ModelStorageGroupName.absolute_paths():
        if path not in hdf5:
            return False
    return True


def generate_init_meta() -> dict[str, str]:
    return {
        config.HDF5FileMetaKey.INITIALIZATION_DATE.value: datetime.now().strftime(
            "%d-%b-%Y %H:%M:%S"
        ),
        config.HDF5FileMetaKey.CREATED_WITH_SOFIRPY.value: "https://sofirpy.readthedocs.io",
        config.HDF5FileMetaKey.SOFIRPY_VERSION.value: sofirpy.__version__,
    }


def run_to_hdf5(run: rdm_run.Run, hdf5_path: Path) -> None:
    hdf5 = h5.HDF5(hdf5_path)
    init_hdf5(hdf5)
    if run.run_name in hdf5:
        raise ValueError(f"Run '{run.run_name}' already exists in '{hdf5.hdf5_path}'.")
    model_storage_group = h5.Group.from_hdf5(
        hdf5, config.ModelStorageGroupName.MODELS.value, read_data=False
    )
    run_group = create_run_group_without_models(run)

    models_group = h5.Group(name=config.RunGroupName.MODELS.value)

    fmus_group = create_fmus_group(run, model_storage_group)
    models_group.append_group(fmus_group)

    python_models_group = create_python_models_group(run, model_storage_group)
    models_group.append_group(python_models_group)

    run_group.append_group(models_group)
    try:
        run_group.to_hdf5(hdf5)
        model_storage_group.to_hdf5(hdf5)
    except Exception:
        run_group.delete(hdf5)
    print(f"Successfully created run '{run.run_name}' at '{hdf5.hdf5_path}'")


def create_run_group_without_models(run: rdm_run.Run) -> h5.Group:
    return (
        h5.Group(name=run.run_name)
        .append_attribute(h5.Attribute(attributes=serialize.RunMeta.serialize(run)))
        .append_dataset(
            h5.Dataset(
                name=config.RunDatasetName.CONFIG.value,
                data=serialize.Config.serialize(run),
            )
        )
        .append_group(
            h5.Group(config.RunGroupName.SIMULATION_RESULTS.value)
            .append_attribute(
                h5.Attribute(attributes=serialize.SimulationConfig.serialize(run))
            )
            .append_dataset(
                h5.Dataset(
                    name=config.RunDatasetName.TIME_SERIES.value,
                    data=serialize.TimeSeries.serialize(run),
                ).append_attribute(
                    h5.Attribute(attributes=serialize.Units.serialize(run))
                )
            )
        )
    )


def create_fmus_group(run: rdm_run.Run, model_storage_group: h5.Group) -> h5.Group:
    fmu_storage_group = model_storage_group.get_group(
        config.ModelStorageGroupName.FMUS.value
    )
    fmus_run_group = h5.Group(config.RunGroupName.FMUS.value)
    for fmu_name in run._models.fmus:
        fmu_group = (
            h5.Group(fmu_name)
            .append_dataset(
                h5.Dataset(
                    name=config.RunDatasetName.CONNECTIONS.value,
                    data=serialize.Connections.serialize(run, fmu_name),
                )
            )
            .append_dataset(
                h5.Dataset(
                    name=config.RunDatasetName.START_VALUES.value,
                    data=serialize.StartValues.serialize(run, fmu_name),
                )
            )
            .append_dataset(
                h5.Dataset(
                    name=config.RunDatasetName.PARAMETERS_TO_LOG.value,
                    data=serialize.ParametersToLog.serialize(run, fmu_name),
                )
            )
        )
        fmu_reference_dataset = h5.Dataset(
            name=config.RunDatasetName.FMU_REFERENCE.value,
            data=serialize.FmuReference.serialize(run, fmu_name),
        )
        fmu_group.append_dataset(fmu_reference_dataset)
        fmu_hash = fmu_reference_dataset.data
        try:
            fmu_storage_group.get_dataset(fmu_hash)
        except KeyError:
            fmu_storage_group.append_dataset(
                h5.Dataset(
                    name=fmu_hash,
                    data=serialize.FmuStorage.serialize(run, fmu_name),
                )
            )
        fmus_run_group.append_group(fmu_group)
    return fmus_run_group


def create_python_models_group(
    run: rdm_run.Run, model_storage_group: h5.Group
) -> h5.Group:
    python_models_storage_group = model_storage_group.get_group(
        config.ModelStorageGroupName.PYTHON_MODELS.value
    )
    python_models_run_group = h5.Group(config.RunGroupName.PYTHON_MODELS.value)
    python_model_classes_storage_group = python_models_storage_group.get_group(
        config.ModelStorageGroupName.CLASSES.value
    )
    python_model_source_code_storage_group = python_models_storage_group.get_group(
        config.ModelStorageGroupName.SOURCE_CODE.value
    )
    for python_model_name in run._models.python_models:
        python_model_group = (
            h5.Group(python_model_name)
            .append_dataset(
                h5.Dataset(
                    name=config.RunDatasetName.CONNECTIONS.value,
                    data=serialize.Connections.serialize(run, python_model_name),
                )
            )
            .append_dataset(
                h5.Dataset(
                    name=config.RunDatasetName.START_VALUES.value,
                    data=serialize.StartValues.serialize(run, python_model_name),
                )
            )
            .append_dataset(
                h5.Dataset(
                    name=config.RunDatasetName.PARAMETERS_TO_LOG.value,
                    data=serialize.ParametersToLog.serialize(run, python_model_name),
                )
            )
        )
        python_model_class_reference_dataset = h5.Dataset(
            name=config.RunDatasetName.REFERENCE_CLASS.value,
            data=serialize.PythonModelInstanceReference.serialize(
                run, python_model_name
            ),
        )
        python_model_group.append_dataset(python_model_class_reference_dataset)
        model_class_hash = python_model_class_reference_dataset.data
        try:
            python_model_classes_storage_group.get_dataset(model_class_hash)
        except KeyError:
            python_model_class_storage_dataset = h5.Dataset(
                name=model_class_hash,
                data=serialize.PythonModelInstanceStorage.serialize(
                    run, python_model_name
                ),
            )
            python_model_classes_storage_group.append_dataset(
                python_model_class_storage_dataset
            )
        python_model_source_code_reference_dataset = h5.Dataset(
            name=config.RunDatasetName.REFERENCE_SOURCE_CODE.value,
            data=serialize.PythonModelSourceCodeReference.serialize(
                run, python_model_name
            ),
        )
        python_model_group.append_dataset(python_model_source_code_reference_dataset)
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
        python_models_run_group.append_group(python_model_group)
    return python_models_run_group
