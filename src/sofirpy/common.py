"""This module contains Datatypes used across sofirpy."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Mapping, Optional, TypedDict, Union

import sofirpy.simulation.simulation_entity as simulation_entity


class ConnectionKeys(Enum):
    """Enum containing the keys that define a connection"""

    INPUT_PARAMETER = "parameter_name"
    CONNECTED_SYSTEM = "connect_to_system"
    OUTPUT_PARAMETER = "connect_to_external_parameter"


class Connection(TypedDict):
    parameter_name: str
    connect_to_system: str
    connect_to_external_parameter: str


Connections = list[Connection]
ConnectionsConfig = dict[str, Connections]

FmuPaths = Mapping[str, Union[str, Path]]
ModelClasses = Mapping[str, type[simulation_entity.SimulationEntity]]

ParametersToLog = dict[str, list[str]]
ParameterValue = Union[bool, float]

StartValue = Union[ParameterValue, tuple[ParameterValue, str]]
StartValues = dict[str, dict[str, StartValue]]

Units = dict[str, Optional[str]]
