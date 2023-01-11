"""This module allows to co-simulate multiple fmus and models written in python."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, TypedDict, Union

import numpy as np
import numpy.typing as npt
import pandas as pd
from tqdm import tqdm
from typing_extensions import NotRequired

from sofirpy import utils
from sofirpy.simulation.fmu import Fmu
from sofirpy.simulation.simulation_entity import SimulationEntity, StartValue


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
            system (str): Name of the corresponding system
            name (str): name of the parameter
    """

    system_name: str
    name: str


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

        1. A time array is created starting from 0 to the specified stop time. The
           intervals have the size of the step size. If the last element in the array
           is greater than the stop time, it is deleted.

        2. The logging multiple is calculated from the logging step size. Since the
           logging step size needs to be a multiple of the step size, the logging
           multiple is an integer. Therefore a precise modulo operation inside the
           simulation loop can be performed.
           E.g if the step size 1e-3 and the logging step size is 1e-1, the logging
           multiple will be 100. Therefor every 100 time step will be logged.

        3. The numpy results object is initialized.

        4. The start values are logged.

        5. The simulation loop starts.

           5.1 A simulation step is performed.

           5.2 All system inputs are set.

           5.3 If the time step + 1 is a multiple of the logging multiple, values are
           logged.

        6. The simulation process is concluded.

        7. The numpy results object is converted to a pandas DataFrame.

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
            input_system_name = connection.input_point.system_name
            input_system = self.systems[input_system_name]
            input_name = connection.input_point.name
            output_system_name = connection.output_point.system_name
            output_system = self.systems[output_system_name]
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
            system_name = parameter.system_name
            system = self.systems[system_name]
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
            f"{parameter.system_name}.{parameter.name}"
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
            system_name = parameter.system_name
            system = self.systems[system_name]
            parameter_name = parameter.name
            try:
                unit = system.simulation_entity.get_unit(parameter_name)
            except AttributeError:
                unit = None
            units[f"{system.name}.{parameter_name}"] = unit

        return units


ConnectionInfo = dict[str, str]

ConnectionInfos = list[ConnectionInfo]


class FmuInfo(TypedDict):
    """TypedDict for fmu_info."""

    name: str
    path: Union[str, Path]
    connections: NotRequired[ConnectionInfos]


class ModelInfo(TypedDict):
    """TypedDict for model_info."""

    name: str
    connections: NotRequired[ConnectionInfos]


FmuInfos = list[FmuInfo]
ModelInfos = list[ModelInfo]
SystemInfo = Union[ModelInfo, FmuInfo]
SystemInfos = list[SystemInfo]

Units = dict[str, Optional[str]]

StartValues = dict[str, dict[str, StartValue]]


def simulate(
    stop_time: Union[float, int],
    step_size: Union[float, int],
    fmu_infos: Optional[FmuInfos] = None,
    model_infos: Optional[ModelInfos] = None,
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
        fmu_infos (Optional[FmuInfos], optional):
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
        model_infos (Optional[ModelInfos], optional):
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
        start_values (Optional[StartValues], optional): Dictionary with start values for
            the simulation. For Fmus the unit can also be specified as a string.
            It has the following format:

            >>> start_values =
            ... {
            ...     "<name of system 1 (corresponding to the names specified in"
            ...     "'model_infos' or 'fmu_infos')>":
            ...     {
            ...         "<name of parameter 1>": "<start value>",
            ...         "<name of parameter 2>", "(<start value>, unit e.g 'kg.m2')"
            ...     },
            ...     "<name of system 2>":
            ...     {
            ...         "<name of parameter 1>": "<start value>",
            ...         "<name of parameter 2>": "<start value>"
            ...     }
            ... }
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
            is set to 2e-3, every second time step is logged. Defaults to None.
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
        start_values,
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

    start_values = start_values.copy()  # copy so mutating doesn't affect passed dict

    fmus = init_fmus(fmu_infos, step_size, start_values)

    models = init_models(model_infos, model_classes, start_values)

    systems = {**fmus, **models}

    connections = init_connections([*fmu_infos, *model_infos])
    _parameters_to_log = init_parameter_list(parameters_to_log)

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
    fmu_infos: FmuInfos, step_size: float, start_values: StartValues
) -> dict[str, System]:
    """Initialize all System object and stores them in a dictionary.

    Args:
        fmu_infos (FmuInfos): Defines
            which fmus should be simulated and how they are connected to other
            systems.
        model_infos (ModelInfos):
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
        fmu.initialize(start_values=_start_values)
        system = System(fmu, fmu_name)
        fmus[fmu_name] = system
        print(f"FMU '{fmu_name}' initialized.")

    return fmus


def init_models(
    model_infos: ModelInfos,
    model_classes: dict[str, SimulationEntity],
    start_values: StartValues,
) -> dict[str, System]:
    """Initialize all System object and stores them in a dictionary.

    Args:
        fmu_infos (FmuInfos): Defines
            which fmus should be simulated and how they are connected to other
            systems.
        model_infos (ModelInfos):
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


