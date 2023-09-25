from __future__ import annotations

import json
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, cast

import cloudpickle
import pandas as pd

import sofirpy.rdm.hdf5.config as config
import sofirpy.rdm.hdf5.hdf5 as h5
import sofirpy.rdm.run as rdm_run


class Deserializer(ABC):
    @staticmethod
    @abstractmethod
    def deserialize(run_group: h5.Group, *args: Any, **kwargs: Any) -> Any:
        ...


class RunMeta(Deserializer):
    @staticmethod
    def deserialize(run_group: h5.Group, *args: Any, **kwargs: Any) -> rdm_run._RunMeta:
        assert run_group.attribute is not None
        assert run_group.attribute.attributes is not None
        dependencies = json.loads(
            run_group.get_dataset(config.RunDatasetName.DEPENDENCIES.value).data
        )
        return rdm_run._RunMeta(
            **run_group.attribute.attributes, dependencies=dependencies
        )


class SimulationConfig(Deserializer):
    @staticmethod
    def deserialize(
        run_group: h5.Group, *args: Any, **kwargs: Any
    ) -> rdm_run._SimulationConfig:
        simulation_results_group = run_group.get_group(
            config.RunGroupName.SIMULATION_RESULTS.value
        )
        assert simulation_results_group.attribute is not None
        assert simulation_results_group.attribute.attributes is not None
        return rdm_run._SimulationConfig(
            **simulation_results_group.attribute.attributes
        )


class Results(Deserializer):
    @staticmethod
    def deserialize(run_group: h5.Group, *args: Any, **kwargs: Any) -> rdm_run._Results:
        simulation_results_group = run_group.get_group(
            config.RunGroupName.SIMULATION_RESULTS.value
        )
        _time_series = simulation_results_group.datasets._datasets[
            config.RunDatasetName.TIME_SERIES.value
        ].data
        time_series = pd.DataFrame.from_records(_time_series)
        units_attr = simulation_results_group.datasets._datasets[
            config.RunDatasetName.TIME_SERIES.value
        ].attribute
        assert units_attr is not None
        units = units_attr.attributes
        assert units is not None
        units = {name: unit if unit else None for name, unit in units.items()}
        return rdm_run._Results(time_series, units)


class Models(Deserializer):
    @staticmethod
    def deserialize(
        run_group: h5.Group,
        *args: Any,
        **kwargs: Any,
    ) -> rdm_run._Models:
        hdf5: h5.HDF5 = kwargs["hdf5"]
        fmu_models_group = run_group.get_group(
            config.RunGroupName.get_fmu_models_path()
        )
        fmus: dict[str, rdm_run._Fmu] = {}
        for name, group in fmu_models_group.groups._groups.items():
            connections = json.loads(
                cast(
                    bytes,
                    group.get_dataset(config.RunDatasetName.CONNECTIONS.value).data,
                )
            )
            start_values = json.loads(
                cast(
                    bytes,
                    group.get_dataset(config.RunDatasetName.START_VALUES.value).data,
                )
            )
            parameters_to_log = json.loads(
                cast(
                    bytes,
                    group.get_dataset(
                        config.RunDatasetName.PARAMETERS_TO_LOG.value
                    ).data,
                )
            )
            reference = cast(
                bytes, group.get_dataset(config.RunDatasetName.FMU_REFERENCE.value).data
            ).decode()
            fmu_content = cast(
                bytes,
                hdf5.read_data(reference, config.ModelStorageGroupName.get_fmu_path()),
            )
            tmp_dir = Path(tempfile.mkdtemp())
            fmu_path = tmp_dir / f"{name}.fmu"
            fmu_path.touch()
            assert fmu_content is not None
            with open(fmu_path, "wb") as fmu_file:
                fmu_file.write(fmu_content)
            fmus[name] = rdm_run._Fmu(
                name,
                connections=connections[config.RunDatasetName.CONNECTIONS.value],
                start_values=start_values[config.RunDatasetName.START_VALUES.value],
                parameters_to_log=parameters_to_log[
                    config.RunDatasetName.PARAMETERS_TO_LOG.value
                ],
                fmu_path=fmu_path,
            )
        python_models_group = run_group.get_group(
            config.RunGroupName.get_python_models_path()
        )
        python_models: dict[str, rdm_run._PythonModel] = {}
        for name, group in python_models_group.groups._groups.items():
            connections = json.loads(
                cast(
                    bytes,
                    group.get_dataset(config.RunDatasetName.CONNECTIONS.value).data,
                )
            )
            start_values = json.loads(
                cast(
                    bytes,
                    group.get_dataset(config.RunDatasetName.START_VALUES.value).data,
                )
            )
            parameters_to_log = json.loads(
                cast(
                    bytes,
                    group.get_dataset(
                        config.RunDatasetName.PARAMETERS_TO_LOG.value
                    ).data,
                )
            )
            class_reference = cast(
                bytes,
                group.get_dataset(config.RunDatasetName.REFERENCE_CLASS.value).data,
            ).decode()
            source_code_reference = cast(
                bytes,
                group.get_dataset(
                    config.RunDatasetName.REFERENCE_SOURCE_CODE.value
                ).data,
            ).decode()
            source_code = cast(
                bytes,
                hdf5.read_data(
                    source_code_reference,
                    config.ModelStorageGroupName.get_source_code_path(),
                ),
            ).decode()
            pickled_class = hdf5.read_data(
                class_reference, config.ModelStorageGroupName.get_classes_path()
            )
            model_class = cloudpickle.loads(pickled_class)
            python_models[name] = rdm_run._PythonModel(
                name,
                connections=connections[config.RunDatasetName.CONNECTIONS.value],
                start_values=start_values[config.RunDatasetName.START_VALUES.value],
                parameters_to_log=parameters_to_log[
                    config.RunDatasetName.PARAMETERS_TO_LOG.value
                ],
                code=source_code,
                model_class=model_class,
            )
        return rdm_run._Models(
            fmus,
            python_models,
        )
