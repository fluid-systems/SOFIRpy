"""This module allows to co-simulate multiple fmus and models written in python."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from numbers import Real
from pathlib import Path
from typing import Literal, Optional, Union, overload

import numpy as np
import numpy.typing as npt
import pandas as pd
from tqdm import tqdm

import sofirpy.common as co
from sofirpy import utils
from sofirpy.simulation.fmu import Fmu
from sofirpy.simulation.simulation_entity import SimulationEntity


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


class Simulator:
    """Object that performs the simulation."""

    def __init__(
        self,
        systems: dict[str, System],
        connections: list[Connection],
        parameters_to_log: list[SystemParameter],
    ) -> None:
        """Initialize Simulator object.

        Args:
            systems (list[System]): list of systems which are to be simulated
            connections (list[Connection]): list of connections between the
                 systems
            parameters_to_log (list[SystemParameter]): List of Parameters that should
                be logged.
        """
        self.systems = systems
        self.connections = connections
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
           is greater than the stop time, it is deleted. Advancing in time this way,
           leads to less numerical errors in comparison than using a while loop and
           adding the step size in each iteration.

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
        time_series = self.compute_time_array(stop_time, step_size, start_time)
        number_log_steps = int(stop_time / logging_step_size) + 1
        logging_multiple = round(logging_step_size / step_size)
        self.results = np.zeros((number_log_steps, len(self.parameters_to_log) + 1))

        logging.info("Starting simulation.")

        self.log_values(time=0, log_step=0)
        log_step = 1
        for time_step, time in enumerate(tqdm(time_series[:-1])):
            self.do_step(time)
            self.set_systems_inputs()
            if ((time_step + 1) % logging_multiple) == 0:
                self.log_values(time_series[time_step + 1], log_step)
                log_step += 1

        logging.info("Simulation done.")
        logging.info("Concluding simulation.")
        self.conclude_simulation()
        logging.info("Simulation concluded.")

        return self.convert_to_data_frame(self.results)

    def compute_time_array(
        self, stop_time: float, step_size: float, start_time: float
    ) -> npt.NDArray[np.float64]:
        """Compute the time array for the simulation.

        Args:
            stop_time (float): stop time for the simulation
            step_size (float): step size for the simulation
            start_time (float): start time of the simulation.

        Returns:
            npt.NDArray[np.float64]: time array
        """
        time_series = np.arange(start_time, stop_time + step_size, step_size)
        if time_series[-1] > stop_time:
            return time_series[:-1]
        return time_series

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

    def get_units(self) -> co.Units:
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
            unit = system.simulation_entity.get_unit(parameter_name)
            units[f"{system.name}.{parameter_name}"] = unit

        return units


@overload
def simulate(
    stop_time: float,
    step_size: float,
    fmu_paths: co.FmuPaths | None = ...,
    model_classes: co.ModelClasses | None = ...,
    connections_config: co.ConnectionsConfig | None = ...,
    start_values: co.StartValues | None = ...,
    parameters_to_log: co.ParametersToLog | None = ...,
    logging_step_size: float | None = ...,
    *,
    get_units: Literal[True],
) -> tuple[pd.DataFrame, co.Units]:
    ...


@overload
def simulate(
    stop_time: float,
    step_size: float,
    fmu_paths: co.FmuPaths | None = ...,
    model_classes: co.ModelClasses | None = ...,
    connections_config: co.ConnectionsConfig | None = ...,
    start_values: co.StartValues | None = ...,
    parameters_to_log: co.ParametersToLog | None = ...,
    logging_step_size: float | None = ...,
    *,
    get_units: Literal[False],
) -> pd.DataFrame:
    ...


@overload
def simulate(
    stop_time: float,
    step_size: float,
    fmu_paths: co.FmuPaths | None = ...,
    model_classes: co.ModelClasses | None = ...,
    connections_config: co.ConnectionsConfig | None = ...,
    start_values: co.StartValues | None = ...,
    parameters_to_log: co.ParametersToLog | None = ...,
    logging_step_size: float | None = ...,
) -> pd.DataFrame:
    ...


def simulate(
    stop_time: float,
    step_size: float,
    fmu_paths: co.FmuPaths | None = None,
    model_classes: co.ModelClasses | None = None,
    connections_config: co.ConnectionsConfig | None = None,
    start_values: co.StartValues | None = None,
    parameters_to_log: co.ParametersToLog | None = None,
    logging_step_size: float | None = None,
    get_units: bool = False,
) -> Union[pd.DataFrame, tuple[pd.DataFrame, co.Units]]:
    """Simulate fmus and models written in python.

    Any number of python models and fmus can be simulated, but at least one
    python model or fmu has to be simulated.

    Args:
        stop_time (float): stop time for the simulation
        step_size (float): step size for the simulation
        fmu_paths (FmuPaths | None, optional):
            Dictionary which defines which fmu should be simulated.
            key -> name of the fmu; value -> path to the fmu

            >>> fmu_paths = {
            ...    "<name of the fmu 1>": <Path to the fmu1>,
            ...    "<name of the fmu 2>": <Path to the fmu2>,
            ... }

            Note: The name of the fmus can be chosen arbitrarily, but each name
            in 'fmu_paths' and 'model_classes' must occur only once.
            Defaults to None.
        model_classes (ModelClasses | None, optional):
            Dictionary which defines which Python Models should be simulated.
            key -> name of the model; value -> Class of the model. The class that
            defines the model must inherit from the abstract class SimulationEntity.

            >>> model_classes = {
            ...    "<name of the model 1>": <class of the model1>
            ...    "<name of the model 2>": <class of the model2>
            ... }

            Note: The name of the models can be chosen arbitrarily, but each
            name in 'fmu_paths' and 'model_classes' must occur only once.
            Defaults to None.
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
        start_values (StartValues | None, optional): Dictionary which defines start
            values for the systems. For Fmus the unit can also be specified as a string.
            key -> name of the system;
            value -> dictionary (key -> name of the parameter; value -> start value)

            >>> start_values = {
            ...     "<name of system 1>":
            ...     {
            ...         "<name of parameter 1>": <start value>,
            ...         "<name of parameter 2>", (<start value>, unit e.g 'kg.m2')
            ...     },
            ...     "<name of system 2>":
            ...     {
            ...         "<name of parameter 1>": <start value>,
            ...         "<name of parameter 2>": <start value>
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
        get_units (bool, optional): Determines whether the units of
            the logged parameter should be returned. Defaults to False.

    Raises:
        TypeError: start_time type was invalid
        TypeError: step_size type was invalid
        TypeError: fmu_paths type was invalid
        TypeError: model_classes type was invalid
        ValueError: fmu_paths and model_classes were 'None'
        ValueError: start_time value was invalid
        ValueError: step_size value was invalid

    Returns:
        Union[pd.DataFrame, tuple[pd.DataFrame, dict[str, Units]]:
            Result DataFrame with times series of logged parameters, units of
            logged parameters.
    """
    logging.basicConfig(
        format="Simulation::%(levelname)s::%(message)s",
        level=logging.INFO,
        force=True,
    )
    _validate_input(
        stop_time,
        step_size,
        fmu_paths,
        model_classes,
        connections_config,
        parameters_to_log,
        logging_step_size,
        start_values,
    )

    stop_time = float(stop_time)
    step_size = float(step_size)

    logging.info(f"Simulation stop time set to {stop_time} seconds.")
    logging.info(f"Simulation step size set to {step_size} seconds.")

    logging_step_size = float(logging_step_size or step_size)

    logging.info(f"Simulation logging step size set to {logging_step_size} seconds.")

    connections_config = connections_config or {}
    fmu_paths = fmu_paths or {}
    model_classes = model_classes or {}
    start_values = start_values or {}
    parameters_to_log = parameters_to_log or {}

    start_values = start_values.copy()  # copy because dict will be modified in fmu.py

    fmus = init_fmus(fmu_paths, step_size, start_values)

    models = init_models(model_classes, start_values)

    connections = init_connections(connections_config)
    _parameters_to_log = init_parameter_list(parameters_to_log)

    simulator = Simulator({**fmus, **models}, connections, _parameters_to_log)
    results = simulator.simulate(stop_time, step_size, logging_step_size)

    if get_units:
        units = simulator.get_units()
        return results, units

    return results


def init_fmus(
    fmu_paths: co.FmuPaths, step_size: float, start_values: co.StartValues
) -> dict[str, System]:
    """Initialize fmus as a System object and store them in a dictionary.

    Args:
        fmu_paths (FmuPaths): Dictionary which defines which fmu should be simulated.
            key -> name of the fmu; value -> path to the fmu
        step_size (float): step size of the simulation
        start_values (StartValues): Dictionary which defines start values for the
            systems.

    Returns:
        dict[str, System]: key -> fmu name; value -> System instance
    """
    fmus: dict[str, System] = {}
    for fmu_name, _fmu_path in fmu_paths.items():
        fmu_path: Path = utils.convert_str_to_path(_fmu_path, "fmu_path")
        fmu = Fmu(fmu_path, fmu_name, step_size)
        _start_values = start_values.get(fmu_name) or {}
        fmu.initialize(start_values=_start_values)
        system = System(fmu, fmu_name)
        fmus[fmu_name] = system
        logging.info(f"FMU '{fmu_name}' initialized.")

    return fmus


def init_models(
    model_classes: co.ModelClasses,
    start_values: co.StartValues,
) -> dict[str, System]:
    """Initialize python models as a System object and store them in a dictionary.

    Args:
        model_classes (ModelClasses): Dictionary which defines which Python Models
            should be simulated.
        start_values (StartValues): Dictionary which defines start values for the
            systems.

    Returns:
        dict[str, System]: key -> python model name; value -> System instance
    """

    models: dict[str, System] = {}
    for model_name, model_class in model_classes.items():
        _start_values = start_values.get(model_name) or {}
        model_instance = model_class()
        model_instance.initialize(_start_values)
        system = System(model_instance, model_name)
        models[model_name] = system
        logging.info(f"Python Model '{model_name}' initialized.")

    return models


def init_connections(connections_config: co.ConnectionsConfig) -> list[Connection]:
    """Initialize all the connections.

    Args:
        connections_config (ConnectionsConfig):
            Defines how all systems are connected.

    Returns:
        list[Connection]: List of Connections.
    """
    all_connections: list[Connection] = []

    for this_system_name, connections in connections_config.items():
        for con in connections:
            this_parameter_name = con[co.ConnectionKeys.INPUT_PARAMETER.value]
            this_connection_point = SystemParameter(
                this_system_name, this_parameter_name
            )
            other_system_name = con[co.ConnectionKeys.CONNECTED_SYSTEM.value]
            other_parameter_name = con[co.ConnectionKeys.OUTPUT_PARAMETER.value]
            other_connection_point = SystemParameter(
                other_system_name, other_parameter_name
            )
            connection = Connection(this_connection_point, other_connection_point)
            all_connections.append(connection)

    logging.info("Connections initialized.")

    return all_connections


def init_parameter_list(parameters_to_log: co.ParametersToLog) -> list[SystemParameter]:
    """Initialize all parameters that should be logged.

    Args:
        parameters_to_log (ParametersToLog): Defines which
            parameters should be logged.

    Returns:
        list[SystemParameter]: List of system parameters that should be
        logged.
    """
    log: list[SystemParameter] = []

    for system_name, parameter_names in parameters_to_log.items():
        for parameter_name in parameter_names:
            parameter_to_log = SystemParameter(system_name, parameter_name)
            log.append(parameter_to_log)

    return log


def _validate_input(
    stop_time: float,
    step_size: float,
    fmu_paths: co.FmuPaths | None,
    model_classes: co.ModelClasses | None,
    connections_config: co.ConnectionsConfig | None,
    parameters_to_log: co.ParametersToLog | None,
    logging_step_size: float | None,
    start_values: co.StartValues | None,
) -> None:
    utils.check_type(stop_time, "stop_time", Real)
    utils.check_type(step_size, "step_size", Real)

    if stop_time <= 0:
        raise ValueError(f"'stop_time' is {stop_time}; expected > 0")

    if step_size <= 0 or step_size >= stop_time:
        raise ValueError(f"'step_size' is {step_size}; expected (0, {stop_time})")

    if not fmu_paths and not model_classes:
        raise ValueError(
            "'fmu_paths' and 'model_classes' are empty; "
            "expected at least one not to be empty"
        )

    fmu_names = _validate_fmu_paths(fmu_paths)
    model_names = _validate_model_classes(model_classes)

    all_system_names = fmu_names + model_names

    if len(set(all_system_names)) < len(all_system_names):
        raise ValueError("Duplicate names in system infos.")

    _validate_connection_config(connections_config, all_system_names)

    if parameters_to_log is not None:
        _validate_parameters_to_log(parameters_to_log, all_system_names)

    if logging_step_size is not None:
        _validate_logging_step_size(logging_step_size, step_size)

    if start_values is not None:
        _validate_start_values(start_values, all_system_names)


def _validate_fmu_paths(fmu_paths: Optional[co.FmuPaths]) -> list[str]:
    if fmu_paths is None:
        return []

    utils.check_type(fmu_paths, "fmu_paths", dict)

    fmu_names: list[str] = []

    for fmu_name, fmu_path in fmu_paths.items():
        utils.check_type(
            fmu_path, f"value of key {fmu_name} in 'fmu_paths", (str, Path)
        )
        fmu_names.append(fmu_name)

    return fmu_names


def _validate_model_classes(model_classes: co.ModelClasses | None) -> list[str]:
    if model_classes is None:
        return []

    utils.check_type(model_classes, "model_classes", dict)

    model_names: list[str] = []

    for model_name, model_class in model_classes.items():
        utils.check_type(
            model_class, f"Value to key '{model_name}' in 'model_classes", type
        )
        if not issubclass(model_class, SimulationEntity):
            raise TypeError(
                f"Value to key '{model_name}' in 'model_classes must be "
                "a subclass of 'SimulationEntity'"
            )
        model_names.append(model_name)

    return model_names


def _validate_connection_config(
    connections_config: co.ConnectionsConfig | None, system_names: list[str]
) -> None:
    if connections_config is None:
        return

    for system_name, connections in connections_config.items():
        utils.check_type(
            connections, f"value to key {system_name} in 'connections_info'", list
        )
        for connection in connections:
            utils.check_type(connection, "element in list 'connections'", dict)
            for key, value in connection.items():
                _check_key_exists(key, connection, system_name)
                utils.check_type(
                    value,
                    f"Value to key '{key}' in connections"
                    f"specified for system {system_name}",
                    str,
                )
            connected_system = connection[co.ConnectionKeys.CONNECTED_SYSTEM.value]
            if connected_system not in system_names:
                raise ValueError(
                    f"System '{connected_system}' specified "
                    "in connections doesn't exist."
                )


def _check_key_exists(key: str, connection: co.Connection, system_name: str) -> None:
    if key not in connection:
        raise KeyError(
            f"missing key '{key}' in connections specified for system '{system_name}'"
        )


def _validate_parameters_to_log(
    parameters_to_log: co.ParametersToLog, system_names: list[str]
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


def _validate_logging_step_size(logging_step_size: float, step_size: float) -> None:
    utils.check_type(logging_step_size, "logging_step_size", Real)

    if not round(logging_step_size / step_size, 10).is_integer():
        raise ValueError(
            "'logging_step_size' must be a multiple of the chosen 'step_size'"
        )


def _validate_start_values(
    start_values: co.StartValues, all_system_names: list[str]
) -> None:
    utils.check_type(start_values, "start_values", dict)

    for name in start_values:
        if name not in all_system_names:
            raise ValueError(
                f"System name '{name}' is defined in 'start_values', "
                "but does not exist."
            )
