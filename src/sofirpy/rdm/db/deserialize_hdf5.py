from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np
import pandas as pd

import sofirpy.rdm.db.run_to_hdf5 as rdm_hdf5
import sofirpy.rdm.run as rdm_run


class Deserializer(ABC):
    @staticmethod
    @abstractmethod
    def deserialize(run_group: rdm_hdf5.Group, *args, **kwargs) -> Any:
        ...


class RunMeta(Deserializer):
    @staticmethod
    def deserialize(run_group: rdm_hdf5.Group) -> rdm_run._RunMeta:
        return rdm_run._RunMeta(**run_group.attribute.attributes)


class SimulationConfig(Deserializer):
    @staticmethod
    def deserialize(run_group: rdm_hdf5.Group) -> rdm_run._SimulationConfig:
        simulation_results_group = run_group.get_group("simulation_results")
        return rdm_run._SimulationConfig(
            **simulation_results_group.attribute.attributes
        )


class Results(Deserializer):
    @staticmethod
    def deserialize(run_group: rdm_hdf5.Group) -> rdm_run._Results:
        simulation_results_group = run_group.get_group("simulation_results")
        _time_series = simulation_results_group.datasets.time_series.data
        time_series = pd.DataFrame.from_records(_time_series)
        units = simulation_results_group.datasets.time_series.attribute.attributes
        return rdm_run._Results(time_series, units)


class Models(Deserializer):
    @staticmethod
    def deserialize(
        run_group: rdm_hdf5.Group, model_storage_group: rdm_hdf5.Group
    ) -> rdm_run._Models:
        ...
