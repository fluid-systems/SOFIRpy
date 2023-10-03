from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import sofirpy
import sofirpy.rdm.hdf5.config as config
import sofirpy.rdm.hdf5.hdf5 as h5
import sofirpy.rdm.hdf5.serialize as serialize
import sofirpy.rdm.run as rdm_run


@dataclass
class RunToHDF5:
    hdf5: h5.HDF5
    run: rdm_run.Run
    serializer: type[serialize.Serializer] = serialize.Serializer

    @classmethod
    def store(cls, hdf5_path: Path, run: rdm_run.Run) -> None:
        hdf5 = h5.HDF5(hdf5_path=hdf5_path)
        self = cls(hdf5=hdf5, run=run)
        self._init_hdf5()
        self._run_to_hdf5()

    def _init_hdf5(self) -> None:
        if self._is_initialized():
            return
        init_meta = self._generate_init_meta()
        self.hdf5.append_attributes(init_meta)
        (
            h5.Group(config.ModelStorageGroupName.MODELS.value)
            .append_group(h5.Group(config.ModelStorageGroupName.FMUS.value))
            .append_group(
                h5.Group(config.ModelStorageGroupName.PYTHON_MODELS.value)
                .append_group(h5.Group(config.ModelStorageGroupName.CLASSES.value))
                .append_group(h5.Group(config.ModelStorageGroupName.SOURCE_CODE.value))
            )
            .to_hdf5(self.hdf5)
        )

    def _is_initialized(self) -> bool:
        init_meta = self.hdf5.read_attributes()
        init_meta_keys = set(init_meta.keys())
        if not init_meta_keys.issubset(config.HDF5FileMetaKey.get_values()):
            return False
        for path in config.ModelStorageGroupName.absolute_paths():
            if path not in self.hdf5:
                return False
        return True

    def _generate_init_meta(self) -> dict[str, str]:
        return {
            config.HDF5FileMetaKey.INITIALIZATION_DATE.value: datetime.now().strftime(
                "%d-%b-%Y %H:%M:%S"
            ),
            config.HDF5FileMetaKey.CREATED_WITH_SOFIRPY.value: "https://sofirpy.readthedocs.io",
            config.HDF5FileMetaKey.SOFIRPY_VERSION.value: sofirpy.__version__,
        }

    def _run_to_hdf5(self) -> None:
        logging.basicConfig(
            format="RunToHDF5::%(levelname)s::%(message)s",
            level=logging.INFO,
            force=True,
        )
        if self.run.run_name in self.hdf5:
            raise ValueError(
                f"Run '{self.run.run_name}' already exists in '{self.hdf5.hdf5_path}'."
            )
        model_storage_group = h5.Group.from_hdf5(
            self.hdf5, config.ModelStorageGroupName.MODELS.value, read_data=False
        )
        run_group = self._create_run_group_without_models()

        models_group = h5.Group(name=config.RunGroupName.MODELS.value)

        fmus_group = self._create_fmus_group(model_storage_group)
        models_group.append_group(fmus_group)

        python_models_group = self._create_python_models_group(model_storage_group)
        models_group.append_group(python_models_group)

        run_group.append_group(models_group)
        try:
            run_group.to_hdf5(self.hdf5)
            model_storage_group.to_hdf5(self.hdf5)
        except Exception as e:
            run_group.delete(self.hdf5)
            raise e
        logging.info(
            f"Successfully created run '{self.run.run_name}' at '{self.hdf5.hdf5_path}'"
        )

    def _create_run_group_without_models(self) -> h5.Group:
        return (
            h5.Group(name=self.run.run_name)
            .append_attribute(
                h5.Attribute(
                    attributes=self.serializer.run_meta_serializer.serialize(self.run)
                )
            )
            .append_dataset(
                h5.Dataset(
                    name=config.RunDatasetName.CONFIG.value,
                    data=self.serializer.config_serializer.serialize(self.run),
                )
            )
            .append_dataset(
                h5.Dataset(
                    name=config.RunDatasetName.DEPENDENCIES.value,
                    data=self.serializer.dependencies_serializer.serialize(self.run),
                )
            )
            .append_group(
                h5.Group(config.RunGroupName.SIMULATION_RESULTS.value)
                .append_attribute(
                    h5.Attribute(
                        attributes=self.serializer.simulation_config_serializer.serialize(
                            self.run
                        )
                    )
                )
                .append_dataset(
                    h5.Dataset(
                        name=config.RunDatasetName.TIME_SERIES.value,
                        data=self.serializer.time_series_serializer.serialize(self.run),
                    ).append_attribute(
                        h5.Attribute(
                            attributes=self.serializer.units_serializer.serialize(
                                self.run
                            )
                        )
                    )
                )
            )
        )

    def _create_fmus_group(self, model_storage_group: h5.Group) -> h5.Group:
        fmu_storage_group = model_storage_group.get_group(
            config.ModelStorageGroupName.FMUS.value
        )
        fmus_run_group = h5.Group(config.RunGroupName.FMUS.value)
        for fmu_name in self.run._models.fmus:
            fmu_group = (
                h5.Group(fmu_name)
                .append_dataset(
                    h5.Dataset(
                        name=config.RunDatasetName.CONNECTIONS.value,
                        data=self.serializer.connections_serializer.serialize(
                            self.run, model_name=fmu_name
                        ),
                    )
                )
                .append_dataset(
                    h5.Dataset(
                        name=config.RunDatasetName.START_VALUES.value,
                        data=self.serializer.start_values_serializer.serialize(
                            self.run, model_name=fmu_name
                        ),
                    )
                )
                .append_dataset(
                    h5.Dataset(
                        name=config.RunDatasetName.PARAMETERS_TO_LOG.value,
                        data=self.serializer.parameters_to_log_serializer.serialize(
                            self.run, model_name=fmu_name
                        ),
                    )
                )
            )
            fmu_reference_dataset = h5.Dataset(
                name=config.RunDatasetName.FMU_REFERENCE.value,
                data=self.serializer.fmu_reference_serializer.serialize(
                    self.run, fmu_name=fmu_name
                ),
            )
            fmu_group.append_dataset(fmu_reference_dataset)
            fmu_hash = fmu_reference_dataset.data
            try:
                fmu_storage_group.get_dataset(fmu_hash)
            except KeyError:
                fmu_storage_group.append_dataset(
                    h5.Dataset(
                        name=fmu_hash,
                        data=self.serializer.fmu_storage_serializer.serialize(
                            self.run, fmu_name=fmu_name
                        ),
                    )
                )
            fmus_run_group.append_group(fmu_group)
        return fmus_run_group

    def _create_python_models_group(self, model_storage_group: h5.Group) -> h5.Group:
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
        for python_model_name in self.run._models.python_models:
            python_model_group = (
                h5.Group(python_model_name)
                .append_dataset(
                    h5.Dataset(
                        name=config.RunDatasetName.CONNECTIONS.value,
                        data=self.serializer.connections_serializer.serialize(
                            self.run, model_name=python_model_name
                        ),
                    )
                )
                .append_dataset(
                    h5.Dataset(
                        name=config.RunDatasetName.START_VALUES.value,
                        data=self.serializer.start_values_serializer.serialize(
                            self.run, model_name=python_model_name
                        ),
                    )
                )
                .append_dataset(
                    h5.Dataset(
                        name=config.RunDatasetName.PARAMETERS_TO_LOG.value,
                        data=self.serializer.parameters_to_log_serializer.serialize(
                            self.run, model_name=python_model_name
                        ),
                    )
                )
            )
            python_model_class_reference_dataset = h5.Dataset(
                name=config.RunDatasetName.REFERENCE_CLASS.value,
                data=self.serializer.python_model_class_reference_serializer.serialize(
                    self.run, python_model_name=python_model_name
                ),
            )
            python_model_group.append_dataset(python_model_class_reference_dataset)
            model_class_hash = python_model_class_reference_dataset.data
            try:
                python_model_classes_storage_group.get_dataset(model_class_hash)
            except KeyError:
                python_model_class_storage_dataset = h5.Dataset(
                    name=model_class_hash,
                    data=self.serializer.python_model_class_storage_serializer.serialize(
                        self.run, python_model_name=python_model_name
                    ),
                )
                python_model_classes_storage_group.append_dataset(
                    python_model_class_storage_dataset
                )
            python_model_source_code_reference_dataset = h5.Dataset(
                name=config.RunDatasetName.REFERENCE_SOURCE_CODE.value,
                data=self.serializer.python_model_source_code_reference_serializer.serialize(
                    self.run, python_model_name=python_model_name
                ),
            )
            python_model_group.append_dataset(
                python_model_source_code_reference_dataset
            )
            model_source_code_hash = python_model_source_code_reference_dataset.data
            try:
                python_model_source_code_storage_group.get_dataset(
                    model_source_code_hash
                )
            except KeyError:
                python_model_source_code_storage_dataset = h5.Dataset(
                    name=model_source_code_hash,
                    data=self.serializer.python_model_source_code_storage_serializer.serialize(
                        self.run, python_model_name=python_model_name
                    ),
                )
                python_model_source_code_storage_group.append_dataset(
                    python_model_source_code_storage_dataset
                )
            python_models_run_group.append_group(python_model_group)
        return python_models_run_group
