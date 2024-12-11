"""This module allows to co-simulate multiple fmus and models written in python."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Literal, overload

import numpy as np
import numpy.typing as npt
import pandas as pd
from tqdm import tqdm

import sofirpy.common as co
from sofirpy.simulation.components import Connection, System, SystemParameter
from sofirpy.simulation.config import BaseSimulationConfig, ExtendedSimulationConfig
from sofirpy.simulation.fmu import Fmu, FmuInitConfig
from sofirpy.simulation.recorder import BaseRecorder


class BaseSimulator:
    def __init__(
        self,
        fmu_paths: co.FmuPaths | None = None,
        model_classes: co.SimulationEntityMapping | None = None,
        connections_config: co.ConnectionsConfig | None = None,
        init_configs: co.InitConfigs | None = None,
        parameters_to_log: co.ParametersToLog | None = None,
        recorder: type[BaseRecorder] | None = None,
    ) -> None:
        config = BaseSimulationConfig(
            fmu_paths=fmu_paths or {},
            custom_model_classes=model_classes or {},
            connections=connections_config or {},
            init_configs=init_configs or {},
            parameters_to_log=parameters_to_log or {},
        )
        config.init_configs, fmu_classes = _extract_fmu_init_configs(
            config.fmu_paths, config.init_configs
        )
        simulation_entity_mapping = fmu_classes | config.custom_model_classes
        self.systems = init_systems(simulation_entity_mapping, config.init_configs)
        self.connections = init_connections(config.connections)
        self.parameters_to_log = init_parameter_list(config.parameters_to_log or {})
        recorder = recorder or BaseRecorder
        self.recorder = recorder(self.systems, self.parameters_to_log)
        self.time = 0
        self.step = 0

    def do_step(self, time: float, step_size: float) -> None:
        """Perform a calculation in all systems.

        Args:
            time (float): current simulation time
            step_size (float): step size of the simulation
        """
        for system in self.systems.values():
            system.simulation_entity.do_step(time, step_size)

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
                output_name,
            )
            input_system.simulation_entity.set_parameter(input_name, input_value)

    def get_parameter(self, system_name: str, parameter_name: str) -> co.ParameterValue:
        """Get the value of a parameter in a system.

        Args:
            system_name (str): name of the system
            parameter_name (str): name of the parameter

        Returns:
            float: value of the parameter
        """
        system = self.systems[system_name]
        return system.simulation_entity.get_parameter_value(parameter_name)

    def set_parameter(
        self, system_name: str, parameter_name: str, value: co.ParameterValue
    ) -> None:
        """Set the value of a parameter in a system.

        Args:
            system_name (str): name of the system
            parameter_name (str): name of the parameter
            value (float): value to set
        """
        system = self.systems[system_name]
        system.simulation_entity.set_parameter(parameter_name, value)

    def record(self) -> None:
        """Record the values of the parameters that are set to be logged."""
        self.recorder.record(self.time)

    def get_results_as_pandas_df(self) -> pd.DataFrame:
        return self.recorder.to_pandas()

    def conclude_simulation(self) -> None:
        """Conclude the simulation for all simulation entities."""
        for system in self.systems.values():
            system.simulation_entity.conclude_simulation()


class Simulator(BaseSimulator):
    """Object that performs the simulation."""

    def __init__(
        self,
        stop_time: float,
        step_size: float,
        logging_step_size: float | None = None,
        fmu_paths: co.FmuPaths | None = None,
        model_classes: co.SimulationEntityMapping | None = None,
        connections_config: co.ConnectionsConfig | None = None,
        init_configs: co.InitConfigs | None = None,
        parameters_to_log: co.ParametersToLog | None = None,
    ) -> None:
        super().__init__(
            fmu_paths,
            model_classes,
            connections_config,
            init_configs,
            parameters_to_log=parameters_to_log,
        )
        extended_simulation_config = ExtendedSimulationConfig(
            system_names=set(self.systems),
            stop_time=stop_time,
            step_size=step_size,
            logging_step_size=logging_step_size or step_size,
        )
        self.stop_time = extended_simulation_config.stop_time
        self.step_size = extended_simulation_config.step_size
        self.logging_step_size = extended_simulation_config.logging_step_size
        self.start_time = extended_simulation_config.start_time

    def simulate(
        self,
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

        Returns:
            pd.DataFrame: result DataFrame with times series of logged
            parameters
        """
        logging.info(f"Simulation stop time set to {self.stop_time} seconds.")
        logging.info(f"Simulation step size set to {self.step_size} seconds.")
        logging.info(
            f"Simulation logging step size set to {self.logging_step_size} seconds."
        )
        time_series = self.compute_time_array(
            self.stop_time, self.step_size, self.start_time
        )
        number_log_steps = int(self.stop_time / self.logging_step_size) + 1
        logging_multiple = round(self.logging_step_size / self.step_size)
        dtypes = self.get_dtypes_of_logged_parameters()
        # self.results is a structured numpy array
        self.results = np.zeros(number_log_steps, dtype=dtypes)

        logging.info("Starting simulation.")

        self.log_values(time=0, log_step=0)
        log_step = 1
        for time_step, time in enumerate(tqdm(time_series[:-1])):
            self.do_step(time, self.step_size)
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
        self,
        stop_time: float,
        step_size: float,
        start_time: float,
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

    def log_values(self, time: float, log_step: int) -> None:
        """Log parameter values that are set to be logged.

        Args:
            time (float): current simulation time
            log_step (int): current time step
        """
        self.results[log_step][0] = time

        for i, parameter in enumerate(self.parameters_to_log, start=1):
            system_name = parameter.system_name
            system = self.systems[system_name]
            parameter_name = parameter.name
            value = system.simulation_entity.get_parameter_value(parameter_name)
            self.results[log_step][i] = value

    def convert_to_data_frame(self, results: npt.NDArray[np.void]) -> pd.DataFrame:
        """Covert result numpy array to DataFrame.

        Args:
            results (npt.NDArray[np.void]): Results of the simulation.

        Returns:
            pd.DataFrame: Results as DataFrame. Columns are named as follows:
            '<system_name>.<parameter_name>'.
        """
        return pd.DataFrame(results)

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

    def get_dtypes_of_logged_parameters(self) -> npt.DTypeLike:
        """Get the dtypes of the logged parameters.

        Returns:
            np.dtypes.VoidDType: dtypes of the logged parameters
        """
        dtypes: list[tuple[str, type]] = [("time", np.float64)]
        for parameter in self.parameters_to_log:
            system_name = parameter.system_name
            system = self.systems[system_name]
            parameter_name = parameter.name
            dtype = system.simulation_entity.get_dtype_of_parameter(parameter_name)
            dtypes.append((f"{system.name}.{parameter_name}", dtype))
        return np.dtype(dtypes)


