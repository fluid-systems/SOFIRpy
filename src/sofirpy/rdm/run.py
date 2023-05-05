from __future__ import annotations

import dataclasses as dc
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import (
    Any,
    ClassVar,
    Final,
    Iterable,
    Literal,
    Optional,
    TypedDict,
    Union,
    cast,
)

import pandas as pd
import pydantic
from typing_extensions import NotRequired, Self

import sofirpy
import sofirpy.rdm.run_group as rg
import sofirpy.utils as utils
from sofirpy.simulation.simulation import (
    ConnectionKeys,
    Connections,
    ConnectionsConfig,
    FmuPaths,
    ModelInstances,
    ParametersToLog,
    StartValues,
    Units,
    _Connection,
    simulate,
)
from sofirpy.simulation.simulation_entity import SimulationEntity, StartValue

CONFIG_KEY_TYPE = Literal["run_meta", "models", "simulation_config"]


class Config(TypedDict):
    run_meta: MetaConfig
    models: dict[str, ModelConfig]
    simulation_config: _SimulationConfig


class MetaConfig(TypedDict):
    description: str
    keywords: list[str]


class ModelConfig(TypedDict):
    start_values: NotRequired[dict[str, StartValue]]
    connections: NotRequired[Connections]
    parameters_to_log: NotRequired[list[str]]


class _SimulationConfig(TypedDict):
    stop_time: float
    step_size: float
    logging_step_size: NotRequired[float]


