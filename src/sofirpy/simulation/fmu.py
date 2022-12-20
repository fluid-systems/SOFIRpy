"""Module containing the Fmu class."""
from pathlib import Path
from typing import Optional, Callable

from fmpy import extract, read_model_description
from fmpy.fmi2 import FMU2Slave
from fmpy.simulation import settable_in_initialization_mode, settable_in_instantiated

from sofirpy.simulation.simulation_entity import SimulationEntity, ParameterValue


SetterFunction = Callable[[list[int], list[ParameterValue]], None]
GetterFunction = Callable[[list[int]], list[ParameterValue]]

class Fmu(SimulationEntity):
    """Class representing a fmu."""

    def __init__(self, fmu_path: Path, name: str, step_size: float) -> None:
        """Initialize Fmu object.

        Args:
            fmu_path (Path): path to the fmu
            step_size (float): step size of the simulation
        """
        self.fmu_path = fmu_path
        self.name = name
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

    def initialize(
        self,
        start_values: Optional[dict[str, ParameterValue]] = None
        ) -> None:
        """Initialize the fmu.

        Args:
            start_time (float, optional): start time. Defaults to 0.
        """
        self.model_description = read_model_description(self.fmu_path)
        self.model_description_dict = {
            variable.name: variable
            for variable in self.model_description.modelVariables
        }
        self.model_vars = {
            variable.name: variable.valueReference
            for variable in self.model_description.modelVariables
        }
        self.create_model_vars_dict()
        self.create_unit_vars_dict()
        self.create_var_type_dict()
        unzipdir = extract(self.fmu_path)
        self.fmu = FMU2Slave(
            guid=self.model_description.guid,
            unzipDirectory=unzipdir,
            modelIdentifier=self.model_description.coSimulation.modelIdentifier,
            instanceName="instance1",
        )
        self.setter_functions: dict[str, SetterFunction] = {
            "Boolean": self.fmu.setBoolean,
            "Integer": self.fmu.setInteger,
            "Real": self.fmu.setReal,
            "Enumeration": self.fmu.setInteger
        }
        self.getter_functions: dict[str, GetterFunction] = {
            "Boolean": self.fmu.getBoolean,
            "Integer": self.fmu.getInteger,
            "Real": self.fmu.getReal,
        }
        self.fmu.instantiate()
        self.fmu.setupExperiment()
        if start_values is None:
            start_values = {}
        # start values are set before and after entering Initialization mode
        self.init_mode = False
        self.apply_start_values(start_values)
        self.fmu.enterInitializationMode()
        self.init_mode = True
        self.apply_start_values(start_values)
        if start_values:
            print(f"Not possible to set the following start values in FMU '{self.name}':")
            print(", ".join(start_values.keys()) + "\n")
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

    def create_var_type_dict(self) -> None:

        self.var_types: dict[str, str] = {
            variable.name: variable.type
            for variable in self.model_description.modelVariables
        }

    def apply_start_values(self, start_values: dict[str, ParameterValue]) -> None:

        check_settable = settable_in_initialization_mode
        if not self.init_mode:
            check_settable = settable_in_instantiated

        start_values_applied: list[str] = []

        for parameter_name, parameter_value in start_values.items():

            variable = self.model_description_dict[parameter_name]
            if not check_settable(variable):
                continue
            self.set_parameter(
                parameter_name, parameter_value
            )
            start_values_applied.append(parameter_name)

        [start_values.pop(parameter_name) for parameter_name in start_values_applied]

    def set_input(self, input_name: str, input_value: ParameterValue) -> None:
        """Set the value of an input parameter.

        Args:
            input_name (str): name of the parameter that should be set
            input_value (ParameterValue): value to which the parameter is to
                be set
        """
        self.set_parameter(input_name, input_value)

    def set_parameter(self, parameter_name: str, parameter_value: ParameterValue) -> None:

        var_type = self.var_types[parameter_name]
        self.setter_functions[var_type]([self.model_vars[parameter_name]], [parameter_value])

    def get_parameter_value(self, parameter_name: str) -> ParameterValue:
        """Return the value of a parameter.

        Args:
            parameter_name (str): name of parameter whose value is to be
                obtained

        Returns:
            Union[int, float]: value of the parameter
        """
        var_type = self.var_types[parameter_name]
        value: ParameterValue = self.getter_functions[var_type]([self.model_vars[parameter_name]])[0]
        return value

    def do_step(self, time: float) -> None:
        """Perform a simulation step.

        Args:
            time (float): current time
        """
        self.fmu.doStep(
            currentCommunicationPoint=time, communicationStepSize=self.step_size
        )

    def conclude_simulation(self) -> None:
        """Conclude the simulation process of the FMU."""
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
