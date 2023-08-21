from __future__ import annotations

import hashlib
import inspect
import json
from abc import ABC, abstractmethod
from dataclasses import asdict
from typing import Any

import cloudpickle
import numpy as np
import pandas as pd

from sofirpy import Run


class Serializer(ABC):
    @staticmethod
    @abstractmethod
    def serialize(run: Run, *args, **kwargs) -> Any:
        ...


class AttributeSerializer(Serializer):
    @staticmethod
    @abstractmethod
    def serialize(run: Run) -> dict[str, Any]:
        ...


class RunMeta(AttributeSerializer):
    @staticmethod
    def serialize(run: Run) -> dict[str, Any]:
        return asdict(run._run_meta)


class Config(Serializer):
    @staticmethod
    def serialize(run: Run) -> Any:
        return json.dumps(run.get_config())


class SimulationConfig(AttributeSerializer):
    @staticmethod
    def serialize(run: Run) -> dict[str, Any]:
        return run._simulation_config.to_dict()


class Units(AttributeSerializer):
    @staticmethod
    def serialize(run: Run) -> dict[str, Any]:
        return {k: v if v is not None else "" for k, v in run._results.units.items()}


class TimeSeries(Serializer):
    @staticmethod
    def serialize(run: Run) -> np.recarray[Any, Any]:
        if run._results is None:
            raise ValueError
        return run._results.time_series.to_records(index=False)


class Connections(Serializer):
    @staticmethod
    def serialize(run: Run, model_name: str) -> Any:
        model = run.models[model_name]
        return json.dumps({"connections": model.connections or []})


class StartValues(Serializer):
    @staticmethod
    def serialize(run: Run, model_name: str) -> Any:
        model = run.models[model_name]
        return json.dumps({"start_values": model.start_values or {}})


class ParametersToLog(Serializer):
    @staticmethod
    def serialize(run: Run, model_name: str) -> Any:
        model = run.models[model_name]
        return json.dumps({"parameters_to_log": model.parameters_to_log or []})


class FmuReference(Serializer):
    @staticmethod
    def serialize(run: Run, fmu_name: str) -> Any:
        fmu_path = run.get_fmu_path(fmu_name)
        fmu_content = fmu_path.open("rb").read()
        return hashlib.sha256(fmu_content).hexdigest()


class FmuStorage(Serializer):
    @staticmethod
    def serialize(run: Run, fmu_name: str) -> Any:
        fmu_path = run.get_fmu_path(fmu_name)
        return fmu_path.open("rb").read()


class PythonModelInstanceReference(Serializer):
    @staticmethod
    def serialize(run: Run, python_model_name: str) -> Any:
        model = run.get_model_instance(python_model_name)
        cloudpickle.register_pickle_by_value(inspect.getmodule(model))
        pickled_python_model = cloudpickle.dumps(model)
        model_hash = hashlib.sha256(pickled_python_model).hexdigest()
        return model_hash


class PythonModelInstanceStorage(Serializer):
    @staticmethod
    def serialize(run: Run, python_model_name: str) -> Any:
        model = run.get_model_instance(python_model_name)
        cloudpickle.register_pickle_by_value(inspect.getmodule(model))
        return cloudpickle.dumps(model)


class PythonModelSourceCodeReference(Serializer):
    @staticmethod
    def serialize(run: Run, python_model_name: str) -> Any:
        source_code = run.get_source_code_of_python_model(python_model_name)
        source_code_hash = hashlib.sha256(source_code.encode("utf-8")).hexdigest()
        return source_code_hash


class PythonModelSourceCodeStorage(Serializer):
    @staticmethod
    def serialize(run: Run, python_model_name: str) -> Any:
        return run.get_source_code_of_python_model(python_model_name)
