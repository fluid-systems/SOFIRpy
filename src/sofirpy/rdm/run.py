"""This module allows to create, interact with and store a simulation run."""

from __future__ import annotations

import enum
import inspect
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar, Optional, cast

import pandas as pd
import pydantic
from typing_extensions import NotRequired, Self, TypedDict

import sofirpy
import sofirpy.common as co
import sofirpy.rdm.hdf5.hdf5_to_run
import sofirpy.rdm.hdf5.run_to_hdf5
from sofirpy import utils
from sofirpy.simulation.simulation import simulate
from sofirpy.simulation.simulation_entity import SimulationEntity


class ConfigKeyType(enum.Enum):
    RUN_META = "run_meta"
    MODELS = "models"
    SIMULATION_CONFIG = "simulation_config"


class Config(pydantic.BaseModel):
    run_meta: _RunMetaConfig
    models: dict[str, _ModelsConfig]
    simulation_config: _SimulationConfig

    @classmethod
    def from_file(cls, file_path: Path) -> Config:
        return cls(**json.loads(file_path.read_text(encoding="utf-8")))


class _RunMetaConfig(pydantic.BaseModel):
    description: str = pydantic.Field(default="")
    keywords: list[str] = pydantic.Field(default_factory=list)


class _ModelsConfig(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")
    init_config: Optional[co.InitConfig] = None  # noqa: UP007
    connections: Optional[co.Connections] = None  # noqa: UP007
    parameters_to_log: Optional[list[str]] = None  # noqa: UP007


class _SimulationConfig(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")
    stop_time: float
    step_size: float
    logging_step_size: Optional[float] = None  # noqa: UP007


class ConfigDict(TypedDict):
    run_meta: MetaConfigDict
    models: dict[str, ModelConfigDict]
    simulation_config: SimulationConfigDict


class MetaConfigDict(TypedDict):
    description: str
    keywords: list[str]


class ModelConfigDict(TypedDict):
    init_config: NotRequired[co.InitConfig]
    connections: NotRequired[co.Connections]
    parameters_to_log: NotRequired[list[str]]


class SimulationConfigDict(TypedDict):
    stop_time: float
    step_size: float
    logging_step_size: NotRequired[float]


@dataclass
class Run:
    """Run object representing a simulation Run.

    A Run can be initiated from a config file or loaded from a hdf5 file. It provides
    several methods for updating the configuration of the run. A Run can be serialized
    and stored inside a hdf5 file.
    """

    run_name: str
    _run_meta: RunMeta
    _models: Models
    _simulation_config: SimulationConfig
    _results: Results | None = None

    def __repr__(self) -> str:
        return (
            f"Run: '{self.run_name}'\n"
            f"Description: '{self.description}'\n"
            f"Keywords: {self.keywords}"
        )

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
        utils.check_type(description, "description", str)
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
        utils.check_type(keywords, "keywords", list)
        for keyword in keywords:
            utils.check_type(keyword, "keyword", str)
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
        utils.check_type(keyword, "keyword", str)
        self._run_meta.keywords.append(keyword)

    @property
    def date(self) -> datetime:
        """Date and time run was created.

        Returns:
            datetime: Date and time run was created.
        """
        return datetime.strptime(self._run_meta.date, "%d-%b-%Y %H:%M:%S")

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
    def os(self) -> str:
        """Operating system the simulation was performed on.

        Returns:
            str: Operating system the simulation was performed on.
        """
        return self._run_meta.os

    @property
    def dependencies(self) -> dict[str, str]:
        """Dependencies installed in the Python environment when the run is created.

        Returns:
            dict[str, str]: key -> name of the package; value -> version
        """
        return self._run_meta.dependencies

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
        self._simulation_config.stop_time = float(stop_time)

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
        self._simulation_config.step_size = float(step_size)

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
        self._simulation_config.logging_step_size = float(logging_step_size)

    @property
    def models(self) -> dict[str, Model]:
        """Models of the run. key -> name of the model; value -> Model object

        Returns:
            dict[str, Model]: Models of the run. key -> name of the model;
            value -> Model object
        """
        return self._models.models

    def change_model_name(self, prev_model_name: str, new_model_name: str) -> None:
        """Change the name of a model.

        Args:
            prev_model_name (str): Name of the model to be changed.
            new_model_name (str): New model name.
        """
        self._models.change_model_name(prev_model_name, new_model_name)

    def get_fmu_path(self, fmu_name: str) -> Path:
        """Get the path of a fmu.

        Args:
            fmu_name (str): Name of the fmu.

        Returns:
            Path: Path of the fmu.
        """
        return self._models.fmus[fmu_name].fmu_path

    def move_fmu(self, fmu_name: str, target_directory: str | Path) -> None:
        """Move a fmu to a target directory.

        Args:
            fmu_name (str): Name of the fmu.
            target_directory (str | Path): Target directory.
        """
        target_directory = utils.convert_str_to_path(
            target_directory,
            "target_directory",
        )
        self._models.move_fmu(fmu_name, target_directory)

    def add_fmu(
        self,
        fmu_name: str,
        fmu_path: co.FilePath,
        connections: list[co.Connection] | None = None,
        init_config: co.InitConfig | None = None,
        parameters_to_log: list[str] | None = None,
    ) -> None:
        """Add a fmu.

        Args:
            fmu_name (str): Name of the fmu.
            fmu_path (co.FilePath): Path to the fmu.
            connections (list[_Connection] | None, optional): Connection config for the
                fmu. Defaults to None.
            init_config (co.InitConfig | None, optional): Initial configuration for the
                fmu. Defaults to None.
            parameters_to_log (list[str] | None, optional): Parameters of the fmu that
                should be logged . Defaults to None.
        """
        self._models.fmus[fmu_name] = Fmu(
            name=fmu_name,
            connections=connections,
            init_config=init_config,
            parameters_to_log=parameters_to_log,
            fmu_path=utils.convert_str_to_path(fmu_path, "fmu_path"),
        )

    def remove_fmu(self, fmu_name: str) -> None:
        """Remove a fmu.

        Args:
            fmu_name (str): Name of the fmu that should be removed.
        """
        self._models.remove_fmu(fmu_name)

    def get_model_class(self, model_name: str) -> type[SimulationEntity] | None:
        """Get the instance of a python model.

        Args:
            model_name (str): Name of the model.

        Returns:
            type[SimulationEntity] | None: Model instance.
        """
        return self._models.python_models[model_name].model_class

    def get_source_code_of_python_model(self, model_name: str) -> str:
        """Get the class source code of a python model.

        Args:
            model_name (str): Name of the python model.

        Returns:
            str: Source code of the class.
        """
        return self._models.get_source_code_of_python_model(model_name)

    def create_file_from_source_code(
        self,
        model_name: str,
        target_path: str | Path,
    ) -> None:
        """Create a python file from the source code of a python model.

        Args:
            model_name (str): Name of the python model.
            target_path (str | Path): Target path.
        """
        target_path = utils.convert_str_to_path(target_path, "target_path")
        self._models.create_file_from_source_code(model_name, target_path)

    def add_python_model(
        self,
        model_name: str,
        model_class: type[SimulationEntity],
        connections: list[co.Connection] | None = None,
        init_config: co.InitConfig | None = None,
        parameters_to_log: list[str] | None = None,
    ) -> None:
        """Add a python model.

        Args:
            model_name (str): Name of the python model.
            model_class (type[SimulationEntity]): Model class.
            connections (list[_Connection] | None, optional): Connection config for the
                python model. Defaults to None.
            init_config (StartValues | None, optional): Initial configuration for the
                python model. Defaults to None.
            parameters_to_log (list[str] | None, optional): Parameters of the python
                model that should be logged . Defaults to None.

        Raises:
            TypeError: 'model_class' is not subclass of SimulationEntity
        """
        if not issubclass(model_class, SimulationEntity):
            raise TypeError("'model_classes must be a subclass of 'SimulationEntity'")
        self._models.python_models[model_name] = PythonModel(
            name=model_name,
            connections=connections,
            init_config=init_config,
            parameters_to_log=parameters_to_log,
            model_class=model_class,
        )

    def remove_python_model(self, model_name: str) -> None:
        """Remove a python model.

        Args:
            model_name (str): Name of the python model.
        """
        self._models.remove_python_model(model_name)

    @property
    def init_configs(self) -> co.InitConfigs | None:
        """Initial configuration for models.

        Returns:
            co.InitConfigs | None: Initial configuration for models.
        """
        return self._models.init_configs

    @init_configs.setter
    def init_configs(self, init_configs: co.InitConfigs | None) -> None:
        """Initial configuration for models.

        Args:
            init_configs (co.InitConfigs | None): Initial configuration for models.
        """
        if init_configs is not None:
            utils.check_type(init_configs, "init_configs", dict)
        self._models.init_configs = init_configs

    def get_init_config_of_model(
        self,
        model_name: str,
    ) -> co.InitConfig | None:
        """Get the initial configuration of a model.

        Args:
            model_name (str): Name of the model.

        Returns:
            co.InitConfig | None: Initial configuration of the model.
        """
        return self._models.get_init_config_of_model(model_name)

    def set_init_config_of_model(
        self,
        model_name: str,
        init_config: co.InitConfig,
    ) -> None:
        """Set the initial configuration of a model.

        Args:
            model_name (str): Name of the model.
            init_config (co.InitConfig): Initial configuration for the model.
        """
        utils.check_type(init_config, "init_config", dict)
        self._models.set_init_config_of_model(model_name, init_config)

    def remove_init_config_of_model(self, model_name: str) -> None:
        """Remove all initial configurations of a model.

        Args:
            model_name (str): Name of the model.
        """
        self._models.remove_init_config_of_model(model_name)

    @property
    def connections(self) -> co.ConnectionsConfig | None:
        """Connection configuration for the simulation.

        Returns:
            ConnectionsConfig | None: Connection configuration for the simulation.
        """
        return self._models.connections_config

    @connections.setter
    def connections(self, connections: co.ConnectionsConfig) -> None:
        """Connection configuration for the simulation.

        Args:
            connections (ConnectionsConfig): Connection configuration for the
                simulation.
        """
        utils.check_type(connections, "connections", dict)
        self._models.connections_config = connections

    def get_connections_of_model(self, model_name: str) -> co.Connections | None:
        """Get the connections of a model.

        Args:
            model_name (str): Name of the model.

        Returns:
            co.Connections | None: Connections of the model.
        """
        return self._models.get_connections_of_model(model_name)

    def set_connections_of_model(
        self,
        model_name: str,
        connections: co.Connections,
    ) -> None:
        """Set the connections of a model.

        Args:
            model_name (str): Name of the model.
            connections (Connections): Connections to be set.
        """
        utils.check_type(connections, "connections", list)
        self._models.set_connections_of_model(model_name, connections)

    def remove_connections_of_model(self, model_name: str) -> None:
        """Remove the connections of a model.

        Args:
            model_name (str): Name of the model.
        """
        self._models.remove_connections_of_model(model_name)

    def get_connection(self, model_name: str, input_name: str) -> co.Connection | None:
        """Get the connection of an input parameter.

        Args:
            model_name (str): Name of the model.
            input_name (str): Name of the input parameter.

        Returns:
            _Connection | None: The connection of the input parameter.
        """
        return self._models.get_connection(model_name, input_name)

    def set_connection(
        self,
        model_name: str,
        parameter_name: str,
        connect_to_system: str,
        connect_to_external_parameter: str,
    ) -> None:
        """Set the connection of an input parameter.

        Args:
            model_name (str): Name of the model.
            connection (_Connection): Connection to be set.
        """
        utils.check_type(parameter_name, "parameter_name", str)
        utils.check_type(connect_to_system, "connect_to_system", str)
        utils.check_type(
            connect_to_external_parameter,
            "connect_to_external_parameter",
            str,
        )
        self._models.set_connection(
            model_name,
            co.Connection(
                parameter_name=parameter_name,
                connect_to_system=connect_to_system,
                connect_to_external_parameter=connect_to_external_parameter,
            ),
        )

    def remove_connection(self, model_name: str, input_name: str) -> None:
        """Remove the connection of an input parameter.

        Args:
            model_name (str): Name of the model.
            input_name (str): Name of the input parameter.
        """
        self._models.remove_connection(model_name, input_name)

    @property
    def parameters_to_log(self) -> co.ParametersToLog | None:
        """Parameters that are logged during the simulation.

        Returns:
            ParametersToLog | None: Parameters that are logged during the simulation.
        """
        return self._models.parameters_to_log

    @parameters_to_log.setter
    def parameters_to_log(self, parameters_to_log: co.ParametersToLog | None) -> None:
        """Parameters that are logged during the simulation.

        Args:
            parameters_to_log (ParametersToLog | None): Parameters that are logged
                during the simulation.
        """
        if parameters_to_log is not None:
            utils.check_type(parameters_to_log, "parameters_to_log", dict)
        self._models.parameters_to_log = parameters_to_log

    def get_parameters_to_log_of_model(self, model_name: str) -> list[str] | None:
        """Get the parameters that are logged in the specified model.

        Args:
            model_name (str): Name of the model.

        Returns:
            list[str] | None: Parameters that are logged in the specified model.
        """
        return self._models.get_parameters_to_log_of_model(model_name)

    def set_parameters_to_log_of_model(
        self,
        model_name: str,
        parameters_to_log: list[str],
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
    def units(self) -> co.Units | None:
        """Units of the logged parameters.

        Raises:
            AttributeError: No simulation was performed.

        Returns:
            Units | None: Units of the logged parameters.
        """
        if self._results is None:
            raise AttributeError("No simulation performed yet.")
        return self._results.units

    @classmethod
    def from_config(
        cls,
        run_name: str,
        stop_time: float,
        step_size: float,
        keywords: list[str] | None = None,
        description: str | None = None,
        fmu_paths: co.FmuPaths | None = None,
        model_classes: co.ModelClasses | None = None,
        connections_config: co.ConnectionsConfig | None = None,
        init_configs: co.InitConfigs | None = None,
        parameters_to_log: co.ParametersToLog | None = None,
        logging_step_size: float | None = None,
    ) -> Self:
        """Initialize a run from a configuration.

        Args:
            run_name (str): Name of the run.
            stop_time (float): stop time for the simulation
            step_size (float): step size for the simulation
            keywords (list[str] | None, optional): Keywords describing the simulation.
                Defaults to None.
            description (str, optional): Description of the run. Defaults to None.
            fmu_paths (FmuPaths | None, optional):
                Dictionary which defines which fmu should be simulated.
                key -> name of the fmu; value -> path to the fmu

                >>> fmu_paths = {
                ...    "<name of the fmu 1>": "path/to/fmu1",
                ...    "<name of the fmu 2>": "path/to/fmu2",
                ... }

                Note: The name of the fmus can be chosen arbitrarily, but each name
                in 'fmu_paths' and 'model_classes' must occur only once.
                Defaults to None.
            model_classes (ModelClasses | None, optional):
                Dictionary which defines which Python Models should be simulated.
                key -> name of the model; value -> Instance of th model. The class that
                defines the model must inherit from the abstract class SimulationEntity

                >>> model_classes = {
                ...    "<name of the model 1>": <Instance of the model1>
                ...    "<name of the model 2>": <Instance of the model2>
                ... }

                Note: The name of the models can be chosen arbitrarily, but each
                name in 'fmu_paths' and 'model_classes' must occur only once.
                Defaults to None..
            connections_config (ConnectionsConfig | None, optional):
                Dictionary which defines how the inputs and outputs of the systems
                (fmu or python model) are connected.
                key -> name of the system; value -> list of connections

                >>> connections_config = {
                ...     "<name of the system 1>": [
                ...         {
                ...             "parameter_name":       "<name of the input"
                ...                                     "parameter of the system>",
                ...             "connect_to_system":    "<name of the system the input"
                ...                                     "parameter should be connected to>",
                ...             "connect_to_external_parameter":    "<name of the output"
                ...                                                 "parameter in the"
                ...                                                 "connected system the"
                ...                                                 "input parameter should"
                ...                                                 "be connected to>"
                ...         },
                ...         {
                ...             "parameter_name":       "<name of the input"
                ...                                     "parameter of the system>",
                ...             "connect_to_system":    "<name of the system the input"
                ...                                     "parameter should be connected to>",
                ...             "connect_to_external_parameter":    "<name of the output"
                ...                                                 "parameter in the"
                ...                                                 "connected system the"
                ...                                                 "input parameter should"
                ...                                                 "be connected to>"
                ...         }
                ...     ],
                ...     "<name of the system 2>": [
                ...         {
                ...             "parameter_name":       "<name of the input"
                ...                                     "parameter of the system>",
                ...             "connect_to_system":    "<name of the system the input"
                ...                                     "parameter should be connected to>",
                ...             "connect_to_external_parameter":    "<name of the output"
                ...                                                 "parameter in the"
                ...                                                 "connected system the"
                ...                                                 "input parameter should"
                ...                                                 "be connected to>"
                ...         }
                ...     ]
                ... }

                Defaults to None.
            init_configs (co.InitConfigs | None, optional): Dictionary which defines
                initial configurations for the systems. Fmus can only have the key
                'start_values' for specifying the start values.
                key -> name of the system;
                value -> dictionary (key -> config name; value -> config value)

                >>> init_configs = {
                ...     "<name of system 1>":
                ...     {
                ...         "<name of config 1>": <config value 1>,
                ...         "<name of config 2>", <config value 2>
                ...     },
                ...     "<name of fmu 1>":
                ...     {
                ...         "start_values": {
                ...             "<name of parameter 1>": (<start value>, unit e.g 'kg.m2'),
                ...             "<name of parameter 2>": <start value>
                ...     }
                ... }

                Defaults to None.
            parameters_to_log (ParametersToLog | None, optional):
                Dictionary that defines which parameters should be logged.
                key -> name of the system; value -> list of parameters names to be logged

                >>> parameters_to_log = {
                ...     "<name of system 1>":
                ...     [
                ...         "<name of parameter 1>",
                ...         "<name of parameter 2>",
                ...     ],
                ...     "<name of system 2>":
                ...     [
                ...         "<name of parameter 1>",
                ...         "<name of parameter 2>",
                ...     ]
                ... }

                Defaults to None.
            logging_step_size (float | None, optional): step size
                for logging. It must be a multiple of the chosen simulation step size.
                Example:
                If the simulation step size is set to 1e-3 and logging step size
                is set to 2e-3, every second time step is logged. Defaults to None.

        Returns:
            Run: Run instance.
        """
        return cls(
            run_name=run_name,
            _run_meta=RunMeta.from_config(
                description=description or "",
                keywords=keywords or [],
            ),
            _models=Models.from_config(
                fmu_paths=fmu_paths or {},
                model_classes=model_classes or {},
                connections_config=connections_config or {},
                init_configs=init_configs or {},
                parameters_to_log=parameters_to_log or {},
            ),
            _simulation_config=SimulationConfig(
                stop_time=stop_time,
                step_size=step_size,
                logging_step_size=logging_step_size,
            ),
        )

    @classmethod
    def from_config_file(
        cls,
        run_name: str,
        config_file_path: str | Path,
        fmu_paths: co.FmuPaths | None = None,
        model_classes: co.ModelClasses | None = None,
    ) -> Self:
        """Initialize a run from a config file.

        Args:
            run_name (str): Name of the run.
            config_file_path (co.FilePath): Path to the config file.
            fmu_paths (FmuPaths | None, optional):
                Dictionary which defines which fmu should be simulated.
                key -> name of the fmu; value -> path to the fmu

                >>> fmu_paths = {
                ...    "<name of the fmu 1>": "path/to/fmu1",
                ...    "<name of the fmu 2>": "path/to/fmu2",
                ... }

                Note: The name of the fmus can be chosen arbitrarily, but each name
                in 'fmu_paths' and 'model_classes' must occur only once.
                Defaults to None.
            model_classes (ModelClasses | None, optional):
                Dictionary which defines which Python Models should be simulated.
                key -> name of the model; value -> Instance of th model. The class that
                defines the model must inherit from the abstract class SimulationEntity

                >>> model_classes = {
                ...    "<name of the model 1>": <Instance of the model1>
                ...    "<name of the model 2>": <Instance of the model2>
                ... }

                Note: The name of the models can be chosen arbitrarily, but each
                name in 'fmu_paths' and 'model_classes' must occur only once.
                Defaults to None.

        Returns:
            Run: Run instance.
        """
        config_file_path = utils.convert_str_to_path(
            config_file_path,
            "config_file_path",
        )
        config = Config.from_file(config_file_path)

        return cls(
            run_name=run_name,
            _run_meta=RunMeta.from_config_file(config),
            _models=Models.from_config_file(
                config=config,
                fmu_paths=fmu_paths or {},
                model_classes=model_classes or {},
            ),
            _simulation_config=SimulationConfig.from_config_file(config),
        )

    @classmethod
    def from_hdf5(cls, run_name: str, hdf5_path: co.FilePath) -> Run:
        """Load a run from a hdf5 file.

        Args:
            run_name (str): Name of the run.
            hdf5_path (co.FilePath): Path to the hdf5 file.

        Returns:
            Run: Run instance.
        """
        hdf5_path = utils.convert_str_to_path(hdf5_path, "hdf5_path")
        return sofirpy.rdm.hdf5.hdf5_to_run.create_run_from_hdf5(hdf5_path, run_name)

    def get_config(self) -> ConfigDict:
        """Get the configuration for the run.

        Returns:
            ConfigDict: Configuration for the run.
        """
        return ConfigDict(
            run_meta=self._run_meta.to_config(),
            models=self._models.to_config(),
            simulation_config=self._simulation_config.to_config(),
        )

    def simulate(self) -> None:
        """Simulate the run."""
        time_series, units = simulate(
            **self._simulation_config.get_simulation_args(),
            **self._models.get_simulation_args(),
            get_units=True,
        )
        self._results = Results(time_series=time_series, units=units)
        self._update_run()

    def _update_run(self) -> None:
        """Updates the meta data of a run."""
        self._run_meta.update()

    def to_hdf5(self, hdf5_path: co.FilePath) -> None:
        """Store the run inside a hdf5 file.

        Args:
            hdf5_path (co.FilePath): Path to the hdf5 file.
        """
        hdf5_path = utils.convert_str_to_path(hdf5_path, "hdf5_path")
        sofirpy.rdm.hdf5.run_to_hdf5.RunToHDF5.store(run=self, hdf5_path=hdf5_path)


@dataclass
class Results:
    time_series: pd.DataFrame
    units: co.Units | None


@pydantic.dataclasses.dataclass
class RunMeta:
    description: str
    keywords: list[str]
    sofirpy_version: str
    python_version: str
    date: str
    os: str
    dependencies: dict[str, str]

    CONFIG_KEY: ClassVar[ConfigKeyType] = ConfigKeyType.RUN_META

    @classmethod
    def from_config(cls, description: str, keywords: list[str]) -> Self:
        utils.check_type(description, "description", str)
        utils.check_type(keywords, "keywords", list)
        return cls(
            description=description,
            keywords=keywords,
            sofirpy_version=sofirpy.__version__,
            python_version=sys.version,
            date=datetime.now().strftime("%d-%b-%Y %H:%M:%S"),
            os=sys.platform,
            dependencies=utils.get_dependencies_of_current_env(),
        )

    @classmethod
    def from_config_file(cls, config: Config) -> Self:
        return cls.from_config(**dict(config.run_meta))

    def update(self) -> None:
        self.sofirpy_version = sofirpy.__version__
        self.python_version = sys.version
        self.date = datetime.now().strftime("%d-%b-%Y %H:%M:%S")
        self.os = sys.platform
        self.dependencies = utils.get_dependencies_of_current_env()

    def to_config(self) -> MetaConfigDict:
        meta_config = cast(
            MetaConfigDict,
            {
                field_name: getattr(self, field_name)
                for field_name in MetaConfigDict.__annotations__
            },
        )
        return meta_config

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@pydantic.dataclasses.dataclass
class SimulationConfig:
    stop_time: float
    step_size: float
    logging_step_size: Optional[float] = None  # noqa: UP007

    CONFIG_KEY: ClassVar[ConfigKeyType] = ConfigKeyType.SIMULATION_CONFIG

    @classmethod
    def from_config_file(cls, config: Config) -> Self:
        return cls(**dict(config.simulation_config))

    def to_dict(self) -> SimulationConfigDict:
        return cast(SimulationConfigDict, asdict(self))

    def to_config(self) -> SimulationConfigDict:
        return self.to_dict()

    def get_simulation_args(self) -> SimulationConfigDict:
        return self.to_dict()


@dataclass
class Models:
    fmus: dict[str, Fmu]
    python_models: dict[str, PythonModel]
    can_simulate_fmu: bool = True
    can_simulate_python_model: bool = True

    CONFIG_KEY: ClassVar[ConfigKeyType] = ConfigKeyType.MODELS

    @classmethod
    def from_config(
        cls,
        fmu_paths: co.FmuPaths,
        model_classes: co.ModelClasses,
        connections_config: co.ConnectionsConfig,
        init_configs: co.InitConfigs,
        parameters_to_log: co.ParametersToLog,
    ) -> Self:
        fmus = {
            name: Fmu(
                name=name,
                fmu_path=utils.convert_str_to_path(path, "fmu_path"),
                connections=connections_config.get(name),
                init_config=init_configs.get(name),
                parameters_to_log=parameters_to_log.get(name),
            )
            for name, path in fmu_paths.items()
        }
        python_models = {
            name: PythonModel(
                name=name,
                model_class=model_class,
                connections=connections_config.get(name),
                init_config=init_configs.get(name),
                parameters_to_log=parameters_to_log.get(name),
            )
            for name, model_class in model_classes.items()
        }
        return cls(fmus=fmus, python_models=python_models)

    @classmethod
    def from_config_file(
        cls,
        config: Config,
        fmu_paths: co.FmuPaths,
        model_classes: co.ModelClasses,
    ) -> Self:
        model_config = config.models
        fmus = {
            name: Fmu(
                name=name,
                fmu_path=utils.convert_str_to_path(path, "fmu_path"),
                **dict(model_config[name]),
            )
            for name, path in fmu_paths.items()
        }
        python_models = {
            name: PythonModel(
                name=name, model_class=model_class, **dict(model_config[name])
            )
            for name, model_class in model_classes.items()
        }
        return cls(fmus=fmus, python_models=python_models)

    @property
    def models(self) -> dict[str, Model]:
        return {**self.fmus, **self.python_models}

    def change_model_name(self, prev_name: str, new_name: str) -> None:
        if prev_name not in self.models:
            raise KeyError(f"name {prev_name} not in models.")
        if prev_name in self.fmus:
            self.fmus[new_name] = self.fmus.pop(prev_name)
        if prev_name in self.python_models:
            self.python_models[new_name] = self.python_models.pop(prev_name)
        self.models[new_name].name = new_name
        self.update_connections(prev_name, new_name)

    def update_connections(self, prev_name: str, new_name: str) -> None:
        for model in self.models.values():
            model.update_connections(prev_name, new_name)

    def remove_fmu(self, fmu_name: str) -> None:
        del self.fmus[fmu_name]
        self.remove_connections_to_external_model(fmu_name)

    def remove_python_model(self, model_name: str) -> None:
        del self.python_models[model_name]
        self.remove_connections_to_external_model(model_name)

    def remove_connections_to_external_model(self, model_name: str) -> None:
        for model in self.models.values():
            model.remove_connections_to_model(model_name)

    @property
    def init_configs(self) -> co.InitConfigs | None:
        init_configs = {
            name: model.init_config
            for name, model in self.models.items()
            if model.init_config
        }
        return init_configs or None

    @init_configs.setter
    def init_configs(self, init_configs: co.InitConfigs | None) -> None:
        if init_configs is None:
            init_configs = {}
        for model_name, model in self.models.items():
            model.init_config = init_configs.get(model_name)

    def get_init_config_of_model(
        self,
        model_name: str,
    ) -> dict[str, co.StartValue] | None:
        return self.models[model_name].init_config

    def set_init_config_of_model(
        self,
        model_name: str,
        init_config: co.InitConfig,
    ) -> None:
        self.models[model_name].init_config = init_config

    def remove_init_config_of_model(self, model_name: str) -> None:
        self.models[model_name].init_config = None

    @property
    def connections_config(self) -> co.ConnectionsConfig | None:
        connections_config = {
            name: model.connections
            for name, model in self.models.items()
            if model.connections
        }
        return connections_config or None

    @connections_config.setter
    def connections_config(
        self,
        connections_config: co.ConnectionsConfig | None,
    ) -> None:
        if connections_config is None:
            connections_config = {}
        for model_name, model in self.models.items():
            model.connections = connections_config.get(model_name)

    def get_connections_of_model(self, model_name: str) -> co.Connections | None:
        return self.models[model_name].connections

    def set_connections_of_model(
        self,
        model_name: str,
        connections: co.Connections,
    ) -> None:
        self.models[model_name].connections = connections

    def remove_connections_of_model(self, model_name: str) -> None:
        self.models[model_name].connections = None

    def get_connection(self, model_name: str, input_name: str) -> co.Connection | None:
        return self.models[model_name].get_connection(input_name)

    def set_connection(self, model_name: str, connection: co.Connection) -> None:
        self.models[model_name].set_connection(connection)

    def remove_connection(self, model_name: str, input_name: str) -> None:
        self.models[model_name].remove_connection(input_name)

    @property
    def parameters_to_log(self) -> co.ParametersToLog | None:
        parameters_to_log = {
            name: model.parameters_to_log
            for name, model in self.models.items()
            if model.parameters_to_log
        }
        return parameters_to_log or None

    @parameters_to_log.setter
    def parameters_to_log(self, parameter_to_log: co.ParametersToLog | None) -> None:
        if parameter_to_log is None:
            parameter_to_log = {}
        for model_name, model in self.models.items():
            model.parameters_to_log = parameter_to_log.get(model_name)

    def get_parameters_to_log_of_model(self, model_name: str) -> list[str] | None:
        return self.models[model_name].parameters_to_log

    def set_parameters_to_log_of_model(
        self,
        model_name: str,
        parameters_to_log: list[str],
    ) -> None:
        self.models[model_name].parameters_to_log = parameters_to_log

    def remove_parameters_to_log_of_model(self, model_name: str) -> None:
        self.models[model_name].parameters_to_log = None

    def append_parameter_to_log(self, model_name: str, parameter_name: str) -> None:
        self.models[model_name].append_parameter_to_log(parameter_name)

    def remove_parameter_to_log(self, model_name: str, parameter_name: str) -> None:
        self.models[model_name].remove_parameter_to_log(parameter_name)

    @property
    def fmu_paths(self) -> dict[str, Path]:
        return {name: fmu.fmu_path for name, fmu in self.fmus.items()}

    @property
    def model_classes(self) -> co.ModelClasses:
        return {
            name: python_model.model_class
            for name, python_model in self.python_models.items()
            if python_model.model_class is not None
        }

    def move_fmu(self, fmu_name: str, target_directory: Path) -> None:
        self.fmus[fmu_name].move_fmu(target_directory)

    def get_source_code_of_python_model(self, model_name: str) -> str:
        return self.python_models[model_name].get_source_code()

    def create_file_from_source_code(self, model_name: str, target_path: Path) -> None:
        self.python_models[model_name].create_file_from_source_code(target_path)

    def to_config(self) -> dict[str, ModelConfigDict]:
        return self.to_dict()

    def to_dict(self) -> dict[str, ModelConfigDict]:
        return {name: model.to_dict() for name, model in self.models.items()}

    def get_simulation_args(self) -> dict[str, Any]:
        return {
            "init_configs": self.init_configs,
            "connections_config": self.connections_config,
            "parameters_to_log": self.parameters_to_log,
            "fmu_paths": self.fmu_paths,
            "model_classes": self.model_classes,
        }


@dataclass
class Model:
    name: str
    connections: co.Connections | None
    init_config: dict[str, Any] | None
    parameters_to_log: list[str] | None

    class Config:
        arbitrary_types_allowed = True

    def get_connection(self, input_name: str) -> co.Connection | None:
        if self.connections is None:
            return None
        for connection in self.connections:
            if connection[co.ConnectionKeys.INPUT_PARAMETER.value] == input_name:
                return connection
        raise KeyError(f"model '{self.name}' has not input parameter '{input_name}'")

    def set_connection(self, connection: co.Connection) -> None:
        if self.connections is None:
            self.connections = []
        self.connections.append(connection)

    def remove_connection(self, input_name: str) -> None:
        if self.connections is None:
            return
        self.connections = [
            connection
            for connection in self.connections
            if connection[co.ConnectionKeys.INPUT_PARAMETER.value] != input_name
        ]

    def remove_connections_to_model(self, model_name: str) -> None:
        if self.connections is None:
            return
        self.connections = [
            connection
            for connection in self.connections
            if connection[co.ConnectionKeys.CONNECTED_SYSTEM.value] != model_name
        ]

    def update_connections(self, prev_name: str, new_name: str) -> None:
        if self.connections is None:
            return
        for connection in self.connections:
            if connection[co.ConnectionKeys.CONNECTED_SYSTEM.value] == prev_name:
                connection[co.ConnectionKeys.CONNECTED_SYSTEM.value] = new_name

    def append_parameter_to_log(self, parameter_name: str) -> None:
        if self.parameters_to_log is None:
            self.parameters_to_log = []
        self.parameters_to_log.append(parameter_name)

    def remove_parameter_to_log(self, parameter_name: str) -> None:
        if self.parameters_to_log is None:
            return
        self.parameters_to_log.remove(parameter_name)

    def to_dict(self) -> ModelConfigDict:
        model_config = cast(
            ModelConfigDict,
            {
                field_name: self.__getattribute__(field_name)
                for field_name in ModelConfigDict.__annotations__
                if self.__getattribute__(field_name) is not None
            },
        )
        return model_config


@dataclass
class Fmu(Model):
    fmu_path: Path

    def move_fmu(self, target_directory: Path) -> None:
        source_path = self.fmu_path
        target_path = target_directory / source_path.name
        utils.move_file(source_path, target_path)
        self.fmu_path = target_path


@dataclass
class PythonModel(Model):
    code: str | None = None
    model_class: type[SimulationEntity] | None = None

    def get_source_code(self) -> str:
        return self.read_code() if self.code is None else self.code

    def read_code(self) -> str:
        if self.model_class is None:
            raise ValueError(
                f"source code for model_class '{self.name}' is not available.",
            )
        return inspect.getsource(self.model_class)

    def create_file_from_source_code(self, target_path: Path) -> None:
        if not target_path.suffix.lower() == ".py":
            raise ValueError(
                f"Suffix of target path was {target_path.suffix}; expected 'py'",
            )
        if not target_path.exists():
            target_path.touch()
        if not target_path.is_file():
            raise FileNotFoundError(f"'{target_path!s}' is not a file.")
        target_path.write_text(self.get_source_code(), encoding="utf-8")