def init_connections(system_infos: SystemInfos) -> list[Connection]:
    """Initialize all the connections.

    Args:
        system_infos (SystemInfos):
            Defines how all systems are connected.

    Returns:
        list[Connection]: List of Connections.
    """
    all_connections: list[Connection] = []

    for system_info in system_infos:
        if SystemInfoKeys.CONNECTIONS.value in system_info:
            connections = system_info[SystemInfoKeys.CONNECTIONS.value]
            this_system_name = system_info[SystemInfoKeys.SYSTEM_NAME.value]
            for con in connections:
                this_parameter_name = con[SystemInfoKeys.INPUT_PARAMETER.value]
                this_connection_point = SystemParameter(
                    this_system_name, this_parameter_name
                )
                other_system_name = con[SystemInfoKeys.CONNECTED_SYSTEM.value]
                other_parameter_name = con[SystemInfoKeys.OUTPUT_PARAMETER.value]
                other_connection_point = SystemParameter(
                    other_system_name, other_parameter_name
                )
                connection = Connection(this_connection_point, other_connection_point)
                all_connections.append(connection)

    return all_connections


def init_parameter_list(
    parameters_to_log: Optional[dict[str, list[str]]]
) -> Optional[list[SystemParameter]]:
    """Initialize all parameters that should be logged.

    Args:
        parameters_to_log (Optional[dict[str, list[str]]]): Defines which
            parameters should be logged.

    Returns:
        Optional[list[SystemParameter]]: List of system parameters that should be
        logged.
    """
    if parameters_to_log is None:
        return None

    log: list[SystemParameter] = []

    for system_name, parameter_names in parameters_to_log.items():
        for parameter_name in parameter_names:
            parameter_to_log = SystemParameter(system_name, parameter_name)
            log.append(parameter_to_log)

    return log


def _validate_input(
    stop_time: Union[float, int],
    step_size: Union[float, int],
    fmu_infos: Optional[FmuInfos],
    model_infos: Optional[ModelInfos],
    model_classes: Optional[dict[str, SimulationEntity]],
    parameters_to_log: Optional[dict[str, list[str]]],
    logging_step_size: Optional[float],
    start_values: Optional[StartValues],
) -> None:

    utils.check_type(stop_time, "stop_time", (float, int))
    utils.check_type(step_size, "step_size", (float, int))

    if stop_time <= 0:
        raise ValueError(f"'stop_time' is {stop_time}; expected > 0")

    if step_size <= 0 or step_size >= stop_time:
        raise ValueError(f"'step_size' is {step_size}; expected (0, {stop_time})")

    if not fmu_infos and not model_infos:
        raise ValueError(
            "'fmu_infos' and 'model_infos' are empty; "
            "expected at least one to be not empty"
        )

    fmu_names = _validate_fmu_infos(fmu_infos)
    model_names = _validate_model_infos(model_infos)

    all_system_names = fmu_names + model_names

    if len(set(all_system_names)) < len(all_system_names):
        raise ValueError("Duplicate names in system infos.")

    fmu_infos = fmu_infos or []
    model_infos = model_infos or []

    _validate_connection_infos([*fmu_infos, *model_infos], all_system_names)

    _validate_model_classes(model_classes, model_names)

    if parameters_to_log is not None:
        _validate_parameters_to_log(parameters_to_log, all_system_names)

    if logging_step_size is not None:
        _validate_logging_step_size(logging_step_size, step_size)

    if start_values is not None:
        _validate_start_values(start_values, all_system_names)