@dataclass
class Run:
    run_name: str
    run_meta: RunMeta
    _models: Models
    simulation_config: SimulationConfig
    results: Optional[Results] = None

    def __repr__(self) -> str:
        return f"Run: '{self.run_name}'\nDescription: {self.description}"

    @property
    def description(self) -> str:
        return self.run_meta.description

    @description.setter
    def description(self, description: str) -> None:
        self.run_meta.description = description

    @property
    def keywords(self) -> list[str]:
        return self.run_meta.keywords

    @keywords.setter
    def keywords(self, keywords: list[str]) -> None:
        self.run_meta.keywords = keywords

    def remove_keyword(self, keyword: str) -> None:
        self.run_meta.keywords.remove(keyword)

    def add_keyword(self, keyword: str) -> None:
        self.run_meta.keywords.append(keyword)

    @property
    def sofirpy_version(self) -> str:
        return self.run_meta.sofirpy_version

    @property
    def python_version(self) -> str:
        return self.run_meta.python_version

    @property
    def stop_time(self) -> float:
        return self.simulation_config.stop_time

    @stop_time.setter
    def stop_time(self, stop_time: float) -> None:
        self.simulation_config.stop_time = stop_time

    @property
    def step_size(self) -> float:
        return self.simulation_config.step_size

    @step_size.setter
    def step_size(self, step_size: float) -> None:
        self.simulation_config.step_size = step_size

    @property
    def models(self) -> dict[str, Model]:
        return self._models.models

    def change_model_name(self, prev_model_name: str, new_model_name: str) -> None:
        self._models.change_model_name(prev_model_name, new_model_name)

    @property
    def start_values(self) -> Optional[StartValues]:
        return self._models.start_values

    @start_values.setter
    def start_values(self, start_values: Optional[StartValues]) -> None:
        self._models.start_values = start_values

    def get_start_values_of_model(
        self, model_name: str
    ) -> Optional[dict[str, StartValue]]:
        return self._models.get_start_values_of_model(model_name)

    def set_start_values_of_model(
        self, model_name: str, start_values: dict[str, StartValue]
    ) -> None:
        self._models.set_start_values_of_model(model_name, start_values)

    def remove_start_values_of_model(self, model_name: str) -> None:
        self._models.remove_start_values_of_model(model_name)

    def get_start_value(
        self, model_name: str, parameter_name: str
    ) -> Optional[StartValue]:
        return self._models.get_start_value(model_name, parameter_name)

    def set_start_value(
        self, model_name: str, parameter_name: str, value: StartValue
    ) -> None:
        self._models.set_start_value(model_name, parameter_name, value)

    def remove_start_value(self, model_name: str, parameter_name: str) -> None:
        self._models.remove_start_value(model_name, parameter_name)

    @property
    def connections(self) -> Optional[ConnectionsConfig]:
        return self._models.connections_config

    @connections.setter
    def connections(self, connections: ConnectionsConfig) -> None:
        self._models.connections_config = connections

    def get_connections_of_model(self, model_name: str) -> Optional[Connections]:
        return self._models.get_connections_of_model(model_name)

    def set_connections_of_model(
        self, model_name: str, connections: Connections
    ) -> None:
        self._models.set_connections_of_model(model_name, connections)

    def remove_connections_of_model(self, model_name: str) -> None:
        self._models.remove_connections_of_model(model_name)

    def get_connection(self, model_name: str, input_name: str) -> Optional[_Connection]:
        return self._models.get_connection(model_name, input_name)

    def set_connection(self, model_name: str, connection: _Connection) -> None:
        self._models.set_connection(model_name, connection)

    def remove_connection(self, model_name: str, input_name: str) -> None:
        self._models.remove_connection(model_name, input_name)

    @property
    def parameters_to_log(self) -> Optional[ParametersToLog]:
        return self._models.parameters_to_log

    @parameters_to_log.setter
    def parameters_to_log(self, parameters_to_log: Optional[ParametersToLog]) -> None:
        self._models.parameters_to_log = parameters_to_log

    def get_parameters_to_log_of_model(self, model_name: str) -> Optional[list[str]]:
        return self._models.get_parameters_to_log_of_model(model_name)

    def set_parameters_to_log_of_model(
        self, model_name: str, parameters_to_log: list[str]
    ) -> None:
        self._models.set_parameters_to_log_of_model(model_name, parameters_to_log)

    def remove_parameters_to_log_of_model(self, model_name: str) -> None:
        self._models.remove_parameters_to_log_of_model(model_name)

    def append_parameter_to_log(self, model_name: str, parameter_name: str) -> None:
        self._models.append_parameter_to_log(model_name, parameter_name)

    def remove_parameter_to_log(self, model_name: str, parameter_name: str) -> None:
        self._models.remove_parameter_to_log(model_name, parameter_name)

    @classmethod
    def from_config(
        cls,
        run_name: str,
        config_path: Path,
        fmu_paths: Optional[FmuPaths] = None,
        model_instances: Optional[ModelInstances] = None,
    ) -> Self:
        with open(config_path) as config_file:
            config: Config = json.load(config_file)

        return cls(
            run_name=run_name,
            run_meta=RunMeta.from_config(config),
            _models=Models.from_config(config, fmu_paths, model_instances),
            simulation_config=SimulationConfig.from_config(config),
        )

    @classmethod
    def from_hdf5(cls, run_name: str, hdf5_path: Path) -> Run:
        return rg.RunGroup.from_hdf5(hdf5_path, run_name).to_run()

    def get_config(self) -> Config:
        return {
            self.run_meta.CONFIG_KEY: self.run_meta.to_dict(),
            self._models.CONFIG_KEY: self._models.to_dict(),
            self.simulation_config.CONFIG_KEY: self.simulation_config.to_dict(),
        }

    def simulate(self) -> None:
        results = simulate(
            **self.simulation_config.get_simulation_args(),
            **self._models.get_simulation_args(),
        )
        assert isinstance(results, tuple)
        time_series, units = results
        self.results = Results(time_series=time_series, units=units)

    def to_hdf5(self, hdf5_path: Path) -> None:
        rg.RunGroup.from_run(self).to_hdf5(hdf5_path)

    def to_run_group(self) -> rg.RunGroup:
        return rg.RunGroup.from_run(self)


class Results(pydantic.BaseModel):
    time_series: pd.DataFrame
    units: Units

    class Config:
        arbitrary_types_allowed = True


@pydantic.dataclasses.dataclass
class RunMeta:
    description: str
    keywords: list[str]
    sofirpy_version: str
    python_version: str
    date: str

    CONFIG_KEY: ClassVar[CONFIG_KEY_TYPE] = "run_meta"

    @classmethod
    def from_config(cls, config: Config) -> Self:
        return cls(
            **config[cls.CONFIG_KEY],
            sofirpy_version=sofirpy.__version__,
            python_version=sys.version,
            date=datetime.now().strftime("%d-%b-%Y %H:%M:%S"),
        )

    @pydantic.validator("keywords", pre=True)
    def convert_numpy_array(cls, keywords: Iterable[str]) -> list[str]:
        return list(keywords)

    def to_dict(self) -> MetaConfig:
        meta_config = cast(
            MetaConfig,
            {
                field_name: self.__getattribute__(field_name)
                for field_name in MetaConfig.__annotations__.keys()
            },
        )
        return meta_config


