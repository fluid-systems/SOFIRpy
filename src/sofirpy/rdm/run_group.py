from __future__ import annotations

import hashlib
import inspect
import json
import sys
import tempfile
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar, Optional, TypedDict, Union, cast

import cloudpickle
import numpy as np
import pandas as pd

# from pip._internal.operations import freeze
from typing_extensions import NotRequired, Self

import sofirpy
import sofirpy.rdm.run as rdm_run
from sofirpy import HDF5
from sofirpy.simulation.simulation import Connections, FmuPaths, ModelInstances, Units
from sofirpy.simulation.simulation_entity import SimulationEntity, StartValue


class Config(TypedDict):
    run_meta: rdm_run.MetaConfig
    models: dict[str, Union[ModelConfig, FmuConfig]]
    simulation_config: SimulationConfig


class MetaConfig(TypedDict):
    description: str
    keywords: list[str]
    date: str
    python_version: str
    sofirpy_version: str


class ModelConfig(TypedDict):
    start_values: NotRequired[dict[str, StartValue]]
    connections: NotRequired[Connections]
    parameters_to_log: NotRequired[list[str]]


class FmuConfig(ModelConfig):
    fmu_path: str


class SimulationConfig(TypedDict):
    stop_time: float
    step_size: float
    logging_step_size: NotRequired[float]
    get_units: NotRequired[bool]


@dataclass
class HDF5Entity(ABC):
    parent: HDF5Object

    @property
    @abstractmethod
    def path(self) -> str:
        ...


@dataclass
class HDF5Object(HDF5Entity):
    @property
    @abstractmethod
    def name(self) -> str:
        ...


@dataclass
class Group(HDF5Object):
    parent: Group


@dataclass
class TopLevelGroup(Group):
    parent: None


@dataclass
class Dataset(HDF5Object):
    parent: Group


class Attribute(HDF5Entity):
    ...


@dataclass
class RunGroup(TopLevelGroup):
    run_name: str
    _attr: Optional[RunAttr] = None
    _config_dataset: Optional[RunConfigDataset] = None
    _models_group: Optional[ModelsGroup] = None
    _simulation_group: Optional[SimulationResultsGroup] = None

    @property
    def path(self) -> str:
        return self.run_name

    @property
    def name(self) -> str:
        return self.run_name

    @property
    def attr(self) -> RunAttr:
        assert self._attr is not None
        return self._attr

    @property
    def config_dataset(self) -> RunConfigDataset:
        assert self._config_dataset is not None
        return self._config_dataset

    @property
    def models_group(self) -> ModelsGroup:
        assert self._models_group is not None
        return self._models_group

    @property
    def simulation_group(self) -> SimulationResultsGroup:
        assert self._simulation_group is not None
        return self._simulation_group

    @classmethod
    def from_run(cls, run: rdm_run.Run) -> Self:
        self = cls(run_name=run.run_name, parent=None)
        self._config_dataset = RunConfigDataset.from_run(run=run, parent=self)
        self._attr = RunAttr.from_run(run=run, parent=self)
        self._models_group = ModelsGroup.from_run(run=run, parent=self)
        self._simulation_group = SimulationResultsGroup.from_run(run=run, parent=self)
        return self

    @classmethod
    def from_hdf5(cls, hdf5_path: Path, run_name: str) -> Self:
        hdf5 = HDF5(hdf5_path)
        self = cls(run_name=run_name, parent=None)
        self._attr = RunAttr.from_hdf5(hdf5, self)
        self._config_dataset = RunConfigDataset.from_hdf5(hdf5, self)
        self._models_group = ModelsGroup.from_hdf5(hdf5, self)
        self._simulation_group = SimulationResultsGroup.from_hdf5(hdf5, self)
        return self

    def to_run(self) -> rdm_run.Run:
        run_name = self.run_name
        run_meta = rdm_run.RunMeta(**self.attr.to_dict())
        fmus = {
            fmu.name: rdm_run.Fmu(
                name=fmu.name,
                fmu_path=fmu.fmu_path,
                connections=fmu.connections_dataset.data,
                start_values=fmu.start_values_dataset.data,
                parameters_to_log=fmu.parameters_to_log_dataset.data,
            )
            for fmu in self.models_group.fmus_group.fmu_groups
        }
        python_models = {
            python_model.name: rdm_run.PythonModel(
                name=python_model.name,
                model_instance=python_model.model_instance,
                connections=python_model.connections_dataset.data,
                start_values=python_model.start_values_dataset.data,
                parameters_to_log=python_model.parameters_to_log_dataset.data,
            )
            for python_model in self.models_group.python_models_group.python_model_groups
        }
        _models = rdm_run.Models(fmus=fmus, python_models=python_models)
        simulation_config = rdm_run.SimulationConfig(
            **self.simulation_group.attr.to_dict()
        )
        results = rdm_run.Results(
            time_series=self.simulation_group.time_series.data,
            units=self.simulation_group.time_series.attr.attributes,
        )
        return rdm_run.Run(
            run_name=run_name,
            _run_meta=run_meta,
            _models=_models,
            _simulation_config=simulation_config,
            _results=results,
        )

    def to_hdf5(self, hdf5_path: Path) -> None:
        assert self.simulation_group.time_series is not None
        hdf5 = HDF5(hdf5_path)
        if not is_hdf5_initialized(hdf5):
            raise ValueError
        try:
            hdf5.create_group(self.path)
            self.attr.to_hdf5(hdf5)
            self.config_dataset.to_hdf5(hdf5)
            self.models_group.to_hdf5(hdf5)
            self.simulation_group.to_hdf5(hdf5)
        except Exception as e:
            hdf5.delete_group(self.run_name)
            raise e


