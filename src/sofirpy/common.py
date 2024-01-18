"""This module contains Datatypes used across sofirpy."""

from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from pathlib import Path
from typing import Optional, TypedDict, Union

from typing_extensions import TypeAlias

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


Connections: TypeAlias = list[Connection]
ConnectionsConfig: TypeAlias = dict[str, Connections]

FmuPaths: TypeAlias = Mapping[str, Union[str, Path]]
ModelClasses: TypeAlias = Mapping[str, type[simulation_entity.SimulationEntity]]

ParametersToLog: TypeAlias = dict[str, list[str]]
ParameterValue: TypeAlias = Union[bool, float]

StartValue: TypeAlias = Union[ParameterValue, tuple[ParameterValue, str]]
StartValues: TypeAlias = dict[str, dict[str, StartValue]]

Units: TypeAlias = dict[str, Optional[str]]
