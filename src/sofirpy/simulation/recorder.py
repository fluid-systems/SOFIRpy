from __future__ import annotations

from typing import Any

import pandas as pd

import sofirpy.common as co
from sofirpy.simulation.components import System, SystemParameter


class BaseRecorder:
    def __init__(
        self, systems: dict[str, System], parameters_to_log: list[SystemParameter]
    ) -> None:
        self.parameters_to_log = parameters_to_log
        self.systems = systems
        self.log = self._init_log()

    def get_full_name(self, system_name: str, parameter_name: str) -> str:
        """Return the full name of a parameter.

        Args:
            system_name (str): Name of the system
            parameter_name (str): Name of the parameter

        Returns:
            str: Full name of the parameter
        """
        return f"{system_name}.{parameter_name}"

    def record(self, time: float) -> None:
        """Record specified parameters of the systems.

        Args:
            time (float): Current simulation time
        """
        self.log["time"].append(time)
        for system_parameter in self.parameters_to_log:
            value = self.systems[
                system_parameter.system_name
            ].simulation_entity.get_parameter_value(system_parameter.name)
            self.log[
                self._get_full_name_from_system_parameter(system_parameter)
            ].append(value)

    def get_dtypes(self) -> dict[str, type[Any]]:
        """Get the dtypes of the parameters to be logged.

        Returns:
            dict[str, type[Any]]: Dtypes of the parameters to be logged.
            key -> full parameter name; value -> dtype
        """
        dtypes = {"time": float}
        for parameter in self.parameters_to_log:
            system_name = parameter.system_name
            system = self.systems[system_name]
            parameter_name = parameter.name
            dtype = system.simulation_entity.get_dtype_of_parameter(parameter_name)
            dtypes[self._get_full_name_from_system_parameter(parameter)] = dtype
        return dtypes

    def to_pandas(self) -> pd.DataFrame:
        """Convert the logged data to a pandas DataFrame.

        Returns:
            pd.DataFrame: Logged data as a pandas DataFrame
        """
        dtypes = self.get_dtypes()
        return pd.DataFrame(self.log).astype(dtypes)

    def _init_log(self) -> dict[str, list[co.ParameterValue]]:
        log: dict[str, list[co.ParameterValue]] = {}
        log["time"] = []
        for system_parameter in self.parameters_to_log:
            log[self._get_full_name_from_system_parameter(system_parameter)] = []
        return log

    def _get_full_name_from_system_parameter(
        self, system_parameter: SystemParameter
    ) -> str:
        return self.get_full_name(system_parameter.system_name, system_parameter.name)
