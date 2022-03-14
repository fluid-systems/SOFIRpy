"""This module allows to simulate multiple fmus and controllers."""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union
import numpy as np
import pandas as pd
from alive_progress import alive_bar
from fair_sim.simulation.simulation_entity import SimulationEntity
from fair_sim.simulation.fmu import Fmu


@dataclass(frozen=True)
class System:
    """System object representing a simulation entity.

    Args:
            simulation_entity (SimulationEntity): fmu or controller
            name (str): name of the system
    """

    simulation_entity: SimulationEntity
    name: str


@dataclass(frozen=True)
class SystemParameter:
    """SystemParameter object representing a parameter in a system.

    Args:
            system (System): System object
            name (str): name of the paremeter
    """

    system: System
    name: str


@dataclass(frozen=True)
class ConnectionPoint(SystemParameter):
    """ConnectionPoint object representing a parameter in a system that is an input our output."""


@dataclass(frozen=True)
class Connection:
    """Object representing a connection between two systems.

    Args:
        input_point (ConnectionPoint): ConnectionPoint object that
            represents an input of a system
        output_point (ConnectionPoint): ConnectionPoint object that
            represents an output of a system
    """

    input_point: ConnectionPoint
    output_point: ConnectionPoint


class Simulation:
    """Object that performs the simulation."""

    def __init__(
        self,
        systems: list[System],
        connections: list[Connection],
        parameters_to_record: Optional[list[SystemParameter]] = None,
    ) -> None:
        """Initialize Simulation object.

        Args:
            systems (list[System]): list of systems which are to be simulated
            connections (list[Connection]): list of connections between the
                 systems
            parameters_to_record (list[SystemParameter], optional): List of
                Parameters that should be logged. Defaults to None.
        """
        self.systems = systems
        self.connections = connections
        if parameters_to_record is None:
            parameters_to_record = []
        self.parameters_to_record = parameters_to_record
        self.results = self.create_result_df(self.parameters_to_record)

    def simulate(
        self, stop_time: float, step_size: float, start_time: float = 0.0
    ) -> pd.DataFrame:
        """Simulate the systems.

        Args:
            stop_time (float): stop time for the simulation
            step_size (float): step size for the simulation
            start_time (float, optional): start time of the simulation.
                Defaults to 0.0.

        Returns:
            pd.DataFrame: results dataframe with times series of logged
            parameters
        """
        time_series = np.arange(start_time, stop_time + step_size, step_size)

        print("Starting Simulation...")

        with alive_bar(len(time_series), bar="blocks", spinner="classic") as bar:
            for time_step, time in enumerate(time_series):

                self.log_values(time, time_step)
                self.set_systems_inputs()
                self.do_step(time)
                bar()

        return self.results

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
            input_system.simulation_entity.set_input(input_name, input_value)

    def do_step(self, time: float) -> None:
        """Perform a calculation in all systems.

        Args:
            time (float): current simulation time
            step_size (float): step size of the simulation
        """
        for system in self.systems:
            system.simulation_entity.do_step(time)

    def log_values(self, time: float, time_step: int) -> None:
        """Log parameter values that are set o be logged.

        Args:
            time (float): current simulation time
            time_step (int): current time step
        """
        new_value_row = [time]
        for parameter in self.parameters_to_record:
            system = parameter.system
            parameter_name = parameter.name
            value = system.simulation_entity.get_parameter_value(parameter_name)
            new_value_row += [value]

        self.results.loc[time_step] = new_value_row

    def create_result_df(
        self, parameters_to_log: list[SystemParameter]
    ) -> pd.DataFrame:
        """Initialise the result dataframe. By default the first column contains the time.

        Args:
            parameters_to_log (list[SystemParameter]): list of parameters that
                should be logged

        Returns:
            pd.DataFrame: dataframe with only the column names
        """
        columns = [
            f"{parameter.system.name}.{parameter.name}"
            for parameter in parameters_to_log
        ]

        return pd.DataFrame(columns=["time"] + columns)

    def get_units(self) -> dict[str, str]:
        """Get a dictionary with all logged parameters as keys and their units as values.

        Returns:
            dict[str, str]: keys: parameter name, values: unit. If the unit can
            not be obtained it is set to None.
        """
        units = {}
        for parameter in self.parameters_to_record:
            system = parameter.system
            parameter_name = parameter.name
            try:
                unit = system.simulation_entity.get_unit(parameter_name)
            except AttributeError:
                unit = None
            units[f"{system.name}.{parameter_name}"] = unit

        return units


