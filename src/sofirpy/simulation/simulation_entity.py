"""Module containing abstract class SimulationEntity"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import sofirpy.common as co


class SimulationEntity(ABC):
    """Abstract object representing a simulation entity."""

    @abstractmethod
    def __init__(self, init_config: co.InitConfig) -> None:
        pass

    @abstractmethod
    def set_parameter(
        self,
        parameter_name: str,
        parameter_value: co.ParameterValue,
    ) -> None:
        """Set the value of a parameter.

        Args:
            parameter_name (str): name of the parameter that should be set
            parameter_value (ParameterValue): value to which the parameter
                is to be set
        """

    @abstractmethod
    def get_parameter_value(self, parameter_name: str) -> co.ParameterValue:
        """Return the value of a parameter.

        Args:
            parameter_name (str): name of parameter whose value is to be
                obtained

        Returns:
            ParameterValue: value of the parameter
        """

    @abstractmethod
    def do_step(self, time: float, step_size: float) -> None:
        """Perform a simulation step.

        Args:
            time (float): current simulation time
            step_size (float): simulation step_size
        """

    def get_unit(self, parameter_name: str) -> str | None:
        """Return the unit of a parameter.

        Args:
            parameter_name (str): Name of the parameter.

        Returns:
            str | None: Unit of the parameter.
        """
        return None

    def conclude_simulation(self) -> None:
        """Conclude the simulation."""
        return None

    def get_dtype_of_parameter(self, parameter_name: str) -> type[Any]:
        """Return the data type of a parameter.

        Args:
            parameter_name (str): Name of the parameter.

        Returns:
            type: Data type of the parameter.
        """
        return float