@dataclass
class RunConfigDataset(Dataset):
    DATASET_NAME: ClassVar[str] = "config"
    parent: RunGroup
    data: rdm_run.Config

    @property
    def name(self) -> str:
        return self.DATASET_NAME

    @property
    def path(self) -> str:
        return f"{self.parent.parent}/{self.name}"

    @classmethod
    def from_run(cls, run: rdm_run.Run, parent: RunGroup) -> Self:
        return cls(parent=parent, data=run.get_config())

    @classmethod
    def from_hdf5(cls, hdf5: HDF5, parent: RunGroup) -> Self:
        return cls(
            parent=parent,
            data=cast(
                rdm_run.Config,
                json.loads(cast(bytes, hdf5.read_data(cls.DATASET_NAME, parent.path))),
            ),
        )

    def to_hdf5(self, hdf5: HDF5) -> None:
        hdf5.store_data(json.dumps(self.data), self.name, self.parent.path)


@dataclass
class RunAttr(Attribute):
    parent: RunGroup
    attributes: Attrs

    CONFIG_KEY = "run_meta"

    class ConfigKeys:
        DESCRIPTION = "description"
        KEYWORDS = "keywords"

    @dataclass
    class Attrs:
        description: str
        keywords: list[str]
        date: str = datetime.now().strftime("%d-%b-%Y %H:%M:%S")
        python_version: str = sys.version
        sofirpy_version: str = sofirpy.__version__

    @property
    def path(self) -> str:
        return self.parent.path

    @classmethod
    def from_run(cls, run: rdm_run.Run, parent: RunGroup) -> Self:
        return cls(parent=parent, attributes=cls.Attrs(**asdict(run._run_meta)))

    @classmethod
    def from_hdf5(cls, hdf5: HDF5, parent: RunGroup) -> Self:
        attr = hdf5.read_attributes(parent.path)
        del attr["typ"]
        return cls(parent, cls.Attrs(**attr))

    def to_hdf5(self, hdf5: HDF5) -> None:
        hdf5.append_attributes({"typ": "run"}, self.path)
        hdf5.append_attributes(cast(dict[str, Any], self.to_dict()), self.path)

    def to_dict(self) -> MetaConfig:
        return cast(MetaConfig, asdict(self.attributes))


@dataclass
class ModelsGroup(Group):
    parent: RunGroup
    _fmus_group: Optional[FmusGroup] = None
    _python_models_group: Optional[PythonModelsGroup] = None

    CONFIG_KEY = "models"
    GROUP_NAME = "models"

    @property
    def path(self) -> str:
        return f"{self.parent.path}/{self.name}"

    @property
    def name(self) -> str:
        return self.GROUP_NAME

    @property
    def fmus_group(self) -> FmusGroup:
        assert self._fmus_group is not None
        return self._fmus_group

    @property
    def python_models_group(self) -> PythonModelsGroup:
        assert self._python_models_group is not None
        return self._python_models_group

    @classmethod
    def from_run(cls, run: rdm_run.Run, parent: RunGroup) -> Self:
        self = cls(parent=parent)
        self._fmus_group = FmusGroup.from_run(run, self)
        self._python_models_group = PythonModelsGroup.from_run(run, self)
        return self

    @classmethod
    def from_hdf5(cls, hdf5: HDF5, parent: RunGroup) -> Self:
        self = cls(parent=parent)
        self._fmus_group = FmusGroup.from_hdf5(hdf5, self)
        self._python_models_group = PythonModelsGroup.from_hdf5(hdf5, self)
        return self

    def to_hdf5(self, hdf5: HDF5) -> None:
        hdf5.create_group(self.path)
        self.fmus_group.to_hdf5(hdf5)
        self.python_models_group.to_hdf5(hdf5)


