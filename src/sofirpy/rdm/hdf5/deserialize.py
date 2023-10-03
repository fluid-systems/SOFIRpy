from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Protocol

import cloudpickle
import numpy as np
import pandas as pd

import sofirpy.rdm.hdf5.config as config
import sofirpy.rdm.hdf5.hdf5 as h5
import sofirpy.rdm.run as rdm_run


class Deserialize(Protocol):
    @staticmethod
    def deserialize(run_group: h5.Group, *args: Any, **kwargs: Any) -> Any:
        ...


class RunMeta(Deserialize):
    @staticmethod
    def deserialize(run_group: h5.Group, *args: Any, **kwargs: Any) -> rdm_run.RunMeta:
        assert run_group.attribute is not None
        assert run_group.attribute.attributes is not None
        dependencies = json.loads(
            run_group.get_dataset(config.RunDatasetName.DEPENDENCIES.value).data
        )
        return rdm_run.RunMeta(
            **run_group.attribute.attributes, dependencies=dependencies
        )


class SimulationConfig(Deserialize):
    @staticmethod
    def deserialize(
        run_group: h5.Group, *args: Any, **kwargs: Any
    ) -> rdm_run.SimulationConfig:
        simulation_results_group = run_group.get_group(
            config.RunGroupName.SIMULATION_RESULTS.value
        )
        assert simulation_results_group.attribute is not None
        assert simulation_results_group.attribute.attributes is not None
        return rdm_run.SimulationConfig(**simulation_results_group.attribute.attributes)


class TimeSeries(Deserialize):
    @staticmethod
    def deserialize(run_group: h5.Group, *args: Any, **kwargs: Any) -> Any:
        data = kwargs.get("data")
        assert isinstance(data, np.ndarray)
        return pd.DataFrame.from_records(data)


class Units(Deserialize):
    @staticmethod
    def deserialize(run_group: h5.Group, *args: Any, **kwargs: Any) -> Any:
        units = kwargs.get("data")
        assert isinstance(units, dict)
        return {name: unit if unit else None for name, unit in units.items()}


class Results(Deserialize):
    @staticmethod
    def deserialize(run_group: h5.Group, *args: Any, **kwargs: Any) -> rdm_run.Results:
        simulation_results_group = run_group.get_group(
            config.RunGroupName.SIMULATION_RESULTS.value
        )
        time_series = Deserializer.time_series.deserialize(
            run_group,
            data=simulation_results_group.datasets._datasets[
                config.RunDatasetName.TIME_SERIES.value
            ].data,
        )
        attributes = simulation_results_group.datasets._datasets[
            config.RunDatasetName.TIME_SERIES.value
        ].attribute
        assert attributes is not None
        units = Deserializer.units.deserialize(
            run_group,
            data=attributes.attributes,
        )

        return rdm_run.Results(time_series, units)


class Connections(Deserialize):
    @staticmethod
    def deserialize(run_group: h5.Group, *args: Any, **kwargs: Any) -> Any:
        data = kwargs.get("data")
        assert isinstance(data, bytes)
        return json.loads(data)


class StartValues(Deserialize):
    @staticmethod
    def deserialize(run_group: h5.Group, *args: Any, **kwargs: Any) -> Any:
        data = kwargs.get("data")
        assert isinstance(data, bytes)
        return json.loads(data)


class ParametersToLog(Deserialize):
    @staticmethod
    def deserialize(run_group: h5.Group, *args: Any, **kwargs: Any) -> Any:
        data = kwargs.get("data")
        assert isinstance(data, bytes)
        return json.loads(data)


class FmuReference(Deserialize):
    @staticmethod
    def deserialize(run_group: h5.Group, *args: Any, **kwargs: Any) -> Any:
        data = kwargs.get("data")
        assert isinstance(data, bytes)
        return data.decode()


class FmuContent(Deserialize):
    @staticmethod
    def deserialize(run_group: h5.Group, *args: Any, **kwargs: Any) -> Any:
        return kwargs.get("data")


class ClassReference(Deserialize):
    @staticmethod
    def deserialize(run_group: h5.Group, *args: Any, **kwargs: Any) -> Any:
        data = kwargs.get("data")
        assert isinstance(data, bytes)
        return data.decode()


class SourceCodeReference(Deserialize):
    @staticmethod
    def deserialize(run_group: h5.Group, *args: Any, **kwargs: Any) -> Any:
        data = kwargs.get("data")
        assert isinstance(data, bytes)
        return data.decode()


class ClassStorage(Deserialize):
    @staticmethod
    def deserialize(run_group: h5.Group, *args: Any, **kwargs: Any) -> Any:
        return cloudpickle.loads(kwargs.get("data"))


