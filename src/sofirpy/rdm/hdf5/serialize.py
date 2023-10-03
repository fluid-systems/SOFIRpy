"""This modules defines how a run is serialized."""
from __future__ import annotations

import hashlib
import inspect
import json
import pickle
from typing import Any, Protocol, cast

import cloudpickle
import numpy as np

import sofirpy.rdm.run as rdm_run


class DatasetSerializer(Protocol):
    @staticmethod
    def serialize(run: rdm_run.Run, *args: Any, **kwargs: Any) -> Any:
        ...


class AttributeSerializer(Protocol):
    @staticmethod
    def serialize(run: rdm_run.Run) -> dict[str, Any]:
        ...


class RunMeta(AttributeSerializer):
    @staticmethod
    def serialize(run: rdm_run.Run) -> dict[str, Any]:
        run_meta = run._run_meta.to_dict()
        del run_meta["dependencies"]
        return run_meta


class Config(DatasetSerializer):
    @staticmethod
    def serialize(run: rdm_run.Run, *args: Any, **kwargs: Any) -> Any:
        return json.dumps(run.get_config())


class Dependencies(DatasetSerializer):
    @staticmethod
    def serialize(run: rdm_run.Run, *args: Any, **kwargs: Any) -> Any:
        return json.dumps(run._run_meta.dependencies)


class SimulationConfig(AttributeSerializer):
    @staticmethod
    def serialize(run: rdm_run.Run) -> dict[str, Any]:
        return cast(dict[str, Any], run._simulation_config.to_dict())


class Units(AttributeSerializer):
    @staticmethod
    def serialize(run: rdm_run.Run) -> dict[str, Any]:
        assert run._results is not None
        if run._results.units is None:
            return {}
        return {k: v if v is not None else "" for k, v in run._results.units.items()}


class TimeSeries(DatasetSerializer):
    @staticmethod
    def serialize(run: rdm_run.Run, *args: Any, **kwargs: Any) -> Any:
        if run._results is None:
            raise ValueError
        return run._results.time_series.to_records(index=False)


class Connections(DatasetSerializer):
    @staticmethod
    def serialize(run: rdm_run.Run, *args: Any, **kwargs: Any) -> Any:
        model = run.models[kwargs["model_name"]]
        return json.dumps({"connections": model.connections or []})


class StartValues(DatasetSerializer):
    @staticmethod
    def serialize(run: rdm_run.Run, *args: Any, **kwargs: Any) -> Any:
        model = run.models[kwargs["model_name"]]
        return json.dumps({"start_values": model.start_values or {}})


class ParametersToLog(DatasetSerializer):
    @staticmethod
    def serialize(run: rdm_run.Run, *args: Any, **kwargs: Any) -> Any:
        model = run.models[kwargs["model_name"]]
        return json.dumps({"parameters_to_log": model.parameters_to_log or []})


class FmuReference(DatasetSerializer):
    @staticmethod
    def serialize(run: rdm_run.Run, *args: Any, **kwargs: Any) -> Any:
        fmu_path = run.get_fmu_path(kwargs["fmu_name"])
        fmu_content = fmu_path.open("rb").read()
        return hashlib.sha256(fmu_content).hexdigest()


class FmuStorage(DatasetSerializer):
    @staticmethod
    def serialize(run: rdm_run.Run, *args: Any, **kwargs: Any) -> Any:
        fmu_path = run.get_fmu_path(kwargs["fmu_name"])
        return np.void(fmu_path.open("rb").read())


class PythonModelClassReference(DatasetSerializer):
    @staticmethod
    def serialize(run: rdm_run.Run, *args: Any, **kwargs: Any) -> Any:
        model = run.get_model_class(kwargs["python_model_name"])
        cloudpickle.register_pickle_by_value(inspect.getmodule(model))
        pickled_python_model = cloudpickle.dumps(model)
        model_hash = hashlib.sha256(pickled_python_model).hexdigest()
        return model_hash


class PythonModelClassStorage(DatasetSerializer):
    @staticmethod
    def serialize(run: rdm_run.Run, *args: Any, **kwargs: Any) -> Any:
        model = run.get_model_class(kwargs["python_model_name"])
        try:
            cloudpickle.register_pickle_by_value(inspect.getmodule(model))
        except pickle.PicklingError:
            return None
        return np.void(cloudpickle.dumps(model))


class PythonModelSourceCodeReference(DatasetSerializer):
    @staticmethod
    def serialize(run: rdm_run.Run, *args: Any, **kwargs: Any) -> Any:
        source_code = run.get_source_code_of_python_model(kwargs["python_model_name"])
        source_code_hash = hashlib.sha256(source_code.encode("utf-8")).hexdigest()
        return source_code_hash


class PythonModelSourceCodeStorage(DatasetSerializer):
    @staticmethod
    def serialize(run: rdm_run.Run, *args: Any, **kwargs: Any) -> Any:
        return run.get_source_code_of_python_model(kwargs["python_model_name"])


class Serializer:
    run_meta_serializer: type[AttributeSerializer] = RunMeta
    simulation_config_serializer: type[AttributeSerializer] = SimulationConfig
    units_serializer: type[AttributeSerializer] = Units
    config_serializer: type[DatasetSerializer] = Config
    dependencies_serializer: type[DatasetSerializer] = Dependencies
    time_series_serializer: type[DatasetSerializer] = TimeSeries
    connections_serializer: type[DatasetSerializer] = Connections
    start_values_serializer: type[DatasetSerializer] = StartValues
    parameters_to_log_serializer: type[DatasetSerializer] = ParametersToLog
    fmu_reference_serializer: type[DatasetSerializer] = FmuReference
    fmu_storage_serializer: type[DatasetSerializer] = FmuStorage
    python_model_class_reference_serializer: type[
        DatasetSerializer
    ] = PythonModelClassReference
    python_model_class_storage_serializer: type[
        DatasetSerializer
    ] = PythonModelClassStorage
    python_model_source_code_reference_serializer: type[
        DatasetSerializer
    ] = PythonModelSourceCodeReference
    python_model_source_code_storage_serializer: type[
        DatasetSerializer
    ] = PythonModelSourceCodeStorage

    @classmethod
    def use_start_value_serializer(cls, serializer: type[DatasetSerializer]) -> None:
        cls.start_values_serializer = serializer
