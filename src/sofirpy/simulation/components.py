"""This module allows to co-simulate multiple fmus and models written in python."""

from __future__ import annotations

from dataclasses import dataclass

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