def simulate(
    stop_time: Union[float, int],
    step_size: float,
    fmu_infos: Optional[list[dict[str, Union[str, list[dict[str, str]]]]]] = None,
    control_infos: Optional[list[dict[str, Union[str, list[dict[str, str]]]]]] = None,
    control_classes: Optional[dict[str, SimulationEntity]] = None,
    parameters_to_log: Optional[dict[str, list[str]]] = None,
    get_units: Optional[bool] = False,
) -> Union[pd.DataFrame, tuple[pd.DataFrame, dict[str, str]]]:
    """Simulate fmus and controllers."

    Any number of controllers and fmus can be simulated, but at least one
    controller or fmu has to be simulated.

    Args:
        stop_time (Union[float,int]): stop time for the simulation
        step_size (float): step size for the simulation
        fmu_infos (Optional[list[dict[str, Union[str, list[dict[str, str]]]]]], optional):
            Defines which fmus should be simulated and how they are connected
            to other systems. It needs to have the following formart:

            >>> fmu_infos = [
            ... {"name": "<name of the fmu>",
            ...  "path": "<path to the fmu>",
            ...  "connections":
            ...     [
            ...     {
            ...         "parameter name":       "<name of the input"
            ...                                 "parameter of the fmu>",
            ...         "connect to system":    "<name of the system the input"
            ...                                 "parameter should be connected to>",
            ...         "connect to external parameter":    "<name of the output"
            ...                                             "parameter in the"
            ...                                             "connected system the"
            ...                                             "input parameter should"
            ...                                             "be connected to>"
            ...         },
            ...         {
            ...         "parameter name":       "<name of the input"
            ...                                 "parameter of the fmu>",
            ...         "connect to system":    "<name of the system the input"
            ...                                  "parameter should be connected to>",
            ...         "connect to external parameter":    "<name of the output"
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
            ...         "parameter name":       "<name of the input"
            ...                                 "parameter of the fmu>",
            ...         "connect to system":    "<name of the system the input"
            ...                                  "parameter should be connected to>",
            ...         "connect to external parameter":    "<name of the output"
            ...                                             "parameter in the"
            ...                                             "connected system the"
            ...                                             "input parameter should"
            ...                                             "be connected to>"
            ...        }
            ... }
            ... ]

            Note: The name of the fmus can be chosen arbitrarily, but each name
            in the controllers and the fmus must occur only once.
            Defaults to None.
        control_infos (Optional[list[dict[str, Union[str, list[dict[str, str]]]]]], optional):
            Defines which controllers should be simulated and how they are
            connected to other systems. It needs to have the same format as
            'fmu_infos' with the difference that
            the key "path" is not part of the dictionaries.
            Note: The name of the controllers can be chosen arbitrarily, but
            each name in the controllers and the fmus must occur only once.
            Defaults to None.
        control_classes (Optional[dict[str, SimulationEntity]], optional): Dictionary
            with the name of the controller as keys and a instance of the
            controller class as values. The name in the dictionary must be
            chosen according to the names specified in 'control_infos'.
            Defaults to None.
        parameters_to_log (Optional[dict[str, list[str]]], optional):
            Dictionary that defines which parameters should be logged.
            It needs to have the following format:

            >>> parameters_to_log =
            ... {
            ...     "<name of system 1 (corresponding to the names specified in"
            ...     "'control_infos' or 'fmu_infos')>":
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
        get_units (Optional[bool], optional): Determines whether the units of
            the logged parameter should be returned. Defaults to False.

    Raises:
        TypeError: start_time type was invalid
        TypeError: step_size type was invalid
        TypeError: fmu_infos type was invalid
        TypeError: control_infos type was invalid
        ValueError: fmu_infos and control_infos were 'None'
        TypeError: control_classes type was invalid
        ValueError: start_time value was invalid
        ValueError: step_size value was invalid

    Returns:
        Union[pd.DataFrame, tuple[pd.DataFrame, dict[str,str]]]:
            Result Dataframe with times series of logged parameters, units of
            logged parameters.
    """
    if not isinstance(stop_time, (float, int)):
        raise TypeError(f"'stop_time' is {type(stop_time)}; expected float, int")
    stop_time = float(stop_time)

    if not isinstance(step_size, (float, int)):
        raise TypeError(f"'step_size' is {type(step_size)}; expected float, int")
    step_size = float(step_size)

    if fmu_infos and not isinstance(fmu_infos, list):
        raise TypeError(f"'fmu_infos' is {type(fmu_infos)}; expected list")

    if control_infos and not isinstance(control_infos, list):
        raise TypeError(f"'control_infos' is {type(control_infos)}; expected list")

    if not fmu_infos and not control_infos:
        raise ValueError(
            "'fmu_infos' and 'control_infos' are empty; expected al least one to be not empty"
        )

    if control_classes and not isinstance(control_classes, dict):
        raise TypeError(f"'control_classes' is {type(control_classes)}; expected dict")

    if stop_time <= 0:
        raise ValueError(f"stop_time is {stop_time}; expected > 0")

    if step_size <= 0 or step_size >= stop_time:
        raise ValueError(f"'step_size' is {step_size}; expected (0, {stop_time})")

    if fmu_infos is None:
        fmu_infos = []
    if control_infos is None:
        control_infos = []
    if control_classes is None:
        control_classes = {}

    systems = init_systems(fmu_infos, control_infos, control_classes, step_size)
    connections = init_connections(fmu_infos + control_infos, systems)
    _parameters_to_log = init_parameter_list(parameters_to_log, systems)

    simulator = Simulation(list(systems.values()), connections, _parameters_to_log)

    results = simulator.simulate(stop_time, step_size)

    if get_units:
        units = simulator.get_units()
        return results, units

    return results