@dataclass
class FmusGroup(Group):
    parent: ModelsGroup
    _fmu_groups: Optional[list[FmuGroup]] = None

    GROUP_NAME = "fmus"

    @property
    def path(self) -> str:
        return f"{self.parent.path}/{self.name}"

    @property
    def name(self) -> str:
        return self.GROUP_NAME

    @property
    def fmu_groups(self) -> list[FmuGroup]:
        assert self._fmu_groups is not None
        return self._fmu_groups

    @property
    def fmu_paths(self) -> FmuPaths:
        return {fmu.name: fmu.fmu_path for fmu in self.fmu_groups}

    @classmethod
    def from_run(cls, run: rdm_run.Run, parent: ModelsGroup) -> Self:
        self = cls(parent)
        self._fmu_groups = [
            FmuGroup.from_run(fmu, self) for fmu in run._models.fmus.values()
        ]
        return self

    @classmethod
    def from_hdf5(cls, hdf5: HDF5, parent: ModelsGroup) -> Self:
        self = cls(parent)
        fmu_groups = []
        for group_name in hdf5.get_group_names(self.path):
            fmu_groups.append(FmuGroup.from_hdf5(hdf5, group_name, self))
        self._fmu_groups = fmu_groups
        return self

    def to_hdf5(self, hdf5: HDF5) -> None:
        hdf5.create_group(self.path)
        for fmu_group in self.fmu_groups:
            fmu_group.to_hdf5(hdf5)


@dataclass
class PythonModelsGroup(Group):
    parent: ModelsGroup
    _python_model_groups: Optional[list[PythonModelGroup]] = None
    GROUP_NAME = "python_models"

    @property
    def path(self) -> str:
        return f"{self.parent.path}/{self.GROUP_NAME}"

    @property
    def name(self) -> str:
        return self.GROUP_NAME

    @property
    def python_model_groups(self) -> list[PythonModelGroup]:
        assert self._python_model_groups is not None
        return self._python_model_groups

    @property
    def model_instances(self) -> ModelInstances:
        return {
            python_model_group.name: python_model_group.model_instance
            for python_model_group in self.python_model_groups
        }

    @classmethod
    def from_run(cls, run: rdm_run.Run, parent: ModelsGroup) -> Self:
        self = cls(parent)
        self._python_model_groups = [
            PythonModelGroup.from_run(python_model, self)
            for python_model in run._models.python_models.values()
        ]
        return self

    @classmethod
    def from_hdf5(cls, hdf5: HDF5, parent: ModelsGroup) -> Self:
        self = cls(parent)
        python_model_groups = []
        for group_name in hdf5.get_group_names(self.path):
            python_model_groups.append(
                PythonModelGroup.from_hdf5(hdf5, group_name, self)
            )
        self._python_model_groups = python_model_groups
        return self

    def to_hdf5(self, hdf5: HDF5) -> None:
        hdf5.create_group(self.path)
        for model_group in self.python_model_groups:
            model_group.to_hdf5(hdf5)


@dataclass
class ModelDataset(Dataset):
    DATASET_NAME: ClassVar[str]
    CONFIG_KEY: ClassVar[str]
    parent: Union[PythonModelGroup, FmuGroup]
    data: Optional[Any]

    @property
    def path(self) -> str:
        return f"{self.parent.path}/{self.DATASET_NAME}"

    @property
    def name(self) -> str:
        return self.DATASET_NAME

    @classmethod
    def from_hdf5(cls, hdf5: HDF5, parent: Union[PythonModelGroup, FmuGroup]) -> Self:
        return cls(
            parent,
            json.loads(
                cast(bytes, hdf5.read_data(cls.DATASET_NAME, parent.path)).decode(
                    "utf-8"
                )
            )["data"],
        )

    def to_hdf5(self, hdf5: HDF5) -> None:
        hdf5.store_data(
            json.dumps({"data": self.data}),
            data_name=self.DATASET_NAME,
            group_path=self.parent.path,
        )


@dataclass
class ConnectionDataset(ModelDataset):
    data: Connections

    DATASET_NAME = "connections"
    CONFIG_KEY = "connections"

    @classmethod
    def from_run(
        cls, model: rdm_run.Model, parent: Union[PythonModelGroup, FmuGroup]
    ) -> Self:
        return cls(parent=parent, data=model.connections or [])


