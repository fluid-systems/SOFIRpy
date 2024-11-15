"""This module contains Datatypes used across sofirpy."""

from __future__ import annotations

import os
from enum import Enum
from typing import Any, Literal, Optional, Union

from typing_extensions import TypeAlias, TypedDict

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

FilePath: TypeAlias = Union[str, os.PathLike[Any]]
FmuPaths: TypeAlias = dict[str, FilePath]

InitConfig: TypeAlias = dict[str, Any]
InitConfigs: TypeAlias = dict[str, InitConfig]
SimulationEntityMapping = dict[str, type[simulation_entity.SimulationEntity]]
ModelClasses: TypeAlias = SimulationEntityMapping

ParametersToLog: TypeAlias = dict[str, list[str]]
ParameterValue: TypeAlias = Union[bool, float, int, str, object]

StartValueConfigLabel: Literal["start_values"] = "start_values"
StartValue: TypeAlias = Union[ParameterValue, tuple[ParameterValue, str]]
StartValues: TypeAlias = dict[str, dict[str, StartValue]]

Units: TypeAlias = dict[str, Optional[str]]