@pydantic.dataclasses.dataclass
class SimulationConfig:
    stop_time: float
    step_size: float
    logging_step_size: Optional[float] = None
    get_units: bool = True

    CONFIG_KEY: ClassVar[CONFIG_KEY_TYPE] = "simulation_config"

    @classmethod
    def from_config(cls, config: Config) -> Self:
        return cls(**config[cls.CONFIG_KEY])

    def to_dict(self) -> _SimulationConfig:
        return cast(_SimulationConfig, asdict(self))

    def get_simulation_args(self) -> _SimulationConfig:
        return self.to_dict()


@dataclass
class Models:
    fmus: dict[str, Fmu]
    python_models: dict[str, PythonModel]

    CONFIG_KEY: ClassVar[CONFIG_KEY_TYPE] = "models"

    @classmethod
    def from_config(
        cls,
        config: Config,
        fmu_paths: Optional[FmuPaths] = None,
        model_instances: Optional[ModelInstances] = None,
    ) -> Self:
        model_config = cast(dict[str, ModelConfig], config[cls.CONFIG_KEY])
        # TODO check if all names in fmu_paths and model_instances are in config
        fmu_paths = fmu_paths or {}
        fmus = {
            name: Fmu(
                name=name,
                fmu_path=utils.convert_str_to_path(path, "fmu_path"),
                **model_config[name],
            )
            for name, path in fmu_paths.items()
        }
        model_instances = model_instances or {}
        python_models = {
            name: PythonModel(
                name=name, model_instance=model_instance, **model_config[name]
            )
            for name, model_instance in model_instances.items()
        }
        return cls(fmus=fmus, python_models=python_models)

    @property
    def models(self) -> dict[str, Model]:
        return {**self.fmus, **self.python_models}

    def change_model_name(self, prev_name: str, new_name: str) -> None:
        if prev_name not in self.models:
            raise ValueError
        if prev_name in self.fmus:
            self.fmus[new_name] = self.fmus.pop(prev_name)
        if prev_name in self.python_models:
            self.python_models[new_name] = self.python_models.pop(prev_name)
        self.models[new_name].name = new_name
        self.update_connections(prev_name, new_name)

    def update_connections(
        self, prev_name: str, new_name: str
    ) -> None:  # TODO maybe instead of doing this link model class in connections --> would automatically update name
        for model in self.models.values():
            model.update_connections(prev_name, new_name)

    @property
    def start_values(self) -> Optional[StartValues]:
        start_values = {
            name: model.start_values
            for name, model in self.models.items()
            if model.start_values
        }
        return start_values or None

    @start_values.setter
    def start_values(self, start_values: Optional[StartValues]) -> None:
        if start_values is None:
            start_values = {}
        for model_name, model in self.models.items():
            model.start_values = start_values.get(model_name)

    def get_start_values_of_model(
        self, model_name: str
    ) -> Optional[dict[str, StartValue]]:
        return self.models[model_name].start_values

    def set_start_values_of_model(
        self, model_name: str, start_values: dict[str, StartValue]
    ) -> None:
        self.models[model_name].start_values = start_values

    def remove_start_values_of_model(self, model_name: str) -> None:
        self.models[model_name].start_values = None

    def get_start_value(
        self, model_name: str, parameter_name: str
    ) -> Optional[StartValue]:
        return self.models[model_name].get_start_value(parameter_name)

    def set_start_value(
        self, model_name: str, parameter_name: str, value: StartValue
    ) -> None:
        self.models[model_name].set_start_value(parameter_name, value)

    def remove_start_value(self, model_name: str, parameter_name: str) -> None:
        self.models[model_name].remove_start_value(parameter_name)

    @property
    def connections_config(self) -> Optional[ConnectionsConfig]:
        connections_config = {
            name: model.connections
            for name, model in self.models.items()
            if model.connections
        }
        return connections_config or None

    @connections_config.setter
    def connections_config(
        self, connections_config: Optional[ConnectionsConfig]
    ) -> None:
        if connections_config is None:
            connections_config = {}
        for model_name, model in self.models.items():
            model.connections = connections_config.get(model_name)

    def get_connections_of_model(self, model_name: str) -> Optional[Connections]:
        return self.models[model_name].connections

    def set_connections_of_model(
        self, model_name: str, connections: Connections
    ) -> None:
        self.models[model_name].connections = connections

    def remove_connections_of_model(self, model_name: str) -> None:
        self.models[model_name].connections = None

    def get_connection(self, model_name: str, input_name: str) -> Optional[_Connection]:
        return self.models[model_name].get_connection(input_name)

    def set_connection(self, model_name: str, connection: _Connection) -> None:
        self.models[model_name].set_connection(connection)

    def remove_connection(self, model_name: str, input_name: str) -> None:
        self.models[model_name].remove_connection(input_name)

    @property
    def parameters_to_log(self) -> Optional[ParametersToLog]:
        parameters_to_log = {
            name: model.parameters_to_log
            for name, model in self.models.items()
            if model.parameters_to_log
        }
        return parameters_to_log or None

    @parameters_to_log.setter
    def parameters_to_log(self, parameter_to_log: Optional[ParametersToLog]) -> None:
        if parameter_to_log is None:
            parameter_to_log = {}
        for model_name, model in self.models.items():
            model.parameters_to_log = parameter_to_log.get(model_name)

    def get_parameters_to_log_of_model(self, model_name: str) -> Optional[list[str]]:
        return self.models[model_name].parameters_to_log

    def set_parameters_to_log_of_model(
        self, model_name: str, parameters_to_log: list[str]
    ) -> None:
        self.models[model_name].parameters_to_log = parameters_to_log

    def remove_parameters_to_log_of_model(self, model_name: str) -> None:
        self.models[model_name].parameters_to_log = None

    def append_parameter_to_log(self, model_name: str, parameter_name: str) -> None:
        self.models[model_name].append_parameter_to_log(parameter_name)

    def remove_parameter_to_log(self, model_name: str, parameter_name: str) -> None:
        self.models[model_name].remove_parameter_to_log(parameter_name)

    @property
    def fmu_paths(self) -> FmuPaths:
        return {name: fmu.fmu_path for name, fmu in self.fmus.items()}

    @property
    def model_instances(self) -> ModelInstances:
        return {
            name: python_model.model_instance
            for name, python_model in self.python_models.items()
        }

    def to_dict(self) -> dict[str, ModelConfig]:
        return {name: model.to_dict() for name, model in self.models.items()}

    def get_simulation_args(self) -> dict[str, Any]:
        return {
            "start_values": self.start_values,
            "connections_config": self.connections_config,
            "parameters_to_log": self.parameters_to_log,
            "fmu_paths": self.fmu_paths,
            "model_instances": self.model_instances,
        }


