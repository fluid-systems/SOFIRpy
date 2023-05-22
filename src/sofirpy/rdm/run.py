"""This module allows to create, interact with and store a simulation run."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar, Iterable, Literal, Optional, TypedDict, cast

import pandas as pd
import pydantic
from typing_extensions import NotRequired, Self

import sofirpy
import sofirpy.rdm.run_group as rg
from sofirpy import utils
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

ConfigKeyType = Literal["run_meta", "models", "simulation_config"]


class _ConfigDict(TypedDict):
    run_meta: _MetaConfigDict
    models: dict[str, _ModelConfigDict]
    simulation_config: _SimulationConfigDict


class _MetaConfigDict(TypedDict):
    description: str
    keywords: list[str]


class _ModelConfigDict(TypedDict):
    start_values: NotRequired[dict[str, StartValue]]
    connections: NotRequired[Connections]
    parameters_to_log: NotRequired[list[str]]


class _SimulationConfigDict(TypedDict):
    stop_time: float
    step_size: float
    logging_step_size: NotRequired[float]


@dataclass
class Run:
    """Run object representing a simulation Run.

    Run can be initiated from a config file or loaded from a hdf5 file. It provides
    several methods for changing the configuration of the run. Runs can be saved to a
    hdf5 file.
    """

    run_name: str
    _run_meta: _RunMeta
    _models: _Models
    _simulation_config: _SimulationConfig
    _results: Optional[_Results] = None

    def __repr__(self) -> str:
        return f"Run: '{self.run_name}'\nDescription: '{self.description}'"

    @property
    def description(self) -> str:
        """Description of the Run.

        Returns:
            str: Description of the Run.
        """
        return self._run_meta.description

    @description.setter
    def description(self, description: str) -> None:
        """Description of the Run.

        Args:
            description (str): Description of the Run.
        """
        self._run_meta.description = description

    @property
    def keywords(self) -> list[str]:
        """Keywords describing the run.

        Returns:
            list[str]: Keywords describing the run.
        """
        return self._run_meta.keywords

    @keywords.setter
    def keywords(self, keywords: list[str]) -> None:
        """Keywords describing the run.

        Args:
            keywords (list[str]): Keywords describing the run.
        """
        self._run_meta.keywords = keywords

    def remove_keyword(self, keyword: str) -> None:
        """Remove a keyword from the list of keywords.

        Args:
            keyword (str): Keywords to be removed.
        """
        self._run_meta.keywords.remove(keyword)

    def add_keyword(self, keyword: str) -> None:
        """Add a keywords to the list of keywords.

        Args:
            keyword (str): Keyword to be added.
        """
        self._run_meta.keywords.append(keyword)

    @property
    def sofirpy_version(self) -> str:
        """Version of sofirpy the run was performed with.

        Returns:
            str: Version of sofirpy the run was performed with.
        """
        return self._run_meta.sofirpy_version

    @property
    def python_version(self) -> str:
        """Version of Python the run was performed with.

        Returns:
            str: Version of Python the run was performed with.
        """
        return self._run_meta.python_version

    @property
    def stop_time(self) -> float:
        """Stop time for the simulation.

        Returns:
            float: Stop time for the simulation.
        """
        return self._simulation_config.stop_time

    @stop_time.setter
    def stop_time(self, stop_time: float) -> None:
        """Stop time for the simulation.

        Args:
            stop_time (float): Stop time for the simulation.
        """
        self._simulation_config.stop_time = stop_time

    @property
    def step_size(self) -> float:
        """Step size of the simulation.

        Returns:
            float: Step size of the simulation.
        """
        return self._simulation_config.step_size

    @step_size.setter
    def step_size(self, step_size: float) -> None:
        """Step size of the simulation.

        Args:
            step_size (float): Step size of the simulation.
        """
        self._simulation_config.step_size = step_size

    @property
    def logging_step_size(self) -> float:
        """Logging step size of the simulation.

        Returns:
            float: Logging step size of the simulation.
        """
        return self._simulation_config.logging_step_size or self.step_size

    @logging_step_size.setter
    def logging_step_size(self, logging_step_size: float) -> None:
        """Logging step size of the simulation.

        Args:
            logging_step_size (float): Logging step size of the simulation.
        """
        self._simulation_config.logging_step_size = logging_step_size

    @property
    def models(self) -> dict[str, _Model]:
        """Models of the run. key -> name of the model; value -> _Model object

        Returns:
            dict[str, _Model]: Models of the run. key -> name of the model;
            value -> _Model object
        """
        return self._models.models

    def change_model_name(self, prev_model_name: str, new_model_name: str) -> None:
        """Change the name of a model.

        Args:
            prev_model_name (str): Name of the model to be changed.
            new_model_name (str): New model name.
        """
        self._models.change_model_name(prev_model_name, new_model_name)

    @property
    def start_values(self) -> Optional[StartValues]:
        """Start values of the simulation.

        Returns:
            Optional[StartValues]: Start values of the simulation.
        """
        return self._models.start_values

    @start_values.setter
    def start_values(self, start_values: Optional[StartValues]) -> None:
        """Start values of the simulation.

        Args:
            start_values (Optional[StartValues]): Start values of the simulation.
        """
        self._models.start_values = start_values

    def get_start_values_of_model(
        self, model_name: str
    ) -> Optional[dict[str, StartValue]]:
        """Get the start values of a model.

        Args:
            model_name (str): Name of the model.

        Returns:
            Optional[dict[str, StartValue]]: Start values of the model.
        """
        return self._models.get_start_values_of_model(model_name)

    def set_start_values_of_model(
        self, model_name: str, start_values: dict[str, StartValue]
    ) -> None:
        """Set the start values of a model.

        Args:
            model_name (str): Name of the model.
            start_values (dict[str, StartValue]): Start values for the model.
        """
        self._models.set_start_values_of_model(model_name, start_values)

    def remove_start_values_of_model(self, model_name: str) -> None:
        """Remove all start values of a model.

        Args:
            model_name (str): Name of the model.
        """
        self._models.remove_start_values_of_model(model_name)

    def get_start_value(
        self, model_name: str, parameter_name: str
    ) -> Optional[StartValue]:
        """Get a start value from a model.

        Args:
            model_name (str): Name of the model.
            parameter_name (str): Name of the parameter inside the model.

        Returns:
            Optional[StartValue]: Start value
        """
        return self._models.get_start_value(model_name, parameter_name)

    def set_start_value(
        self, model_name: str, parameter_name: str, value: StartValue
    ) -> None:
        """Set a start value for a parameter inside a model.

        Args:
            model_name (str): Name of the model.
            parameter_name (str): Name of the parameter.
            value (StartValue): Start value.
        """
        self._models.set_start_value(model_name, parameter_name, value)

    def remove_start_value(self, model_name: str, parameter_name: str) -> None:
        """Remove the start value of parameter inside a model.

        Args:
            model_name (str): Name of the model.
            parameter_name (str): Name of the parameter.
        """
        self._models.remove_start_value(model_name, parameter_name)

    @property
    def connections(self) -> Optional[ConnectionsConfig]:
        """Connection configuration for the simulation.

        Returns:
            Optional[ConnectionsConfig]: Connection configuration for the simulation.
        """
        return self._models.connections_config

    @connections.setter
    def connections(self, connections: ConnectionsConfig) -> None:
        """Connection configuration for the simulation.

        Args:
            connections (ConnectionsConfig): Connection configuration for the
                simulation.
        """
        self._models.connections_config = connections

    def get_connections_of_model(self, model_name: str) -> Optional[Connections]:
        """Get the connections of a model.

        Args:
            model_name (str): Name of the model.

        Returns:
            Optional[Connections]: Connections of the model.
        """
        return self._models.get_connections_of_model(model_name)

    def set_connections_of_model(
        self, model_name: str, connections: Connections
    ) -> None:
        """Set the connections of a model.

        Args:
            model_name (str): Name of the model.
            connections (Connections): Connections to be set.
        """
        self._models.set_connections_of_model(model_name, connections)

    def remove_connections_of_model(self, model_name: str) -> None:
        """Remove the connections of a model.

        Args:
            model_name (str): Name of the model.
        """
        self._models.remove_connections_of_model(model_name)

    def get_connection(self, model_name: str, input_name: str) -> Optional[_Connection]:
        """Get the connection of an input parameter.

        Args:
            model_name (str): Name of the model.
            input_name (str): Name of the input parameter.

        Returns:
            Optional[_Connection]: The connection of the input parameter.
        """
        return self._models.get_connection(model_name, input_name)

    def set_connection(self, model_name: str, connection: _Connection) -> None:
        """Set the connection of an input parameter.

        Args:
            model_name (str): Name of the model.
            connection (_Connection): Connection to be set.
        """
        self._models.set_connection(model_name, connection)

    def remove_connection(self, model_name: str, input_name: str) -> None:
        """Remove the connection of an input parameter.

        Args:
            model_name (str): Name of the model.
            input_name (str): Name of the input parameter.
        """
        self._models.remove_connection(model_name, input_name)

    @property
    def parameters_to_log(self) -> Optional[ParametersToLog]:
        """Parameters that are logged during the simulation.

        Returns:
            Optional[ParametersToLog]: Parameters that are logged during the simulation.
        """
        return self._models.parameters_to_log

    @parameters_to_log.setter
    def parameters_to_log(self, parameters_to_log: Optional[ParametersToLog]) -> None:
        """Parameters that are logged during the simulation.

        Args:
            parameters_to_log (Optional[ParametersToLog]): Parameters that are logged
                during the simulation.
        """
        self._models.parameters_to_log = parameters_to_log

    def get_parameters_to_log_of_model(self, model_name: str) -> Optional[list[str]]:
        """Get the parameters that are logged in the specified model.

        Args:
            model_name (str): Name of the model.

        Returns:
            Optional[list[str]]: Parameters that are logged in the specified model.
        """
        return self._models.get_parameters_to_log_of_model(model_name)

    def set_parameters_to_log_of_model(
        self, model_name: str, parameters_to_log: list[str]
    ) -> None:
        """Set the parameter that are logged in the specified model.

        Args:
            model_name (str): Name of the model.
            parameters_to_log (list[str]): Parameters that should be logged in the
                specified model.
        """
        self._models.set_parameters_to_log_of_model(model_name, parameters_to_log)

    def remove_parameters_to_log_of_model(self, model_name: str) -> None:
        """Remove the parameters that are logged in the specified model.

        Args:
            model_name (str): Name of the model.
        """
        self._models.remove_parameters_to_log_of_model(model_name)

    def append_parameter_to_log(self, model_name: str, parameter_name: str) -> None:
        """Append a parameter that should be logged in the specified model.

        Args:
            model_name (str): Name of the model.
            parameter_name (str): Name of the parameter.
        """
        self._models.append_parameter_to_log(model_name, parameter_name)

    def remove_parameter_to_log(self, model_name: str, parameter_name: str) -> None:
        """Remove a parameter to be logged in the specified model.

        Args:
            model_name (str): Name of the model.
            parameter_name (str): Name of the parameter.
        """
        self._models.remove_parameter_to_log(model_name, parameter_name)

    @property
    def time_series(self) -> pd.DataFrame:
        """Time series results of the simulation.

        Raises:
            AttributeError: No simulation was performed.

        Returns:
            pd.DataFrame: Time series results of the simulation.
        """
        if self._results is None:
            raise AttributeError("No simulation performed yet.")
        return self._results.time_series

    @property
    def units(self) -> Optional[Units]:
        """Units of the logged parameters.

        Raises:
            AttributeError: No simulation was performed.

        Returns:
            Optional[Units]: Units of the logged parameters.
        """
        if self._results is None:
            raise AttributeError("No simulation performed yet.")
        return self._results.units

    @classmethod
    def from_config(
        cls,
        run_name: str,
        config_path: Path,
        fmu_paths: Optional[FmuPaths] = None,
        model_instances: Optional[ModelInstances] = None,
    ) -> Self:
        """Initialize a run from a config file.

        Args:
            run_name (str): Name of the run.
            config_path (Path): Path to the config file.
            fmu_paths (Optional[FmuPaths], optional):
                Dictionary which defines which fmu should be simulated.
                key -> name of the fmu; value -> path to the fmu

                >>> fmu_paths = {
                ...    "<name of the fmu 1>": <Path to the fmu1>,
                ...    "<name of the fmu 2>": <Path to the fmu2>,
                ... }

                Note: The name of the fmus can be chosen arbitrarily, but each name
                in 'fmu_paths' and 'model_instances' must occur only once.
                Defaults to None.
            model_instances (Optional[ModelInstances], optional):
                Dictionary which defines which Python Models should be simulated.
                key -> name of the model; value -> Instance of th model. The class that
                defines the model must inherit from the abstract class SimulationEntity

                >>> model_instances = {
                ...    "<name of the model 1>": <Instance of the model1>
                ...    "<name of the model 2>": <Instance of the model2>
                ... }

                Note: The name of the models can be chosen arbitrarily, but each
                name in 'fmu_paths' and 'model_instances' must occur only once.
                Defaults to None.

        Returns:
            Self: Run instance.
        """
        with open(config_path, encoding="utf-8") as config_file:
            config: _ConfigDict = json.load(config_file)

        return cls(
            run_name=run_name,
            _run_meta=_RunMeta.from_config(config),
            _models=_Models.from_config(config, fmu_paths, model_instances),
            _simulation_config=_SimulationConfig.from_config(config),
        )

    @classmethod
    def from_hdf5(cls, run_name: str, hdf5_path: Path) -> Run:
        """Load a run from a hdf5 file.

        Args:
            run_name (str): Name of the run.
            hdf5_path (Path): Path to the hdf5 file.

        Returns:
            Run: Run instance.
        """
        return rg.RunGroup.from_hdf5(hdf5_path, run_name).to_run()

    def get_config(self) -> _ConfigDict:
        """Get the configuration for the run.

        Returns:
            _ConfigDict: Configuration for the run.
        """
        return _ConfigDict(
            run_meta=self._run_meta.to_dict(),
            models=self._models.to_dict(),
            simulation_config=self._simulation_config.to_dict(),
        )

    def simulate(self) -> None:
        """Simulate the run."""
        time_series, units = simulate(
            **self._simulation_config.get_simulation_args(),
            **self._models.get_simulation_args(),
            get_units=True,
        )
        self._results = _Results(time_series=time_series, units=units)

    def to_hdf5(self, hdf5_path: Path) -> None:
        """Store the run inside a hdf5 file.

        Args:
            hdf5_path (Path): Path to the hdf5 file.
        """
        rg.RunGroup.from_run(self).to_hdf5(hdf5_path)


class _Results(pydantic.BaseModel):
    time_series: pd.DataFrame
    units: Optional[Units]

    class Config:
        arbitrary_types_allowed = True


@pydantic.dataclasses.dataclass
class _RunMeta:
    description: str
    keywords: list[str]
    sofirpy_version: str
    python_version: str
    date: str

    CONFIG_KEY: ClassVar[ConfigKeyType] = "run_meta"

    @classmethod
    def from_config(cls, config: _ConfigDict) -> Self:
        return cls(
            **config[cls.CONFIG_KEY],
            sofirpy_version=sofirpy.__version__,
            python_version=sys.version,
            date=datetime.now().strftime("%d-%b-%Y %H:%M:%S"),
        )

    @pydantic.validator("keywords", pre=True)
    def convert_numpy_array(cls, keywords: Iterable[str]) -> list[str]:
        return list(keywords)

    def to_dict(self) -> _MetaConfigDict:
        meta_config = cast(
            _MetaConfigDict,
            {
                field_name: self.__getattribute__(field_name)
                for field_name in _MetaConfigDict.__annotations__.keys()
            },
        )
        return meta_config


@pydantic.dataclasses.dataclass
class _SimulationConfig:
    stop_time: float
    step_size: float
    logging_step_size: Optional[float] = None

    CONFIG_KEY: ClassVar[ConfigKeyType] = "simulation_config"

    @classmethod
    def from_config(cls, config: _ConfigDict) -> Self:
        return cls(**config[cls.CONFIG_KEY])

    def to_dict(self) -> _SimulationConfigDict:
        return cast(_SimulationConfigDict, asdict(self))

    def get_simulation_args(self) -> _SimulationConfigDict:
        return self.to_dict()


@dataclass
class _Models:
    fmus: dict[str, _Fmu]
    python_models: dict[str, _PythonModel]

    CONFIG_KEY: ClassVar[ConfigKeyType] = "models"

    @classmethod
    def from_config(
        cls,
        config: _ConfigDict,
        fmu_paths: Optional[FmuPaths] = None,
        model_instances: Optional[ModelInstances] = None,
    ) -> Self:
        model_config = cast(dict[str, _ModelConfigDict], config[cls.CONFIG_KEY])
        # TODO check if all names in fmu_paths and model_instances are in config
        fmu_paths = fmu_paths or {}
        fmus = {
            name: _Fmu(
                name=name,
                fmu_path=utils.convert_str_to_path(path, "fmu_path"),
                **model_config[name],
            )
            for name, path in fmu_paths.items()
        }
        model_instances = model_instances or {}
        python_models = {
            name: _PythonModel(
                name=name, model_instance=model_instance, **model_config[name]
            )
            for name, model_instance in model_instances.items()
        }
        return cls(fmus=fmus, python_models=python_models)

    @property
    def models(self) -> dict[str, _Model]:
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
    ) -> None:  # TODO maybe instead of doing this link model class in connections
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

    def to_dict(self) -> dict[str, _ModelConfigDict]:
        return {name: model.to_dict() for name, model in self.models.items()}

    def get_simulation_args(self) -> dict[str, Any]:
        return {
            "start_values": self.start_values,
            "connections_config": self.connections_config,
            "parameters_to_log": self.parameters_to_log,
            "fmu_paths": self.fmu_paths,
            "model_instances": self.model_instances,
        }


class _Model(pydantic.BaseModel):
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
        raise KeyError(f"model '{self.name}' has not input parameter '{input_name}'")

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

    def to_dict(self) -> _ModelConfigDict:
        model_config = cast(
            _ModelConfigDict,
            {
                field_name: self.__getattribute__(field_name)
                for field_name in _ModelConfigDict.__annotations__.keys()
                if self.__getattribute__(field_name) is not None
            },
        )
        return model_config


class _Fmu(_Model):
    fmu_path: Path


class _PythonModel(_Model):
    model_instance: SimulationEntity