@overload
def simulate(
    stop_time: float,
    step_size: float,
    fmu_paths: co.FmuPaths | None = ...,
    model_classes: co.ModelClasses | None = ...,
    connections_config: co.ConnectionsConfig | None = ...,
    init_configs: co.InitConfigs | None = ...,
    parameters_to_log: co.ParametersToLog | None = ...,
    logging_step_size: float | None = ...,
    *,
    get_units: Literal[True],
) -> tuple[pd.DataFrame, co.Units]: ...


@overload
def simulate(
    stop_time: float,
    step_size: float,
    fmu_paths: co.FmuPaths | None = ...,
    model_classes: co.ModelClasses | None = ...,
    connections_config: co.ConnectionsConfig | None = ...,
    init_configs: co.InitConfigs | None = ...,
    parameters_to_log: co.ParametersToLog | None = ...,
    logging_step_size: float | None = ...,
    *,
    get_units: Literal[False],
) -> pd.DataFrame: ...


@overload
def simulate(
    stop_time: float,
    step_size: float,
    fmu_paths: co.FmuPaths | None = ...,
    model_classes: co.ModelClasses | None = ...,
    connections_config: co.ConnectionsConfig | None = ...,
    init_configs: co.InitConfigs | None = ...,
    parameters_to_log: co.ParametersToLog | None = ...,
    logging_step_size: float | None = ...,
) -> pd.DataFrame: ...


def simulate(
    stop_time: float,
    step_size: float,
    fmu_paths: co.FmuPaths | None = None,
    model_classes: co.ModelClasses | None = None,
    connections_config: co.ConnectionsConfig | None = None,
    init_configs: co.InitConfigs | None = None,
    parameters_to_log: co.ParametersToLog | None = None,
    logging_step_size: float | None = None,
    get_units: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, co.Units]:
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
        init_configs (co.InitConfigs | None, optional): Dictionary which defines initial
            configurations for the systems. Fmus can only have the key 'start_values'
            for specifying the start values. key -> name of the system;
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
        get_units (bool, optional): Determines whether the units of
            the logged parameter should be returned. Defaults to False.

    Returns:
        pd.DataFrame | tuple[pd.DataFrame, co.Units]:
            Result DataFrame with times series of logged parameters, units of
            logged parameters.
    """
    logging.basicConfig(
        format="Simulation::%(levelname)s::%(message)s",
        level=logging.INFO,
        force=True,
    )

    simulator = Simulator(
        fmu_paths=fmu_paths,
        model_classes=model_classes,
        connections_config=connections_config,
        init_configs=init_configs,
        parameters_to_log=parameters_to_log,
        stop_time=stop_time,
        step_size=step_size,
        logging_step_size=logging_step_size,
    )
    results = simulator.simulate()

    if get_units:
        units = simulator.get_units()
        return results, units

    return results


def init_systems(
    simulation_entity_mapping: co.SimulationEntityMapping, init_configs: co.InitConfigs
) -> dict[str, System]:
    systems: dict[str, System] = {}
    for system_name, simulation_entity_class in simulation_entity_mapping.items():
        init_config = init_configs.get(system_name, {})
        system_instance = simulation_entity_class(init_config)
        system = System(system_instance, system_name)
        systems[system_name] = system
        logging.info(f"System '{system_name}' initialized.")
    return systems


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
                this_system_name,
                this_parameter_name,
            )
            other_system_name = con[co.ConnectionKeys.CONNECTED_SYSTEM.value]
            other_parameter_name = con[co.ConnectionKeys.OUTPUT_PARAMETER.value]
            other_connection_point = SystemParameter(
                other_system_name,
                other_parameter_name,
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


def _extract_fmu_init_configs(
    fmu_paths: dict[str, Path],
    init_config: co.InitConfig,
) -> tuple[dict[str, Any], co.SimulationEntityMapping]:
    fmu_classes: co.SimulationEntityMapping = {}
    for fmu_name, fmu_path in fmu_paths.items():
        fmu_init_config: dict[str, Any] = init_config.get(fmu_name, {})
        init_config[fmu_name] = FmuInitConfig(
            fmu_path=fmu_path,
            name=fmu_name,
            start_values=fmu_init_config.get(co.StartValueConfigLabel, {}),
        ).model_dump()
        fmu_classes[fmu_name] = Fmu
    return init_config, fmu_classes