@dataclass
class StartValuesDataset(ModelDataset):
    data: dict[str, StartValue]

    DATASET_NAME = "start_values"
    CONFIG_KEY = "start_values"

    @classmethod
    def from_run(
        cls, model: rdm_run.Model, parent: Union[PythonModelGroup, FmuGroup]
    ) -> Self:
        return cls(parent=parent, data=model.start_values or {})


@dataclass
class ParametersToLogDataset(ModelDataset):
    data: list[str]

    DATASET_NAME = "parameters_to_log"
    CONFIG_KEY = "parameters_to_log"

    @classmethod
    def from_run(
        cls, model: rdm_run.Model, parent: Union[PythonModelGroup, FmuGroup]
    ) -> Self:
        return cls(parent=parent, data=model.parameters_to_log or [])


@dataclass
class FmuReferenceDataset(ModelDataset):
    data: str
    fmu_content: Optional[bytes] = None  # TODO maybe move this to FmuStorageDataset
    DATASET_NAME = "reference"

    CONFIG_KEY = "fmu_path"

    @classmethod
    def from_run(cls, model: rdm_run.Fmu, parent: FmuGroup) -> Self:
        with open(model.fmu_path, "rb") as fmu:
            fmu_content = fmu.read()
        fmu_hash = hashlib.sha256(fmu_content).hexdigest()
        return cls(parent=parent, data=fmu_hash, fmu_content=fmu_content)

    @classmethod
    def from_hdf5(cls, hdf5: HDF5, parent: FmuGroup) -> Self:
        fmu_hash = cast(bytes, hdf5.read_data(cls.DATASET_NAME, parent.path)).decode(
            "utf-8"
        )
        fmu_content = ModelStorageGroup.from_hdf5(
            hdf5
        ).fmus_storage_group.get_fmu_content_from_reference(hdf5, fmu_hash)
        return cls(parent, data=fmu_hash, fmu_content=fmu_content)

    def write_fmu_content_to_tmp_dir(self) -> Path:
        tmp_dir = Path(tempfile.mkdtemp())
        fmu_path = tmp_dir / f"{self.parent.model_name}.fmu"
        fmu_path.touch()
        assert self.fmu_content is not None
        with open(fmu_path, "wb") as fmu_file:
            fmu_file.write(self.fmu_content)
        self.fmu_content = None
        return fmu_path

    def to_hdf5(self, hdf5: HDF5) -> None:
        fmus_storage_group = ModelStorageGroup.from_hdf5(hdf5).fmus_storage_group
        hdf5.store_data(self.data, self.name, self.parent.path)
        if self.data in fmus_storage_group.get_references():
            return
        assert self.fmu_content is not None
        fmus_storage_group.store_fmu(hdf5, self.fmu_content, self.data)
        self.fmu_content = None  # for memory purposes


@dataclass
class PythonModelReferenceDataset(ModelDataset):
    data: str
    pickled_python_model: Optional[bytes] = None
    DATASET_NAME = "reference"

    @classmethod
    def from_run(cls, model: rdm_run.PythonModel, parent: PythonModelGroup) -> Self:
        cloudpickle.register_pickle_by_value(inspect.getmodule(model.model_instance))
        pickled_python_model = cloudpickle.dumps(model.model_instance)
        model_hash = hashlib.sha256(pickled_python_model).hexdigest()
        return cls(
            parent=parent, data=model_hash, pickled_python_model=pickled_python_model
        )

    @classmethod
    def from_hdf5(cls, hdf5: HDF5, parent: PythonModelGroup) -> Self:
        model_hash = cast(bytes, hdf5.read_data(cls.DATASET_NAME, parent.path)).decode(
            "utf-8"
        )
        pickled_python_model = ModelStorageGroup.from_hdf5(
            hdf5
        ).python_models_storage_group.get_pickled_model_by_reference(hdf5, model_hash)
        return cls(parent, data=model_hash, pickled_python_model=pickled_python_model)

    def unpickle_python_model(self) -> SimulationEntity:
        return cast(SimulationEntity, cloudpickle.loads(self.pickled_python_model))

    def to_hdf5(self, hdf5: HDF5) -> None:
        assert self.pickled_python_model is not None
        python_models_storage_group = ModelStorageGroup.from_hdf5(
            hdf5
        ).python_models_storage_group
        hdf5.store_data(self.data, self.name, self.parent.path)
        if self.data in python_models_storage_group.get_references():
            return
        python_models_storage_group.store_model(
            hdf5, self.pickled_python_model, self.data
        )
        self.pickled_python_model = None  # for memory purposes


