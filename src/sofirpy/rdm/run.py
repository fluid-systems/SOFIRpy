from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd
from typing_extensions import Self

from sofirpy.rdm.run_group import RunGroup, SimulationConfig
from sofirpy.simulation.simulation import ModelInstances, simulate


@dataclass
class Run:
    run_group: RunGroup

    @property
    def run_name(self) -> str:
        return self.run_group.run_name

    @property
    def simulation_results(self) -> Optional[pd.DataFrame]:
        return self.run_group.simulation_group.time_series.data

    @classmethod
    def from_hdf5(cls, hdf5_path: Path, run_name: str) -> Self:
        return cls(RunGroup.from_hdf5(hdf5_path, run_name))

    @classmethod
    def from_config(
        cls,
        run_name: str,
        config_path: Path,
        model_instances: Optional[ModelInstances] = None,
    ) -> Self:
        return cls(RunGroup.from_config(run_name, config_path, model_instances))

    def simulate(self) -> None:
        _results = simulate(**self.run_group.simulation_and_model_config)
        if isinstance(_results, tuple):
            results, units = _results
            self.run_group.store_simulation_results(results, units)
            return
        self.run_group.store_simulation_results(_results, None)

    def to_hdf5(self, hdf5_path: Path) -> None:
        if self.simulation_results is None:
            raise ValueError(
                "No simulation performed"
            )  # TODO allow the user to store before doing a simulation?
        self.run_group.to_hdf5(hdf5_path)
