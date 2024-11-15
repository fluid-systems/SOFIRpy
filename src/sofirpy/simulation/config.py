import pathlib as pl

import pydantic
from typing_extensions import Self

import sofirpy.common as co


class BaseSimulationConfig(pydantic.BaseModel):
    fmu_paths: dict[str, pl.Path]
    custom_model_classes: co.SimulationEntityMapping
    connections: co.ConnectionsConfig
    init_configs: co.InitConfigs

    @property
    def system_names(self) -> set[str]:
        return set(self.custom_model_classes) | set(self.fmu_paths)

    @pydantic.field_validator("fmu_paths", mode="before")
    @classmethod
    def validate_fmu_paths_exist(cls, fmu_paths: co.FmuPaths) -> dict[str, pl.Path]:
        _fmu_paths: dict[str, pl.Path] = {
            name: pl.Path(path) for name, path in fmu_paths.items()
        }
        for name, path in _fmu_paths.items():
            if not path.exists():
                raise FileNotFoundError(f"FMU {name!r} not found at {path}")
        return _fmu_paths

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
        system_names = list(self.custom_model_classes) + list(self.fmu_paths)
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
    def check_systems_in_init_config_exists(self) -> Self:
        for system_name in self.init_configs:
            if system_name not in self.system_names:
                raise ValueError(
                    f"System {system_name!r} in init_configs does not exist."
                )
        return self


class ExtendedSimulationConfig(pydantic.BaseModel):
    system_names: set[str]
    stop_time: float = pydantic.Field(ge=0.0)
    step_size: float = pydantic.Field(gt=0.0)
    logging_step_size: float = pydantic.Field(gt=0.0)
    start_time: float = 0.0
    parameters_to_log: co.ParametersToLog

    @pydantic.model_validator(mode="after")
    def check_system_in_parameters_to_log_exists(self) -> Self:
        for system_name in self.parameters_to_log:
            if system_name not in self.system_names:
                raise ValueError(
                    f"System {system_name!r} in parameters_to_log does not exist."
                )
        return self

    @pydantic.model_validator(mode="after")
    def check_logging_step_size_is_multiple_of_step_size(self) -> Self:
        if not round(self.logging_step_size / self.step_size, 10).is_integer():
            raise ValueError(
                "'logging_step_size' must be a multiple of the chosen 'step_size'",
            )
        return self