class Model(pydantic.BaseModel):
    name: str
    connections: Optional[Connections]
    start_values: Optional[dict[str, StartValue]]
    parameters_to_log: Optional[list[str]]

    class Config:
        arbitrary_types_allowed = True

    def get_start_value(self, parameter_name: str) -> Optional[StartValue]:
        if self.start_values is None:
            return None
        return self.start_values.get(parameter_name)

    def set_start_value(self, parameter_name: str, value: StartValue) -> None:
        if self.start_values is None:
            self.start_values = {}
        self.start_values[parameter_name] = value

    def remove_start_value(self, parameter_name: str) -> None:
        if self.start_values is None:
            return
        del self.start_values[parameter_name]

    def get_connection(self, input_name: str) -> Optional[_Connection]:
        if self.connections is None:
            return None
        for connection in self.connections:
            if connection[ConnectionKeys.INPUT_PARAMETER.value] == input_name:
                return connection
        return None

    def set_connection(self, connection: _Connection) -> None:
        if self.connections is None:
            self.connections = []
        self.connections.append(connection)

    def remove_connection(self, input_name: str) -> None:
        if self.connections is None:
            return
        for connection in self.connections:
            if connection[ConnectionKeys.INPUT_PARAMETER.value] == input_name:
                self.connections.remove(connection)

    def update_connections(self, prev_name: str, new_name: str) -> None:
        if self.connections is None:
            return
        for connection in self.connections:
            if connection[ConnectionKeys.CONNECTED_SYSTEM.value] == prev_name:
                connection[ConnectionKeys.CONNECTED_SYSTEM.value] = new_name

    def append_parameter_to_log(self, parameter_name: str) -> None:
        if self.parameters_to_log is None:
            self.parameters_to_log = []
        self.parameters_to_log.append(parameter_name)

    def remove_parameter_to_log(self, parameter_name: str) -> None:
        if self.parameters_to_log is None:
            return
        self.parameters_to_log.remove(parameter_name)

    def to_dict(self) -> ModelConfig:
        model_config = cast(
            ModelConfig,
            {
                field_name: self.__getattribute__(field_name)
                for field_name in ModelConfig.__annotations__.keys()
                if self.__getattribute__(field_name) is not None
            },
        )
        return model_config


class Fmu(Model):
    fmu_path: Path


class PythonModel(Model):
    model_instance: SimulationEntity