def init_systems(
    fmu_infos: list[dict[str, Union[str, list[dict[str, str]]]]],
    control_infos: list[dict[str, Union[str, list[dict[str, str]]]]],
    control_classes: dict[str, SimulationEntity],
    step_size: float,
) -> dict[str, System]:
    """Initialize all System object and stores them in a dictionary.

    Args:
        fmu_infos (list[dict[str, Union[str, list[dict[str, str]]]]]): Defines
            which fmus should be simulated and how they are connected to other
            systems.
        control_infos (list[dict[str, Union[str, list[dict[str, str]]]]]):
            Defines which controllers should be simulated and how they are
            connected to other systems.
        control_classes (dict[str, SimulationEntity]): Dictionary with the name of
            the controller as keys and a instance of the controller class as
            values.
        step_size (float): step size of the simulation

    Returns:
        dict[str, System]: Dictrionary with system names as keys and the
            corresponding System instance as values.
    """
    systems = {}
    for fmu_info in fmu_infos:
        fmu_name: str = fmu_info["name"]
        _fmu_path: str = fmu_info["path"]
        fmu_path = Path(_fmu_path)
        fmu = Fmu(fmu_path, step_size)
        fmu.initialize_fmu()
        system = System(fmu, fmu_name)
        systems[fmu_name] = system
        print(f"FMU '{fmu_name}' initialized.")

    for control_info in control_infos:
        control_name: str = control_info["name"]
        controller = control_classes[control_name]
        system = System(controller, control_name)
        systems[control_name] = system
        print(f"Controller '{control_name}' initialized.")

    return systems


def init_connections(
    system_infos: list[dict[str, Union[str, list[dict[str, str]]]]],
    systems: dict[str, System],
) -> list[Connection]:
    """Initialize all the connections.

    Args:
        system_infos (list[dict[str, Union[str, list[dict[str, str]]]]]):
            Defines how all systems are connected.
        systems (dict[str, System]): Dictrionary with system names as keys and
            the corresponding System instance as values.

    Returns:
        list[Connection]: List of Connections.
    """
    all_connections = []

    for system_info in system_infos:
        if system_info.get("connections"):
            connections = system_info["connections"]
            this_system_name = system_info["name"]
            this_system = systems[this_system_name]
            for con in connections:
                this_parameter_name = con["parameter name"]
                this_connection_point = ConnectionPoint(
                    this_system, this_parameter_name
                )
                other_system_name = con["connect to system"]
                other_system = systems[other_system_name]
                other_parameter_name = con["connect to external parameter"]
                other_connection_point = ConnectionPoint(
                    other_system, other_parameter_name
                )
                connection = Connection(this_connection_point, other_connection_point)
                all_connections.append(connection)

    return all_connections


def init_parameter_list(
    parameters_to_log: Optional[dict[str, list[str]]], systems: dict[str, System]
) -> list[SystemParameter]:
    """Initialize all parameters that should be logged.

    Args:
        parameters_to_log (Optional[dict[str, list[str]]]): Defines which
            paramters should be logged.
        systems (dict[str, System]): Dictrionary with system names as keys and
            the corresponding System instance as values.

    Returns:
        list[SystemParameter]: List of system parameters that should be logged.
    """
    log: list[SystemParameter] = []

    if parameters_to_log is None:
        return log

    for system_name in list(parameters_to_log.keys()):
        system = systems[system_name]
        for parameter_name in parameters_to_log[system_name]:
            parameter_to_log = SystemParameter(system, parameter_name)
            log.append(parameter_to_log)

    return log