@dataclass
class ModelGroup(Group):
    parent: Union[FmusGroup, PythonModelsGroup]
    model_name: str
    _connections_dataset: Optional[ConnectionDataset] = None
    _start_values_dataset: Optional[StartValuesDataset] = None
    _parameters_to_log_dataset: Optional[ParametersToLogDataset] = None

    @property
    def path(self) -> str:
        return f"{self.parent.path}/{self.name}"

    @property
    def name(self) -> str:
        return self.model_name

    @property
    def connections_dataset(self) -> ConnectionDataset:
        assert self._connections_dataset is not None
        return self._connections_dataset

    @property
    def start_values_dataset(self) -> StartValuesDataset:
        assert self._start_values_dataset is not None
        return self._start_values_dataset

    @property
    def parameters_to_log_dataset(self) -> ParametersToLogDataset:
        assert self._parameters_to_log_dataset is not None
        return self._parameters_to_log_dataset

    def to_hdf5(self, hdf5: HDF5) -> None:
        hdf5.create_group(self.path)
        self.connections_dataset.to_hdf5(hdf5)
        self.start_values_dataset.to_hdf5(hdf5)
        self.parameters_to_log_dataset.to_hdf5(hdf5)


@dataclass
class FmuGroup(ModelGroup):
    _reference_dataset: Optional[FmuReferenceDataset] = None
    _fmu_path: Optional[Path] = None

    @property
    def reference_dataset(self) -> FmuReferenceDataset:
        assert self._reference_dataset is not None
        return self._reference_dataset

    @property
    def fmu_path(self) -> Path:
        assert self._fmu_path is not None
        return self._fmu_path

    @classmethod
    def from_run(cls, model: rdm_run.Fmu, parent: FmusGroup) -> Self:
        self = cls(parent=parent, model_name=model.name, _fmu_path=model.fmu_path)
        self._connections_dataset = ConnectionDataset.from_run(model, self)
        self._start_values_dataset = StartValuesDataset.from_run(model, self)
        self._parameters_to_log_dataset = ParametersToLogDataset.from_run(model, self)
        self._reference_dataset = FmuReferenceDataset.from_run(model, self)
        return self

    @classmethod
    def from_hdf5(cls, hdf5: HDF5, group_name: str, parent: FmusGroup) -> Self:
        self = cls(parent=parent, model_name=group_name)
        self._connections_dataset = ConnectionDataset.from_hdf5(hdf5, self)
        self._start_values_dataset = StartValuesDataset.from_hdf5(hdf5, self)
        self._parameters_to_log_dataset = ParametersToLogDataset.from_hdf5(hdf5, self)
        self._reference_dataset = FmuReferenceDataset.from_hdf5(hdf5, self)
        self._fmu_path = self.reference_dataset.write_fmu_content_to_tmp_dir()
        return self

    def to_hdf5(self, hdf5: HDF5) -> None:
        super().to_hdf5(hdf5)
        self.reference_dataset.to_hdf5(hdf5)


@dataclass
class PythonModelGroup(ModelGroup):
    _reference_dataset: Optional[PythonModelReferenceDataset] = None
    _model_instance: Optional[SimulationEntity] = None

    @property
    def reference_dataset(self) -> PythonModelReferenceDataset:
        assert self._reference_dataset is not None
        return self._reference_dataset

    @property
    def model_instance(self) -> SimulationEntity:
        assert self._model_instance is not None
        return self._model_instance

    @classmethod
    def from_run(cls, model: rdm_run.PythonModel, parent: PythonModelsGroup) -> Self:
        self = cls(
            parent=parent, model_name=model.name, _model_instance=model.model_instance
        )
        self._connections_dataset = ConnectionDataset.from_run(model, self)
        self._start_values_dataset = StartValuesDataset.from_run(model, self)
        self._parameters_to_log_dataset = ParametersToLogDataset.from_run(model, self)
        self._reference_dataset = PythonModelReferenceDataset.from_run(model, self)
        return self

    @classmethod
    def from_hdf5(cls, hdf5: HDF5, group_name: str, parent: PythonModelsGroup) -> Self:
        self = cls(parent=parent, model_name=group_name)
        self._connections_dataset = ConnectionDataset.from_hdf5(hdf5, self)
        self._start_values_dataset = StartValuesDataset.from_hdf5(hdf5, self)
        self._parameters_to_log_dataset = ParametersToLogDataset.from_hdf5(hdf5, self)
        self._reference_dataset = PythonModelReferenceDataset.from_hdf5(hdf5, self)
        self._model_instance = self.reference_dataset.unpickle_python_model()
        self._reference_dataset.pickled_python_model = None
        return self

    def to_hdf5(self, hdf5: HDF5) -> None:
        super().to_hdf5(hdf5)
        self.reference_dataset.to_hdf5(hdf5)


