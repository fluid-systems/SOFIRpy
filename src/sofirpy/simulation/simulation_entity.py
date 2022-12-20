"""Module containing abstract class SimulationEntity"""

from abc import ABC, abstractmethod
from typing import Optional, Union


ParameterValue = Union[bool, int, float]


class SimulationEntity(ABC):
    """Abstract object representing a simulation entity."""

    @abstractmethod
    def set_parameter(self, parameter_name: str, parameter_value: ParameterValue) -> None:
        """Set the value of a parameter.

        Args:
            parameter_name (str): name of the parameter that should be set
            parameter_value (ParameterValue): value to which the parameter
                is to be set
        """

    @abstractmethod
    def get_parameter_value(self, parameter_name: str) -> ParameterValue:
        """Return the value of a parameter.

        Args:
            parameter_name (str): name of parameter whose value is to be
                obtained

        Returns:
            ParameterValue: value of the parameter
        """

    @abstractmethod
    def do_step(self, time: float) -> None:
        """Perform a simulation step.

        Args:
            time (float): current simulation time
        """

    def initialize(self, start_values: dict[str, ParameterValue]) -> None:
        """Initialize the model"""

    def apply_start_values(self, start_values: dict[str, ParameterValue]) -> None:
        """Apply start values for parameters"""

    def get_unit(self, parameter_name: str) -> Optional[str]:
        """Return the unit of a parameter.

        Args:
            parameter_name (str): Name of the parameter.

        Returns:
            Optional[str]: Unit of the parameter.
        """

    def conclude_simulation(self) -> None:
        """Conclude the simulation."""
