from pathlib import Path
from typing import Union, Optional
from fmpy import extract, read_model_description
from fmpy.fmi2 import FMU2Slave
from sofirpy.simulation.simulation_entity import SimulationEntity


class Fmu(SimulationEntity):
    """Class representing a fmu."""

    def __init__(self, fmu_path: Path, step_size: float) -> None:
        """Initialize Fmu object.

        Args:
            fmu_path (Path): path to the fmu
            step_size (float): step size of the simulation
        """
        self.fmu_path = fmu_path
        self.step_size = step_size

    @property
    def fmu_path(self) -> Path:
        """Path to the fmu.

        Returns:
            Path: Path to the fmu.
        """
        return self._fmu_path

    @fmu_path.setter
    def fmu_path(self, fmu_path: Path) -> None:
        """Set the fmu path.

        Args:
            fmu_path (str): The path to the fmu.

        Raises:
            FileNotFoundError: fmu_path doesn't exist
        """
        if not fmu_path.exists():
            raise FileNotFoundError(f"The path '{fmu_path}' does not exist")
        self._fmu_path = fmu_path

    def initialize_fmu(self, start_time: float = 0) -> None:
        """Initialize the fmu.

        Args:
            start_time (float, optional): start time. Defaults to 0.
        """
        self.model_description = read_model_description(self.fmu_path)
        self.create_model_vars_dict()
        self.create_unit_vars_dict()
        unzipdir = extract(self.fmu_path)
        self.fmu = FMU2Slave(
            guid=self.model_description.guid,
            unzipDirectory=unzipdir,
            modelIdentifier=self.model_description.coSimulation.modelIdentifier,
            instanceName="instance1",
        )

        self.fmu.instantiate()
        self.fmu.setupExperiment(startTime=start_time)
        self.fmu.enterInitializationMode()
        self.fmu.exitInitializationMode()

    def create_model_vars_dict(self) -> None:
        """Create a dictionary for the variables of the fmu.

        The keys of this dictionary are the names of the variables and the
        values are the corresponding reference numbers."""
        self.model_vars = {
            variable.name: variable.valueReference
            for variable in self.model_description.modelVariables
        }

    def create_unit_vars_dict(self) -> None:
        """Create a dictionary for the units of the fmu variables.

        The keys of this dictionary are the names of the variables and the
        values are the corresponding units."""
        self.unit_vars: dict[str, Optional[str]] = {
            variable.name: variable.unit
            for variable in self.model_description.modelVariables
        }

    def set_input(self, input_name: str, input_value: Union[float, int]) -> None:
        """Set the value of an input parameter.

        Args:
            input_name (str): name of the parameter that should be set
            input_value (Union[float, int]): value to which the parameter is to
                be set
        """
        self.fmu.setReal([self.model_vars[input_name]], [input_value])

    def get_parameter_value(self, parameter_name: str) -> float:
        """Return the value of a parameter.

        Args:
            parameter_name (str): name of parameter whose value is to be
                obtained

        Returns:
            Union[int, float]: value of the parameter
        """
        return float(self.fmu.getReal([self.model_vars[parameter_name]])[0])

    def do_step(self, time: float) -> None:
        """Perform a simulation step.

        Args:
            time (float): current time
        """
        self.fmu.doStep(
            currentCommunicationPoint=time, communicationStepSize=self.step_size
        )

    def conclude_simulation_process(self) -> None:
        """Conclude the simulation process of the fmu."""
        self.fmu.terminate()
        self.fmu.freeInstance()

    def get_unit(self, parameter_name: str) -> Optional[str]:
        """Return the unit of a variable.

        Args:
            parameter_name (str): Name of the variable.

        Returns:
            str: The unit of the variable.
        """
        return self.unit_vars[parameter_name]