@dataclass
class SimulationResultsGroup(Group):
    parent: RunGroup
    _time_series: Optional[TimeSeriesDataset] = None
    _attr: Optional[SimulationResultsAttr] = None

    GROUP_NAME = "simulation_results"

    @property
    def path(self) -> str:
        return f"{self.parent.path}/{self.name}"

    @property
    def name(self) -> str:
        return self.GROUP_NAME

    @property
    def attr(self) -> SimulationResultsAttr:
        assert self._attr is not None
        return self._attr

    @property
    def time_series(self) -> TimeSeriesDataset:
        assert self._time_series is not None
        return self._time_series

    @property
    def simulation_config(self) -> SimulationConfig:
        return self.attr.to_dict()

    @classmethod
    def from_run(cls, run: rdm_run.Run, parent: RunGroup) -> Self:
        self = cls(parent=parent)
        self._time_series = TimeSeriesDataset.from_run(run, self)
        self._attr = SimulationResultsAttr.from_run(run, self)
        return self

    @classmethod
    def from_hdf5(cls, hdf5: HDF5, parent: RunGroup) -> Self:
        self = cls(parent)
        self._time_series = TimeSeriesDataset.from_hdf5(hdf5, self)
        self._attr = SimulationResultsAttr.from_hdf5(hdf5, self)
        return self

    def to_hdf5(self, hdf5: HDF5) -> None:
        hdf5.create_group(self.path)
        self.time_series.to_hdf5(hdf5)
        self.attr.to_hdf5(hdf5)


@dataclass
class SimulationResultsAttr(Attribute):
    parent: SimulationResultsGroup
    attributes: Attrs

    CONFIG_KEY = "simulation_config"

    class ConfigKeys:
        STOP_TIME = "stop_time"
        STEP_SIZE = "step_size"
        LOGGING_STEP_SIZE = "logging_step_size"
        GET_UNITS = "get_units"

    @dataclass
    class Attrs:
        stop_time: float
        step_size: float
        logging_step_size: Optional[float] = None
        get_units: bool = True

        def __post_init__(self) -> None:
            if self.logging_step_size is None:
                self.logging_step_size = self.step_size

    @property
    def path(self) -> str:
        return self.parent.path

    @classmethod
    def from_run(cls, run: rdm_run.Run, parent: SimulationResultsGroup) -> Self:
        return cls(
            parent=parent, attributes=cls.Attrs(**run._simulation_config.to_dict())
        )

    @classmethod
    def from_hdf5(cls, hdf5: HDF5, parent: SimulationResultsGroup) -> Self:
        return cls(parent, cls.Attrs(**hdf5.read_attributes(parent.path)))

    def to_dict(self) -> SimulationConfig:
        return cast(SimulationConfig, asdict(self.attributes))

    def to_hdf5(self, hdf5: HDF5) -> None:
        hdf5.append_attributes(cast(dict[str, Any], self.to_dict()), self.path)


@dataclass
class TimeSeriesDataset(Dataset):
    DATASET_NAME: ClassVar[str] = "time_series"

    parent: SimulationResultsGroup
    data: pd.DataFrame
    _attr: Optional[TimeSeriesAttr] = None

    @property
    def path(self) -> str:
        return f"{self.parent.path}/{self.name}"

    @property
    def name(self) -> str:
        return self.DATASET_NAME

    @property
    def attr(self) -> TimeSeriesAttr:
        assert self._attr is not None
        return self._attr

    @classmethod
    def from_run(cls, run: rdm_run.Run, parent: SimulationResultsGroup) -> Self:
        if run._results is None:
            raise ValueError
        self = cls(parent=parent, data=run._results.time_series)
        self._attr = TimeSeriesAttr.from_run(run, self)
        return self

    @classmethod
    def from_hdf5(cls, hdf5: HDF5, parent: SimulationResultsGroup) -> Self:
        _time_series = hdf5.read_data(cls.DATASET_NAME, parent.path)
        time_series = pd.DataFrame.from_records(_time_series)
        self = cls(parent=parent, data=time_series)
        self._attr = TimeSeriesAttr.from_hdf5(hdf5, self)
        return self

    def to_hdf5(self, hdf5: HDF5) -> None:
        if self.data is None:
            data = "No simulation performed"
        else:
            data = self.data.to_records(index=False)
        hdf5.store_data(
            data,
            data_name=self.name,
            group_path=self.parent.path,
        )
        self.attr.to_hdf5(hdf5)


