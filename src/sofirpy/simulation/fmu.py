"""Module containing the Fmu class."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

from fmpy import extract, read_model_description
from fmpy.fmi2 import FMU2Slave
from fmpy.simulation import (
    apply_start_values,
    settable_in_initialization_mode,
    settable_in_instantiated,
)

import sofirpy.common as co
from sofirpy.simulation.simulation_entity import SimulationEntity

SetterFunction = Callable[[list[int], list[co.ParameterValue]], None]
GetterFunction = Callable[[list[int]], list[co.ParameterValue]]


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

    def initialize(self, start_values: dict[str, co.StartValue]) -> None:
        """Initialize the fmu.

        Args:
            start_time (float, optional): start time. Defaults to 0.
        """
        self.model_description = read_model_description(self.fmu_path)
        self.model_description_dict = {
            variable.name: variable
            for variable in self.model_description.modelVariables
        }
        unzip_dir = extract(self.fmu_path)
        self.fmu = FMU2Slave(
            guid=self.model_description.guid,
            unzipDirectory=unzip_dir,
            modelIdentifier=self.model_description.coSimulation.modelIdentifier,
            instanceName="instance1",
        )
        self.setter_functions: dict[str, SetterFunction] = {
            "Boolean": self.fmu.setBoolean,
            "Integer": self.fmu.setInteger,
            "Real": self.fmu.setReal,
            "Enumeration": self.fmu.setInteger,
        }
        self.getter_functions: dict[str, GetterFunction] = {
            "Boolean": self.fmu.getBoolean,
            "Integer": self.fmu.getInteger,
            "Real": self.fmu.getReal,
        }
        self.fmu.instantiate()
        self.fmu.setupExperiment()
        not_set_start_values = apply_start_values(
            self.fmu, self.model_description, start_values, settable_in_instantiated
        )
        self.fmu.enterInitializationMode()
        not_set_start_values = apply_start_values(
            self.fmu,
            self.model_description,
            not_set_start_values,
            settable_in_initialization_mode,
        )
        if not_set_start_values:
            logging.warning(
                f"The following start values for the FMU '{self.name}' "
                f"can not be set:\n{not_set_start_values}"
            )
        self.fmu.exitInitializationMode()

    def set_parameter(
        self, parameter_name: str, parameter_value: co.ParameterValue
    ) -> None:
        var_type = self.model_description_dict[parameter_name].type
        self.setter_functions[var_type](
            [self.model_description_dict[parameter_name].valueReference],
            [parameter_value],
        )

    def get_parameter_value(self, parameter_name: str) -> co.ParameterValue:
        """Return the value of a parameter.

        Args:
            parameter_name (str): name of parameter whose value is to be
                obtained

        Returns:
            Union[int, float]: value of the parameter
        """
        var_type = self.model_description_dict[parameter_name].type
        value: co.ParameterValue = self.getter_functions[var_type](
            [self.model_description_dict[parameter_name].valueReference]
        )[0]
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

    def get_unit(self, parameter_name: str) -> str | None:
        """Return the unit of a variable.

        Args:
            parameter_name (str): Name of the variable.

        Returns:
            str: The unit of the variable.
        """
        unit: str | None = self.model_description_dict[parameter_name].unit
        return unit