def _validate_fmu_infos(fmu_infos: Optional[FmuInfos]) -> list[str]:

    if fmu_infos is None:
        return []

    utils.check_type(fmu_infos, "fmu_infos", list)

    fmu_names: list[str] = []

    for fmu_info in fmu_infos:
        utils.check_type(fmu_info, "element in list 'fmu_infos", dict)
        _check_key_exists(SystemInfoKeys.SYSTEM_NAME.value, fmu_info)
        utils.check_type(
            fmu_info[SystemInfoKeys.SYSTEM_NAME.value],
            f"Value to key '{SystemInfoKeys.SYSTEM_NAME.value}' in 'fmu_infos",
            str,
        )
        fmu_names.append(fmu_info[SystemInfoKeys.SYSTEM_NAME.value])
        _check_key_exists(SystemInfoKeys.FMU_PATH.value, fmu_info)
        utils.check_type(
            fmu_info[SystemInfoKeys.FMU_PATH.value],
            f"Value to key '{SystemInfoKeys.FMU_PATH.value}' in 'fmu_infos",
            (str, Path),
        )

    return fmu_names


def _validate_model_infos(model_infos: Optional[ModelInfos]) -> list[str]:

    if model_infos is None:
        return []

    utils.check_type(model_infos, "model_infos", list)

    model_names: list[str] = []

    for model_info in model_infos:
        utils.check_type(model_info, "element in list 'model_info", dict)
        _check_key_exists(SystemInfoKeys.SYSTEM_NAME.value, model_info)
        utils.check_type(
            model_info[SystemInfoKeys.SYSTEM_NAME.value],
            f"Value to key '{SystemInfoKeys.SYSTEM_NAME.value}' in 'model_infos",
            str,
        )
        model_names.append(model_info[SystemInfoKeys.SYSTEM_NAME.value])

    return model_names


def _validate_connection_infos(
    system_infos: SystemInfos, system_names: list[str]
) -> None:

    for system_info in system_infos:
        if SystemInfoKeys.CONNECTIONS.value in system_info:
            utils.check_type(
                system_info[SystemInfoKeys.CONNECTIONS.value],
                f"Value to key '{SystemInfoKeys.CONNECTIONS.value}",
                list,
            )
            for connection in system_info[SystemInfoKeys.CONNECTIONS.value]:
                utils.check_type(connection, "element in list 'connections", dict)
                for key in (
                    SystemInfoKeys.INPUT_PARAMETER.value,
                    SystemInfoKeys.OUTPUT_PARAMETER.value,
                    SystemInfoKeys.CONNECTED_SYSTEM.value,
                ):
                    _check_key_exists(key, connection)
                    utils.check_type(
                        connection[key], f"Value to key '{key}' in 'connections", str
                    )
                connected_system = connection[SystemInfoKeys.CONNECTED_SYSTEM.value]
                if connected_system not in system_names:
                    raise ValueError(
                        f"System '{connected_system}' specified "
                        "in connections doesn't exist."
                    )


def _check_key_exists(key: str, info_dict: Union[SystemInfo, ConnectionInfo]) -> None:

    if key not in info_dict:
        raise KeyError(f"missing key '{key}' in {info_dict}")


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

    utils.check_type(model_classes, "model_classes", dict)

    if not set(model_classes.keys()) == set(model_names):
        raise ValueError("Names in 'model_classes' and in 'model_info' do not match.")


def _validate_parameters_to_log(
    parameters_to_log: dict[str, list[str]], system_names: list[str]
) -> None:

    utils.check_type(parameters_to_log, "parameters_to_log", dict)

    for name, parameter_names in parameters_to_log.items():
        if name not in system_names:
            raise ValueError(
                f"System name '{name}' is defined in 'parameters_to_log', "
                "but does not exist."
            )
        utils.check_type(
            parameter_names, f"Value to key '{name}' in 'parameters_to_log", list
        )


def _validate_logging_step_size(
    logging_step_size: Union[int, float], step_size: Union[int, float]
) -> None:

    utils.check_type(logging_step_size, "logging_step_size", (int, float))

    if not round(logging_step_size / step_size, 10).is_integer():
        raise ValueError(
            "'logging_step_size' must be a multiple of the chosen 'step_size'"
        )


def _validate_start_values(
    start_values: StartValues, all_system_names: list[str]
) -> None:

    utils.check_type(start_values, "start_values", dict)

    for name in start_values:
        if name not in all_system_names:
            raise ValueError(
                f"System name '{name}' is defined in 'start_values', "
                "but does not exist."
            )