@dataclass
class TimeSeriesAttr(Attribute):
    parent: HDF5Object
    attributes: Optional[Units]

    # @dataclass
    # class Attr:
    #     @classmethod
    #     def from_dict(cls, units: Optional[dict]):
    #         if units is None:
    #             return cls()
    #         return make_dataclass(
    #             cls.__name__, [(key, type(val)) for key, val in units.items()]
    #         )(**units)
    @property
    def path(self) -> str:
        return self.parent.path

    @classmethod
    def from_run(cls, run: rdm_run.Run, parent: HDF5Object) -> Self:
        if run._results is None:
            raise ValueError
        return cls(parent=parent, attributes=run._results.units)

    @classmethod
    def from_hdf5(cls, hdf5: HDF5, parent: HDF5Object) -> Self:
        attr = {
            parameter_name: (unit or None)
            for parameter_name, unit in hdf5.read_attributes(parent.path).items()
        }
        return cls(parent=parent, attributes=attr)

    def to_dict(self) -> Optional[Units]:
        return self.attributes

    def to_hdf5(self, hdf5: HDF5) -> None:
        if not self.attributes:
            return
        hdf5.append_attributes(
            {k: v if v is not None else "" for k, v in self.attributes.items()},
            self.path,
        )


@dataclass
class FmuContentDataset(Dataset):
    dataset_name: str
    data: Optional[Any] = None

    @property
    def name(self) -> str:
        return self.dataset_name

    @property
    def path(self) -> str:
        return f"{self.parent.path}/{self.name}"

    @classmethod
    def from_hdf5(cls, dataset_name: str, parent: Group) -> Self:
        return cls(parent, dataset_name)

    def to_hdf5(self, hdf5: HDF5) -> None:
        assert self.data is not None
        hdf5.store_data(np.void(self.data), self.dataset_name, self.parent.path)

    def read_data(self, hdf5: HDF5) -> bytes:
        return cast(bytes, hdf5.read_data(self.name, self.parent.path))


@dataclass
class FmusStorageGroup(Group):
    parent: ModelStorageGroup
    _fmus: Optional[list[FmuContentDataset]] = None

    @property
    def name(self) -> str:
        return "fmus"

    @property
    def path(self) -> str:
        return f"{self.parent.path}/{self.name}"

    @property
    def fmus(self) -> list[FmuContentDataset]:
        assert self._fmus is not None
        return self._fmus

    @classmethod
    def from_hdf5(cls, hdf5: HDF5, parent: ModelStorageGroup) -> Self:
        self = cls(parent)
        fmus = []
        for dataset_name in hdf5.get_dataset_names(self.path):
            fmus.append(FmuContentDataset.from_hdf5(dataset_name, self))
        self._fmus = fmus
        return self

    def to_hdf5(self, hdf5: HDF5) -> None:
        hdf5.create_group(self.path)

    def get_fmu_content_from_reference(self, hdf5: HDF5, reference: str) -> bytes:
        return cast(bytes, hdf5.read_data(reference, self.path))

    def store_fmu(self, hdf5: HDF5, fmu_content: bytes, fmu_hash: str) -> None:
        FmuContentDataset(parent=self, dataset_name=fmu_hash, data=fmu_content).to_hdf5(
            hdf5
        )

    def get_references(self) -> list[str]:
        return [fmu_dataset.dataset_name for fmu_dataset in self.fmus]


@dataclass
class PythonModelsContentDataset(Dataset):
    dataset_name: str
    data: Optional[Any] = None

    @property
    def name(self) -> str:
        return self.dataset_name

    @property
    def path(self) -> str:
        return f"{self.parent.path}/{self.name}"

    @classmethod
    def from_hdf5(cls, dataset_name: str, parent: Group) -> Self:
        return cls(parent, dataset_name)

    def to_hdf5(self, hdf5: HDF5) -> None:
        assert self.data is not None
        hdf5.store_data(np.void(self.data), self.dataset_name, self.parent.path)

    def read_data(self, hdf5: HDF5) -> bytes:
        return cast(bytes, hdf5.read_data(self.name, self.parent.path))


