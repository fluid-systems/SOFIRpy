"""This module allows to co-simulate multiple fmus and models written in python."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional, TypedDict, Union

import numpy as np
import numpy.typing as npt
import pandas as pd
from tqdm import tqdm

from sofirpy import utils
from sofirpy.simulation.fmu import Fmu
from sofirpy.simulation.simulation_entity import SimulationEntity, ParameterValue


@dataclass(frozen=True)
class System:
    """System object representing a simulation entity.

    Args:
            simulation_entity (SimulationEntity): fmu or python model
            name (str): name of the system
    """

    simulation_entity: SimulationEntity
    name: str


@dataclass(frozen=True)
class SystemParameter:
    """SystemParameter object representing a parameter in a system.

    Args:
            system (System): System object
            name (str): name of the parameter
    """

    system: System
    name: str
    in_input: bool = False


@dataclass(frozen=True)
class Connection:
    """Representing a connection between two systems.

    Args:
        input_point (SystemParameter): SystemParameter object that
            represents an input of a system
        output_point (SystemParameter): SystemParameter object that
            represents an output of a system
    """

    input_point: SystemParameter
    output_point: SystemParameter


class Simulation:
    """Object that performs the simulation."""

    def __init__(
        self,
        systems: dict[str, System],
        connections: list[Connection],
        parameters_to_log: Optional[list[SystemParameter]] = None,
    ) -> None:
        """Initialize Simulation object.

        Args:
            systems (list[System]): list of systems which are to be simulated
            connections (list[Connection]): list of connections between the
                 systems
            parameters_to_log (list[SystemParameter], optional): List of
                Parameters that should be logged. Defaults to None.
        """
        self.systems = systems
        self.connections = connections
        if parameters_to_log is None:
            parameters_to_log = []
        self.parameters_to_log = parameters_to_log

    def simulate(
        self,
        stop_time: float,
        step_size: float,
        logging_step_size: float,
        start_time: float = 0.0,
    ) -> pd.DataFrame:
        """Simulate the systems.

        The following steps are performed.
        1. start values are set
        2. start values are logged
        3. simulation loop starts

        Args:
            stop_time (float): stop time for the simulation
            step_size (float): step size for the simulation
            logging_step_size(float): logging step size for the simulation
            start_time (float, optional): start time of the simulation.
                Defaults to 0.0.

        Returns:
            pd.DataFrame: result DataFrame with times series of logged
            parameters
        """
        time_series = np.arange(start_time, stop_time + step_size, step_size)
        if time_series[-1] > stop_time:
            time_series = time_series[:-1]

        number_log_steps = int(stop_time / logging_step_size) + 1

        logging_multiple = round(logging_step_size / step_size)
        self.results = np.zeros((number_log_steps, len(self.parameters_to_log) + 1))

        print("Starting Simulation...")

        self.log_values(time=0, log_step=0)
        log_step = 1
        for time_step, time in enumerate(tqdm(time_series[:-1])):
            self.do_step(time)
            self.set_systems_inputs()
            if ((time_step + 1) % logging_multiple) == 0:
                self.log_values(time_series[time_step + 1], log_step)
                log_step += 1

        self.conclude_simulation()

        return self.convert_to_data_frame(self.results)

    def set_systems_inputs(self) -> None:
        """Set inputs for all systems."""
        for connection in self.connections:
            input_system = connection.input_point.system
            input_name = connection.input_point.name
            output_system = connection.output_point.system
            output_name = connection.output_point.name
            input_value = output_system.simulation_entity.get_parameter_value(
                output_name
            )
            input_system.simulation_entity.set_parameter(input_name, input_value)

    def do_step(self, time: float) -> None:
        """Perform a calculation in all systems.

        Args:
            time (float): current simulation time
            step_size (float): step size of the simulation
        """
        for system in self.systems.values():
            system.simulation_entity.do_step(time)

    def log_values(self, time: float, log_step: int) -> None:
        """Log parameter values that are set to be logged.

        Args:
            time (float): current simulation time
            log_step (int): current time step
        """
        new_value_row = [time]

        for parameter in self.parameters_to_log:
            system = parameter.system
            parameter_name = parameter.name
            value = system.simulation_entity.get_parameter_value(parameter_name)
            new_value_row += [value]

        self.results[log_step] = new_value_row

    def conclude_simulation(self) -> None:
        """Conclude the simulation for all simulation entities."""
        for system in self.systems.values():
            system.simulation_entity.conclude_simulation()

    def convert_to_data_frame(self, results: npt.NDArray[np.float64]) -> pd.DataFrame:
        """Covert result numpy array to DataFrame.

        Args:
            results (npt.NDArray[npt.float64]): Results of the simulation.

        Returns:
            pd.DataFrame: Results as DataFrame. Columns are named as follows:
            '<system_name>.<parameter_name>'.
        """
        columns = ["time"] + [
            f"{parameter.system.name}.{parameter.name}"
            for parameter in self.parameters_to_log
        ]

        return pd.DataFrame(results, columns=columns)

    def get_units(self) -> Units:
        """Get a dictionary with units of all logged parameters.

        Returns:
            Units: keys: parameter name, values: unit. If the unit can
            not be obtained it is set to None.
        """
        units = {}
        for parameter in self.parameters_to_log:
            system = parameter.system
            parameter_name = parameter.name
            try:
                unit = system.simulation_entity.get_unit(parameter_name)
            except AttributeError:
                unit = None
            units[f"{system.name}.{parameter_name}"] = unit

        return units


ConnectionInfo = dict[str, str]

ConnectionInfos = list[ConnectionInfo]


class SystemInfo(TypedDict, total=False):
    """TypedDict for fmu_info and model_info."""

    name: str
    path: Union[str, Path]
    connections: ConnectionInfos


SystemInfos = list[SystemInfo]

Units = dict[str, Optional[str]]

StartValues = dict[str, dict[str, ParameterValue]]


def simulate(
    stop_time: Union[float, int],
    step_size: Union[float, int],
    fmu_infos: Optional[SystemInfos] = None,
    model_infos: Optional[SystemInfos] = None,
    model_classes: Optional[dict[str, SimulationEntity]] = None,
    start_values: Optional[StartValues] = None,
    parameters_to_log: Optional[dict[str, list[str]]] = None,
    logging_step_size: Optional[Union[float, int]] = None,
    get_units: bool = False,
) -> Union[pd.DataFrame, tuple[pd.DataFrame, Units]]:
    """Simulate fmus and models written in python.

    Any number of python models and fmus can be simulated, but at least one
    python model or fmu has to be simulated.

    Args:
        stop_time (Union[float,int]): stop time for the simulation
        step_size (Union[float, int]): step size for the simulation
        fmu_infos (Optional[SystemInfos], optional):
            Defines which fmus should be simulated and how they are connected
            to other systems. It needs to have the following format:

            >>> fmu_infos = [
            ... {"name": "<name of the fmu>",
            ...  "path": "<path to the fmu>",
            ...  "connections":
            ...     [
            ...     {
            ...         "parameter_name":       "<name of the input"
            ...                                 "parameter of the fmu>",
            ...         "connect_to_system":    "<name of the system the input"
            ...                                 "parameter should be connected to>",
            ...         "connect_to_external_parameter":    "<name of the output"
            ...                                             "parameter in the"
            ...                                             "connected system the"
            ...                                             "input parameter should"
            ...                                             "be connected to>"
            ...         },
            ...         {
            ...         "parameter_name":       "<name of the input"
            ...                                 "parameter of the fmu>",
            ...         "connect_to_system":    "<name of the system the input"
            ...                                  "parameter should be connected to>",
            ...         "connect_to_external_parameter":    "<name of the output"
            ...                                             "parameter in the"
            ...                                             "connected system the"
            ...                                             "input parameter should"
            ...                                             "be connected to>"
            ...         }
            ...     ]
            ...     },
            ... {"name": "<name of the fmu>",
            ...  "path": "<path to the fmu>",
            ...  "connections":
            ...     [
            ...     {
            ...         "parameter_name":       "<name of the input"
            ...                                 "parameter of the fmu>",
            ...         "connect_to_system":    "<name of the system the input"
            ...                                  "parameter should be connected to>",
            ...         "connect_to_external_parameter":    "<name of the output"
            ...                                             "parameter in the"
            ...                                             "connected system the"
            ...                                             "input parameter should"
            ...                                             "be connected to>"
            ...        }
            ... }
            ... ]

            Note: The name of the fmus can be chosen arbitrarily, but each name
            in 'fmu_infos' and 'model_infos' must occur only once.
            Defaults to None.
        model_infos (Optional[SystemInfos], optional):
            Defines which python models should be simulated and how they are
            connected to other systems. It needs to have the same format as
            'fmu_infos' with the difference that
            the key "path" is not part of the dictionaries.
            Note: The name of the models can be chosen arbitrarily, but each
            name in 'fmu_infos' and 'model_infos' must occur only once.
            Defaults to None.
        model_classes (Optional[dict[str, SimulationEntity]], optional): Dictionary
            with the name of the python model as keys and a instance of the
            model class as values. The name in the dictionary must be
            chosen according to the names specified in 'model_infos'.
            Defaults to None.
        parameters_to_log (Optional[dict[str, list[str]]], optional):
            Dictionary that defines which parameters should be logged.
            It needs to have the following format:

            >>> parameters_to_log =
            ... {
            ...     "<name of system 1 (corresponding to the names specified in"
            ...     "'model_infos' or 'fmu_infos')>":
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
        logging_step_size (Optional[Union[float, int]], optional): step_size
            for logging. It must be a multiple of the chosen simulation 'step_size'.
            Example:
            If the simulation 'step_size' is set to 1e-3 and 'logging_step_size'
            is set to 2e-3, every second time step is logged.
        get_units (bool, optional): Determines whether the units of
            the logged parameter should be returned. Defaults to False.

    Raises:
        TypeError: start_time type was invalid
        TypeError: step_size type was invalid
        TypeError: fmu_infos type was invalid
        TypeError: model_infos type was invalid
        ValueError: fmu_infos and model_infos were 'None'
        TypeError: model_classes type was invalid
        ValueError: start_time value was invalid
        ValueError: step_size value was invalid

    Returns:
        Union[pd.DataFrame, tuple[pd.DataFrame, dict[str, Units]]:
            Result DataFrame with times series of logged parameters, units of
            logged parameters.
    """
    _validate_input(
        stop_time,
        step_size,
        fmu_infos,
        model_infos,
        model_classes,
        parameters_to_log,
        logging_step_size,
    )

    stop_time = float(stop_time)
    step_size = float(step_size)

    if logging_step_size is None:
        logging_step_size = step_size

    logging_step_size = float(logging_step_size)

    if fmu_infos is None:
        fmu_infos = []
    if model_infos is None:
        model_infos = []
    if model_classes is None:
        model_classes = {}
    if start_values is None:
        start_values = {}

    start_values = start_values.copy() # copy so mutating doesn't affect passed dict

    fmus = init_fmus(
        fmu_infos,
        step_size,
        start_values
    )

    models = init_models(
        model_infos,
        model_classes,
        start_values
    )

    systems = {**fmus, **models}

    connections = init_connections(fmu_infos + model_infos, systems)
    _parameters_to_log = init_parameter_list(parameters_to_log, systems)

    simulator = Simulation(systems, connections, _parameters_to_log)
    results = simulator.simulate(stop_time, step_size, logging_step_size)

    if get_units:
        units = simulator.get_units()
        return results, units

    return results


class SystemInfoKeys(Enum):
    """Enum containing the keys of fmu_info and model_info"""

    SYSTEM_NAME = "name"
    FMU_PATH = "path"
    CONNECTIONS = "connections"
    INPUT_PARAMETER = "parameter_name"
    CONNECTED_SYSTEM = "connect_to_system"
    OUTPUT_PARAMETER = "connect_to_external_parameter"


def init_fmus(
    fmu_infos: SystemInfos,
    step_size: float,
    start_values: StartValues
) -> dict[str, System]:
    """Initialize all System object and stores them in a dictionary.

    Args:
        fmu_infos (SystemInfos): Defines
            which fmus should be simulated and how they are connected to other
            systems.
        model_infos (SystemInfos):
            Defines which python models should be simulated and how they are
            connected to other systems.
        model_classes (dict[str, SimulationEntity]): Dictionary with the name of
            the models as keys and a instance of the model class as
            values.
        step_size (float): step size of the simulation

    Returns:
        dict[str, System]: Dictionary with system names as keys and the
            corresponding System instance as values.
    """
    fmus = {}
    for fmu_info in fmu_infos:
        fmu_name: str = fmu_info[SystemInfoKeys.SYSTEM_NAME.value]
        fmu_path: Path = utils.convert_str_to_path(
            fmu_info[SystemInfoKeys.FMU_PATH.value], "fmu_path"
        )
        fmu = Fmu(fmu_path, fmu_name, step_size)
        _start_values = start_values.get(fmu_name) or {}
        fmu.initialize(start_values = _start_values)
        system = System(fmu, fmu_name)
        fmus[fmu_name] = system
        print(f"FMU '{fmu_name}' initialized.")

    return fmus

def init_models(
    model_infos: SystemInfos,
    model_classes: dict[str, SimulationEntity],
    start_values: StartValues
) -> dict[str, System]:
    """Initialize all System object and stores them in a dictionary.

    Args:
        fmu_infos (SystemInfos): Defines
            which fmus should be simulated and how they are connected to other
            systems.
        model_infos (SystemInfos):
            Defines which python models should be simulated and how they are
            connected to other systems.
        model_classes (dict[str, SimulationEntity]): Dictionary with the name of
            the models as keys and a instance of the model class as
            values.
        step_size (float): step size of the simulation

    Returns:
        dict[str, System]: Dictionary with system names as keys and the
            corresponding System instance as values.
    """

    models = {}
    for model_info in model_infos:
        model_name: str = model_info[SystemInfoKeys.SYSTEM_NAME.value]
        model = model_classes[model_name]
        _start_values = start_values.get(model_name) or {}
        model.initialize(_start_values)
        system = System(model, model_name)
        models[model_name] = system
        print(f"Model '{model_name}' initialized.")

    return models


def init_connections(
    system_infos: SystemInfos, systems: dict[str, System]
) -> list[Connection]:
    """Initialize all the connections.

    Args:
        system_infos (SystemInfos):
            Defines how all systems are connected.
        systems (dict[str, System]): Dictionary with system names as keys and
            the corresponding System instance as values.

    Returns:
        list[Connection]: List of Connections.
    """
    all_connections: list[Connection] = []

    for system_info in system_infos:
        if system_info.get(SystemInfoKeys.CONNECTIONS.value) is not None:
            connections = system_info[SystemInfoKeys.CONNECTIONS.value]
            this_system_name = system_info[SystemInfoKeys.SYSTEM_NAME.value]
            this_system = systems[this_system_name]
            for con in connections:
                this_parameter_name = con[SystemInfoKeys.INPUT_PARAMETER.value]
                this_connection_point = SystemParameter(
                    this_system, this_parameter_name
                )
                other_system_name = con[SystemInfoKeys.CONNECTED_SYSTEM.value]
                other_system = systems[other_system_name]
                other_parameter_name = con[SystemInfoKeys.OUTPUT_PARAMETER.value]
                other_connection_point = SystemParameter(
                    other_system, other_parameter_name
                )
                connection = Connection(this_connection_point, other_connection_point)
                all_connections.append(connection)

    return all_connections


def init_parameter_list(
    parameters_to_log: Optional[dict[str, list[str]]], systems: dict[str, System]
) -> Optional[list[SystemParameter]]:
    """Initialize all parameters that should be logged.

    Args:
        parameters_to_log (Optional[dict[str, list[str]]]): Defines which
            parameters should be logged.
        systems (dict[str, System]): Dictionary with system names as keys and
            the corresponding System instance as values.

    Returns:
        Optional[list[SystemParameter]]: List of system parameters that should be
        logged.
    """
    if parameters_to_log is None:
        return None

    log: list[SystemParameter] = []

    for system_name in list(parameters_to_log.keys()):
        system = systems[system_name]
        for parameter_name in parameters_to_log[system_name]:
            parameter_to_log = SystemParameter(system, parameter_name)
            log.append(parameter_to_log)

    return log


def _validate_input(
    stop_time: Union[float, int],
    step_size: Union[float, int],
    fmu_infos: Optional[SystemInfos],
    model_infos: Optional[SystemInfos],
    model_classes: Optional[dict[str, SimulationEntity]],
    parameters_to_log: Optional[dict[str, list[str]]],
    logging_step_size: Optional[float],
) -> None:

    if not isinstance(stop_time, (float, int)):
        raise TypeError(f"'stop_time' is {type(stop_time)}; expected float, int")

    if not isinstance(step_size, (float, int)):
        raise TypeError(f"'step_size' is {type(step_size)}; expected float, int")

    if stop_time <= 0:
        raise ValueError(f"'stop_time' is {stop_time}; expected > 0")

    if step_size <= 0 or step_size >= stop_time:
        raise ValueError(f"'step_size' is {step_size}; expected (0, {stop_time})")

    if not fmu_infos and not model_infos:
        raise ValueError(
            "'fmu_infos' and 'model_infos' are empty; expected al least one to be not empty"
        )

    fmu_names = _validate_fmu_infos(fmu_infos)
    model_names = _validate_model_infos(model_infos)

    all_system_names = _get_all_system_names(fmu_names, model_names)

    if len(set(all_system_names)) < len(all_system_names):
        raise ValueError("Duplicate names in system infos.")

    _validate_model_classes(model_classes, model_names)

    if parameters_to_log is not None:
        _validate_parameters_to_log(parameters_to_log, all_system_names)

    if logging_step_size is not None:
        _validate_logging_step_size(logging_step_size, step_size)


def _validate_fmu_infos(fmu_infos: Optional[SystemInfos]) -> Optional[list[str]]:

    if fmu_infos is None:
        return None

    if not isinstance(fmu_infos, list):
        raise TypeError(f"'fmu_infos' is {type(fmu_infos)}; expected list")

    fmu_names: list[str] = []

    for fmu_info in fmu_infos:
        _check_key_exists(SystemInfoKeys.SYSTEM_NAME.value, fmu_info)
        _check_value_type(
            SystemInfoKeys.SYSTEM_NAME.value,
            fmu_info[SystemInfoKeys.SYSTEM_NAME.value],
            str,
        )
        fmu_names.append(fmu_info[SystemInfoKeys.SYSTEM_NAME.value])
        _check_key_exists(SystemInfoKeys.FMU_PATH.value, fmu_info)
        _check_value_type(
            SystemInfoKeys.FMU_PATH.value,
            fmu_info[SystemInfoKeys.FMU_PATH.value],
            (str, Path),
        )
        if fmu_info.get(SystemInfoKeys.CONNECTIONS.value) is not None:
            _validate_connection_infos(fmu_info[SystemInfoKeys.CONNECTIONS.value])

    return fmu_names


def _validate_model_infos(model_infos: Optional[SystemInfos]) -> Optional[list[str]]:

    if model_infos is None:
        return None

    if model_infos and not isinstance(model_infos, list):
        raise TypeError(f"'model_infos' is {type(model_infos)}; expected list")

    model_names: list[str] = []

    for model_info in model_infos:
        _check_key_exists(SystemInfoKeys.SYSTEM_NAME.value, model_info)
        _check_value_type(
            SystemInfoKeys.SYSTEM_NAME.value,
            model_info[SystemInfoKeys.SYSTEM_NAME.value],
            str,
        )
        model_names.append(model_info[SystemInfoKeys.SYSTEM_NAME.value])
        if model_info.get(SystemInfoKeys.CONNECTIONS.value) is not None:
            _validate_connection_infos(model_info[SystemInfoKeys.CONNECTIONS.value])

    return model_names


def _validate_connection_infos(connection_infos: ConnectionInfos) -> None:

    if not isinstance(connection_infos, list):
        raise TypeError(
            f"value of key '{SystemInfoKeys.CONNECTIONS.value}' is {type(connection_infos)}; expected list"
        )
    for connection in connection_infos:
        for key in (
            SystemInfoKeys.INPUT_PARAMETER.value,
            SystemInfoKeys.OUTPUT_PARAMETER.value,
            SystemInfoKeys.CONNECTED_SYSTEM.value,
        ):
            _check_key_exists(key, connection)
            _check_value_type(key, connection[key], str)


def _check_key_exists(key: str, info_dict: Union[SystemInfo, ConnectionInfo]) -> None:

    if key not in info_dict:
        raise KeyError(f"missing key '{key}' in {info_dict}")


def _check_value_type(key: str, value: Any, typ: Any) -> None:

    if not isinstance(value, typ):
        typ_name = typ.__name__
        if isinstance(typ, tuple):  # if multiple types allowed
            typ_name = ", ".join([t.name for t in typ])
        raise TypeError(f"value of key '{key}' is {type(value)}; expected {typ_name}")


def _get_all_system_names(
    fmu_names: Optional[list[str]], model_names: Optional[list[str]]
) -> list[str]:

    if fmu_names is not None and model_names is not None:
        return [*fmu_names, *model_names]
    if fmu_names is not None:
        return fmu_names
    if model_names is not None:
        return model_names
    return []


def _validate_model_classes(
    model_classes: Optional[dict[str, SimulationEntity]],
    model_names: Optional[list[str]],
) -> None:

    if model_classes is None:
        if model_names:
            raise ValueError("Models are defined but 'model_classes' is 'None'")
        return

    if model_names is None:
        model_names = []

    if not isinstance(model_classes, dict):
        raise TypeError(f"'model_classes' is {type(model_classes)}; expected dict")

    if not set(model_classes.keys()) == set(model_names):
        raise ValueError("Names in 'model_classes' and in 'model_info' do not match.")


def _validate_parameters_to_log(
    parameters_to_log: dict[str, list[str]], system_names: list[str]
) -> None:

    if not isinstance(parameters_to_log, dict):
        raise TypeError(
            f"'parameters_to_log' is {type(parameters_to_log)}; expected dict"
        )

    for name, parameter_names in parameters_to_log.items():
        if name not in system_names:
            raise ValueError(
                f"System name '{name}' is defined in 'parameters_to_log', but does not exist."
            )
        if not isinstance(parameter_names, list):
            raise TypeError(
                f"Value to key '{name}' in 'parameters_to_log' is {type(parameter_names)}; expected list"
            )


def _validate_logging_step_size(
    logging_step_size: Union[int, float], step_size: Union[int, float]
) -> None:

    if not isinstance(logging_step_size, (int, float)):
        raise TypeError(
            f"'logging_step_size' is {type(logging_step_size)}; expected int, float"
        )

    if not round(logging_step_size / step_size, 10).is_integer():
        raise ValueError(
            "'logging_step_size' must be a multiple of the chosen 'step_size'"
        )
