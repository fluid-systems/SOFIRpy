import pathlib as pl

import pydantic
from typing_extensions import Self

import sofirpy.common as co


class SimulationConfig(pydantic.BaseModel):
    fmu_paths: dict[str, pl.Path]
    model_classes: co.ModelClasses
    connections: co.ConnectionsConfig
    start_values: co.StartValues
    parameters_to_log: co.ParametersToLog

    @property
    def system_names(self) -> set[str]:
        return set(self.model_classes) | set(self.fmu_paths)

    @pydantic.field_validator("fmu_paths", mode="before")
    @classmethod
    def validate_fmu_paths_exist(cls, fmus_paths: co.FmuPaths) -> dict[str, pl.Path]:
        fmus_paths = {name: pl.Path(path) for name, path in fmus_paths.items()}
        for name, path in fmus_paths.items():
            if not path.exists():
                raise FileNotFoundError(f"FMU {name!r} not found at {path}")
        return fmus_paths

    @pydantic.model_validator(mode="after")
    def check_any_system_defined(self) -> Self:
        if not self.system_names:
            raise ValueError(
                "'fmu_paths' and 'model_classes' are empty; "
                "expected at least one not to be empty",
            )
        return self

    @pydantic.model_validator(mode="after")
    def check_no_duplicate_system_names(self) -> Self:
        system_names = list(self.model_classes) + list(self.fmu_paths)
        if len(system_names) != len(set(system_names)):
            raise ValueError("Duplicate system names found")
        return self

    @pydantic.model_validator(mode="after")
    def check_system_in_connection_exists(self) -> Self:
        for system_name, connections in self.connections.items():
            if system_name not in self.system_names:
                raise ValueError(
                    f"System {system_name!r} in connections does not exist."
                )
            for connection in connections:
                connected_system = connection[co.ConnectionKeys.CONNECTED_SYSTEM.value]
                if connected_system not in self.system_names:
                    raise ValueError(
                        f"System {connected_system!r} in connections does not exist."
                    )
        return self

    @pydantic.model_validator(mode="after")
    def check_system_in_parameters_to_log_exists(self) -> Self:
        for system_name in self.parameters_to_log:
            if system_name not in self.system_names:
                raise ValueError(
                    f"System {system_name!r} in parameters_to_log does not exist."
                )
        return self

    @pydantic.model_validator(mode="after")
    def check_system_in_start_values_exists(self) -> Self:
        for system_name in self.start_values:
            if system_name not in self.system_names:
                raise ValueError(
                    f"System {system_name!r} in start_values does not exist."
                )
        return self