@dataclass
class PythonModelsStorageGroup(Group):
    parent: ModelStorageGroup
    _python_models: Optional[list[PythonModelsContentDataset]] = None

    @property
    def name(self) -> str:
        return "python_models"

    @property
    def path(self) -> str:
        return f"{self.parent.path}/{self.name}"

    @property
    def python_models(self) -> list[PythonModelsContentDataset]:
        assert self._python_models is not None
        return self._python_models

    @classmethod
    def from_hdf5(cls, hdf5: HDF5, parent: ModelStorageGroup) -> Self:
        self = cls(parent)
        python_models = []
        for dataset_name in hdf5.get_dataset_names(self.path):
            python_models.append(
                PythonModelsContentDataset.from_hdf5(dataset_name, self)
            )
        self._python_models = python_models
        return self

    def get_pickled_model_by_reference(self, hdf5: HDF5, reference: str) -> bytes:
        return cast(bytes, hdf5.read_data(reference, self.path))

    def store_model(self, hdf5: HDF5, pickled_model: bytes, model_hash: str) -> None:
        PythonModelsContentDataset(
            parent=self, dataset_name=model_hash, data=pickled_model
        ).to_hdf5(hdf5)

    def to_hdf5(self, hdf5: HDF5) -> None:
        hdf5.create_group(self.path)

    def get_references(self) -> list[str]:
        return [
            python_model_dataset.dataset_name
            for python_model_dataset in self.python_models
        ]


@dataclass
class ModelStorageGroup(TopLevelGroup):
    _fmus_storage_group: Optional[FmusStorageGroup] = None
    _python_models_storage_group: Optional[PythonModelsStorageGroup] = None

    @property
    def name(self) -> str:
        return "models"

    @property
    def path(self) -> str:
        return self.name

    @property
    def fmus_storage_group(self) -> FmusStorageGroup:
        assert self._fmus_storage_group is not None
        return self._fmus_storage_group

    @property
    def python_models_storage_group(self) -> PythonModelsStorageGroup:
        assert self._python_models_storage_group is not None
        return self._python_models_storage_group

    @classmethod
    def initialize(cls, hdf5: HDF5) -> Self:
        if is_hdf5_initialized(hdf5):
            return cls.from_hdf5(hdf5)
        self = cls(parent=None)
        self._fmus_storage_group = FmusStorageGroup(self)
        self.fmus_storage_group.to_hdf5(hdf5)
        self._python_models_storage_group = PythonModelsStorageGroup(self)
        self.python_models_storage_group.to_hdf5(hdf5)
        return self

    @classmethod
    def from_hdf5(cls, hdf5: HDF5) -> Self:
        self = cls(parent=None)
        self._fmus_storage_group = FmusStorageGroup.from_hdf5(hdf5, self)
        self._python_models_storage_group = PythonModelsStorageGroup.from_hdf5(
            hdf5, self
        )
        return self

    def to_hdf5(self, hdf5: HDF5) -> None:
        if self.path in hdf5:
            return
        hdf5.create_group(self.path)
        self.fmus_storage_group.to_hdf5(hdf5)


class MetaKeys(Enum):
    CREATION_DATE = "creation date"
    PYTHON_VERSION = "python version"
    SOFIRPY_VERSION = "sofirpy version"
    ENVIRONMENT_INFORMATION = "environment information"


def generate_meta() -> dict[str, Union[str, list[str]]]:
    return {
        MetaKeys.CREATION_DATE.value: datetime.now().strftime("%d-%b-%Y %H:%M:%S"),
        MetaKeys.PYTHON_VERSION.value: sys.version,
        MetaKeys.SOFIRPY_VERSION.value: sofirpy.__version__,
        # MetaKeys.ENVIRONMENT_INFORMATION.value: get_environment_information(),
    }


def get_init_key_value() -> tuple[str, str]:
    return (
        "Initialization",
        "Created with sofirpy. See Documentation here: https://sofirpy.readthedocs.io",
    )


def init_hdf5(hdf5_path: Path) -> HDF5:
    hdf5 = HDF5(hdf5_path)
    if is_hdf5_initialized(hdf5):
        print("HDF5 already initialized")
        return hdf5
    meta = generate_meta()
    key, value = get_init_key_value()
    meta = {**meta, key: value}
    hdf5.append_attributes(meta)
    ModelStorageGroup.initialize(hdf5)

    print("HDF5 initialized")

    return hdf5


def is_hdf5_initialized(hdf5: HDF5) -> bool:
    key, value = get_init_key_value()
    attr = hdf5.read_attributes("")
    if key not in attr:
        return False
    if not attr[key] == value:
        return False
    if not "models" in hdf5:  # TODO overthink init behavior
        return False
    return True


class RunAttrKeys(Enum):
    RUN_NAME = "run_name"
    ID = "id"
    DESCRIPTION = "description"
    CREATION_DATE = "creation date"


def get_run_group_meta(run_name: str) -> dict[str, str]:
    return {
        RunAttrKeys.RUN_NAME.value: run_name,
        RunAttrKeys.ID.value: generate_id(),
        RunAttrKeys.DESCRIPTION.value: "",
    }


def generate_id() -> str:
    return str(1)


# def get_environment_information() -> list[str]:
#     return list(freeze.freeze())


class HDF5NotInitialized(Exception):
    ...
