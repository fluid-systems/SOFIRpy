from abc import ABC, abstractmethod
from typing import Union


class SimulationEntity(ABC):
    """Abstract object representing a simulation entity."""

    @abstractmethod
    def set_input(self, input_name: str, input_value: Union[float, int]):
        """Set the value of an input parameter.

        Args:
            input_name (str): name of the parameter that should be set
            input_value (Union[float, int]): value to which the parameter
                is to be set
        """

    @abstractmethod
    def get_parameter_value(self, parameter_name: str) -> Union[int, float]:
        """Return the value of a parameter.

        Args:
            parameter_name (str): name of parameter whose value is to be
                obtained

        Returns:
            Union[int, float]: value of the parameter
        """

    @abstractmethod
    def do_step(self, time: float):
        """Perform simulation entity calculation and set parameters accordingly.

        Args:
            time (float): current simulation time
        """
