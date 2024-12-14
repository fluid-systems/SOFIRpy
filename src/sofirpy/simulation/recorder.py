from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np
import numpy.typing as npt
import pandas as pd

import sofirpy.common as co
from sofirpy.simulation.components import System, SystemParameter


class BaseRecorder(ABC):
    def __init__(
        self,
        parameters_to_log: list[SystemParameter],
        systems: dict[str, System],
        recorder_config: dict[str, Any] | None = None,
    ):
        self.parameters_to_log = parameters_to_log
        self.systems = systems
        self.recorder_config = recorder_config

    @abstractmethod
    def record(self, time: float, time_step: int) -> None:
        """Record specified parameters of the systems.

        Args:
            time (float): Current simulation time
            time_step (int): Current time step
        """

    @abstractmethod
    def to_pandas(self) -> pd.DataFrame: ...

    def get_log_name(self, system_name: str, parameter_name: str) -> str:
        """Return the log name of a parameter.

        To avoid name clashes, the log name is a combination of the system name
        and the parameter name.

        Args:
            system_name (str): Name of the system
            parameter_name (str): Name of the parameter

        Returns:
            str: Full name of the parameter
        """
        return f"{system_name}.{parameter_name}"

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
            dtypes[self.get_log_name(system_name, parameter_name)] = dtype
        return dtypes


class VariableSizeRecorder(BaseRecorder):
    def __init__(
        self, parameters_to_log: list[SystemParameter], systems: dict[str, System]
    ) -> None:
        super().__init__(parameters_to_log, systems)
        self.log = self._init_log()

    def _init_log(self) -> dict[str, list[co.ParameterValue]]:
        log: dict[str, list[co.ParameterValue]] = {}
        log["time"] = []
        for system_parameter in self.parameters_to_log:
            log[
                self.get_log_name(system_parameter.system_name, system_parameter.name)
            ] = []
        return log

    def record(self, time: float, time_step: int) -> None:
        """Record specified parameters of the systems.

        Args:
            time (float): Current simulation time
            time_step (int): Current time step
        """
        self.log["time"].append(time)
        for system_parameter in self.parameters_to_log:
            value = self.systems[
                system_parameter.system_name
            ].simulation_entity.get_parameter_value(system_parameter.name)
            log_name = self.get_log_name(
                system_parameter.system_name, system_parameter.name
            )
            self.log[log_name].append(value)

    def to_pandas(self) -> pd.DataFrame:
        """Convert the logged data to a pandas DataFrame.

        Returns:
            pd.DataFrame: Logged data as a pandas DataFrame
        """
        dtypes = self.get_dtypes()
        return pd.DataFrame(self.log).astype(dtypes)


class FixedSizedRecorder(BaseRecorder):
    def __init__(
        self,
        parameters_to_log: list[SystemParameter],
        systems: dict[str, System],
        recorder_config: dict[str, Any] | None = None,
    ):
        super().__init__(parameters_to_log, systems, recorder_config)
        if self.recorder_config is None:
            raise ValueError(
                "For FixedSizeRecorder 'stop_time' and 'step_size' need to be defined "
                "in the recorder_config."
            )
        self.stop_time: float = self.recorder_config["stop_time"]
        self.step_size: float = self.recorder_config["step_size"]
        self.logging_step_size: float = self.recorder_config.get(
            "logging_step_size", "step_size"
        )
        self.logging_multiple = round(self.logging_step_size / self.step_size)
        number_log_steps = int(self.stop_time / self.logging_step_size) + 1
        dtypes = self._get_numpy_dtypes()
        self.log: npt.NDArray[np.void] = np.zeros(number_log_steps, dtype=dtypes)
        self.log_step = 0

    def _get_numpy_dtypes(self) -> npt.DTypeLike:
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

    def record(self, time: float, time_step: int) -> None:
        if ((time_step + 1) % self.logging_multiple) != 0 and time_step != 0:
            return
        self.log[self.log_step][0] = time
        for i, parameter in enumerate(self.parameters_to_log, start=1):
            system_name = parameter.system_name
            system = self.systems[system_name]
            parameter_name = parameter.name
            value = system.simulation_entity.get_parameter_value(parameter_name)
            self.log[self.log_step][i] = value
        self.log_step += 1

    def to_pandas(self) -> pd.DataFrame:
        """Covert result numpy array to DataFrame.
        Returns:
            pd.DataFrame: Results as DataFrame. Columns are named as specified in the
            get_log_name method. By default '<system_name>.<parameter_name>'.
        """
        return pd.DataFrame(self.log)