class SourceCodeStorage(Deserialize):
    @staticmethod
    def deserialize(run_group: h5.Group, *args: Any, **kwargs: Any) -> Any:
        data = kwargs.get("data")
        assert isinstance(data, bytes)
        return data.decode()


class Models(Deserialize):
    @staticmethod
    def deserialize(
        run_group: h5.Group,
        *args: Any,
        **kwargs: Any,
    ) -> rdm_run.Models:
        hdf5: h5.HDF5 = kwargs["hdf5"]
        fmu_models_group = run_group.get_group(
            config.RunGroupName.get_fmu_models_path()
        )
        fmus: dict[str, rdm_run.Fmu] = {}
        for name, group in fmu_models_group.groups._groups.items():
            connections = Deserializer.connections.deserialize(
                run_group,
                data=group.get_dataset(config.RunDatasetName.CONNECTIONS.value).data,
            )
            start_values = Deserializer.start_values.deserialize(
                run_group,
                data=group.get_dataset(config.RunDatasetName.START_VALUES.value).data,
            )

            parameters_to_log = Deserializer.parameters_to_log.deserialize(
                run_group,
                data=group.get_dataset(
                    config.RunDatasetName.PARAMETERS_TO_LOG.value
                ).data,
            )
            reference = Deserializer.fmu_reference.deserialize(
                run_group,
                data=group.get_dataset(config.RunDatasetName.FMU_REFERENCE.value).data,
            )
            fmu_content = Deserializer.fmu_content.deserialize(
                run_group,
                data=hdf5.read_data(
                    reference, config.ModelStorageGroupName.get_fmu_path()
                ),
            )
            tmp_dir = Path(tempfile.mkdtemp())
            fmu_path = tmp_dir / f"{name}.fmu"
            fmu_path.touch()
            assert fmu_content is not None
            with open(fmu_path, "wb") as fmu_file:
                fmu_file.write(fmu_content)
            fmus[name] = rdm_run.Fmu(
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
        python_models: dict[str, rdm_run.PythonModel] = {}
        for name, group in python_models_group.groups._groups.items():
            connections = Deserializer.connections.deserialize(
                run_group,
                data=group.get_dataset(config.RunDatasetName.CONNECTIONS.value).data,
            )
            start_values = Deserializer.start_values.deserialize(
                run_group,
                data=group.get_dataset(config.RunDatasetName.START_VALUES.value).data,
            )

            parameters_to_log = Deserializer.parameters_to_log.deserialize(
                run_group,
                data=group.get_dataset(
                    config.RunDatasetName.PARAMETERS_TO_LOG.value
                ).data,
            )
            class_reference = Deserializer.class_reference.deserialize(
                run_group,
                data=group.get_dataset(
                    config.RunDatasetName.REFERENCE_CLASS.value
                ).data,
            )
            source_code_reference = Deserializer.source_code_reference.deserialize(
                run_group,
                data=group.get_dataset(
                    config.RunDatasetName.REFERENCE_SOURCE_CODE.value
                ).data,
            )
            source_code = Deserializer.source_code_storage.deserialize(
                run_group,
                data=hdf5.read_data(
                    source_code_reference,
                    config.ModelStorageGroupName.get_source_code_path(),
                ),
            )
            model_class = Deserializer.class_storage.deserialize(
                run_group,
                data=hdf5.read_data(
                    class_reference, config.ModelStorageGroupName.get_classes_path()
                ),
            )
            python_models[name] = rdm_run.PythonModel(
                name,
                connections=connections[config.RunDatasetName.CONNECTIONS.value],
                start_values=start_values[config.RunDatasetName.START_VALUES.value],
                parameters_to_log=parameters_to_log[
                    config.RunDatasetName.PARAMETERS_TO_LOG.value
                ],
                code=source_code,
                model_class=model_class,
            )
        return rdm_run.Models(
            fmus,
            python_models,
        )


class Deserializer:
    run_meta: type[Deserialize] = RunMeta
    simulation_config: type[Deserialize] = SimulationConfig
    time_series: type[Deserialize] = TimeSeries
    units: type[Deserialize] = Units
    results: type[Deserialize] = Results
    models: type[Deserialize] = Models
    connections: type[Deserialize] = Connections
    start_values: type[Deserialize] = StartValues
    parameters_to_log: type[Deserialize] = ParametersToLog
    fmu_reference: type[Deserialize] = FmuReference
    fmu_content: type[Deserialize] = FmuContent
    class_reference: type[Deserialize] = ClassReference
    source_code_reference: type[Deserialize] = SourceCodeReference
    class_storage: type[Deserialize] = ClassStorage
    source_code_storage: type[Deserialize] = SourceCodeStorage

    @classmethod
    def use_start_values_deserializer(cls, deserializer: type[Deserialize]) -> None:
        cls.start_values = deserializer
