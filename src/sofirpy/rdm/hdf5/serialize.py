from __future__ import annotations

import hashlib
import inspect
import json
import pickle
from abc import ABC, abstractmethod
from dataclasses import asdict
from typing import Any, cast

import cloudpickle
import numpy as np

import sofirpy.rdm.run as rdm_run


class Serializer(ABC):
    @staticmethod
    @abstractmethod
    def serialize(run: rdm_run.Run, *args: Any, **kwargs: Any) -> Any:
        ...


class AttributeSerializer(ABC):
    @staticmethod
    @abstractmethod
    def serialize(run: rdm_run.Run) -> dict[str, Any]:
        ...


class RunMeta(AttributeSerializer):
    @staticmethod
    def serialize(run: rdm_run.Run) -> dict[str, Any]:
        return asdict(run._run_meta)


class Config(Serializer):
    @staticmethod
    def serialize(run: rdm_run.Run, *args: Any, **kwargs: Any) -> Any:
        return json.dumps(run.get_config())


class Dependencies(Serializer):
    @staticmethod
    def serialize(run: rdm_run.Run, *args: Any, **kwargs: Any) -> Any:
        return json.dumps(run._run_meta.get_dependencies())


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


class TimeSeries(Serializer):
    @staticmethod
    def serialize(run: rdm_run.Run, *args: Any, **kwargs: Any) -> Any:
        if run._results is None:
            raise ValueError
        return run._results.time_series.to_records(index=False)


class Connections(Serializer):
    @staticmethod
    def serialize(run: rdm_run.Run, *args: Any, **kwargs: Any) -> Any:
        model = run.models[kwargs["model_name"]]
        return json.dumps({"connections": model.connections or []})


class StartValues(Serializer):
    @staticmethod
    def serialize(run: rdm_run.Run, *args: Any, **kwargs: Any) -> Any:
        model = run.models[kwargs["model_name"]]
        return json.dumps({"start_values": model.start_values or {}})


class ParametersToLog(Serializer):
    @staticmethod
    def serialize(run: rdm_run.Run, *args: Any, **kwargs: Any) -> Any:
        model = run.models[kwargs["model_name"]]
        return json.dumps({"parameters_to_log": model.parameters_to_log or []})


class FmuReference(Serializer):
    @staticmethod
    def serialize(run: rdm_run.Run, *args: Any, **kwargs: Any) -> Any:
        fmu_path = run.get_fmu_path(kwargs["fmu_name"])
        fmu_content = fmu_path.open("rb").read()
        return hashlib.sha256(fmu_content).hexdigest()


class FmuStorage(Serializer):
    @staticmethod
    def serialize(run: rdm_run.Run, *args: Any, **kwargs: Any) -> Any:
        fmu_path = run.get_fmu_path(kwargs["fmu_name"])
        return np.void(fmu_path.open("rb").read())


class PythonModelInstanceReference(Serializer):
    @staticmethod
    def serialize(run: rdm_run.Run, *args: Any, **kwargs: Any) -> Any:
        model = run.get_model_class(kwargs["python_model_name"])
        cloudpickle.register_pickle_by_value(inspect.getmodule(model))
        pickled_python_model = cloudpickle.dumps(model)
        model_hash = hashlib.sha256(pickled_python_model).hexdigest()
        return model_hash


class PythonModelClassStorage(Serializer):
    @staticmethod
    def serialize(run: rdm_run.Run, *args: Any, **kwargs: Any) -> Any:
        model = run.get_model_class(kwargs["python_model_name"])
        try:
            cloudpickle.register_pickle_by_value(inspect.getmodule(model))
        except pickle.PicklingError:
            return None
        return np.void(cloudpickle.dumps(model))


class PythonModelSourceCodeReference(Serializer):
    @staticmethod
    def serialize(run: rdm_run.Run, *args: Any, **kwargs: Any) -> Any:
        source_code = run.get_source_code_of_python_model(kwargs["python_model_name"])
        source_code_hash = hashlib.sha256(source_code.encode("utf-8")).hexdigest()
        return source_code_hash


class PythonModelSourceCodeStorage(Serializer):
    @staticmethod
    def serialize(run: rdm_run.Run, *args: Any, **kwargs: Any) -> Any:
        return run.get_source_code_of_python_model(kwargs["python_model_name"])
