from __future__ import annotations

import hashlib
import inspect
import json
import sys
import tempfile
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field, make_dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, ClassVar, Optional, TypedDict, Union, cast

import cloudpickle
import numpy as np
import pandas as pd
from pip._internal.operations import freeze
from typing_extensions import NotRequired, Self

import sofirpy
import sofirpy.rdm.run as rdm_run
import sofirpy.utils as utils
from sofirpy import HDF5
from sofirpy.simulation.simulation import (
    Connections,
    ConnectionsConfig,
    FmuPaths,
    ModelInstances,
    ParametersToLog,
    StartValues,
    Units,
)
from sofirpy.simulation.simulation_entity import SimulationEntity, StartValue


class Config(TypedDict):
    run_meta: MetaConfig
    models: dict[str, Union[ModelConfig, FmuConfig]]
    simulation_config: SimulationConfig


class MetaConfig(TypedDict):
    run_name: str
    description: str
    keywords: list[str]


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
    parent: Optional[HDF5Object]

    @property
    @abstractmethod
    def path(self) -> str:
        ...


@dataclass
class HDF5Object(HDF5Entity):
    parent: Optional[Group]

    @property
    @abstractmethod
    def name(self) -> str:
        ...


class Group(HDF5Object):
    ...


class Dataset(HDF5Object):
    ...


class Attribute(HDF5Entity):
    ...


@dataclass
class RunGroup(Group):
    run_name: str
    attr: Optional[RunAttr] = None
    config_dataset: Optional[RunConfigDataset] = None
    models_group: Optional[ModelsGroup] = None
    simulation_group: Optional[SimulationResultsGroup] = None

    @property
    def path(self) -> str:
        return self.run_name

    @property
    def name(self) -> str:
        return self.run_name

    @property
    def simulation_and_model_config(self) -> dict[str, Any]:  # TODO specify type
        return {
            **self.simulation_group.simulation_config,
            **self.models_group.model_config,
        }

    @classmethod
    def from_config(
        cls,
        run_name: str,
        config_path: Path,
        model_instances: Optional[ModelInstances] = None,
    ) -> Self:
        with open(config_path) as config_file:
            config: Config = json.load(config_file)
        self = cls(run_name=run_name, parent=None)
        config_dataset = RunConfigDataset.from_config(config, self)
        self.config_dataset = config_dataset
        attr = RunAttr.from_config(config, self)
        self.attr = attr
        models_group = ModelsGroup.from_config(
            config, self, model_instances=model_instances
        )
        self.models_group = models_group
        simulation_group = SimulationResultsGroup.from_config(config, self)
        self.simulation_group = simulation_group
        return self

    @classmethod
    def from_run(cls, run: rdm_run.Run) -> Self:
        self = cls(run_name=run.run_name, parent=None)
        self.config_dataset = RunConfigDataset.from_run(run=run, parent=self)
        self.attr = RunAttr.from_run(run=run, parent=self)
        self.models_group = ModelsGroup.from_run(run=run, parent=self)
        self.simulation_group = SimulationResultsGroup.from_run(run=run, parent=self)
        return self

    @classmethod
    def from_hdf5(cls, hdf5_path: Path, run_name: str) -> Self:
        hdf5 = HDF5(hdf5_path)
        self = cls(run_name=run_name, parent=None)
        attr = RunAttr.from_hdf5(hdf5, self)
        self.attr = attr
        models_group = ModelsGroup.from_hdf5(hdf5, self)
        self.models_group = models_group
        simulation_group = SimulationResultsGroup.from_hdf5(hdf5, self)
        self.simulation_group = simulation_group
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
            units=self.simulation_group.time_series.attr,
        )
        return rdm_run.Run(
            run_name=run_name,
            _run_meta=run_meta,
            _models=_models,
            _simulation_config=simulation_config,
            _results=results,
        )

    def store_simulation_results(
        self, results: pd.DataFrame, units: Optional[Units]
    ) -> None:
        self.simulation_group.time_series.data = results
        self.simulation_group.time_series.attr = units

    def to_hdf5(self, hdf5_path: Path) -> None:
        assert self.simulation_group.time_series is not None
        hdf5 = HDF5(hdf5_path)
        if not is_hdf5_initialized(hdf5):
            raise Valueerror
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
    parent: HDF5Entity
    data: Config

    @property
    def name(self) -> str:
        return self.DATASET_NAME

    @property
    def path(self) -> str:
        return f"{self.parent.parent}/{self.name}"

    @classmethod
    def from_run(cls, run: rdm_run.Run, parent: Group) -> Self:
        return cls(parent=parent, data=run.get_config())

    @classmethod
    def from_config(cls, config: Config, parent: HDF5Entity) -> Self:
        return cls(parent, config)

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
    def from_run(cls, run: rdm_run.Run, parent: HDF5Object) -> Self:
        return cls(parent=parent, attributes=cls.Attrs(**asdict(run._run_meta)))

    @classmethod
    def from_config(cls, config: dict[str, Any], parent: RunGroup) -> Self:
        meta_config = config.get(cls.CONFIG_KEY) or {}
        return cls(
            parent=parent,
            attributes=cls.Attrs(
                run_name=parent.run_name,
                description=meta_config.get(cls.ConfigKeys.DESCRIPTION) or "",
                keywords=meta_config.get(cls.ConfigKeys.KEYWORDS) or [],
            ),
        )

    @classmethod
    def from_hdf5(cls, hdf5: HDF5, parent: RunGroup) -> Self:
        attr = hdf5.read_attributes(parent.path)
        del attr["typ"]
        return cls(parent, cls.Attrs(**attr))

    def to_hdf5(self, hdf5: HDF5) -> None:
        hdf5.append_attributes({"typ": "run"}, self.path)
        hdf5.append_attributes(self.to_dict(), self.path)

    def to_dict(self) -> MetaConfig:  # TODO right type
        return asdict(self.attributes)


@dataclass
class ModelsGroup(Group):
    parent: RunGroup
    fmus_group: Optional[FmusGroup] = None
    python_models_group: Optional[PythonModelsGroup] = None

    CONFIG_KEY = "models"
    GROUP_NAME = "models"

    @property
    def path(self) -> None:
        return f"{self.parent.path}/{self.name}"

    @property
    def name(self) -> None:
        return self.GROUP_NAME

    @classmethod
    def from_run(cls, run: rdm_run.Run, parent: Group) -> Self:
        self = cls(parent=parent)
        self.fmus_group = FmusGroup.from_run(run, self)
        self.python_models_group = PythonModelsGroup.from_run(run, self)
        return self

    @classmethod
    def from_config(
        cls,
        config: Config,
        parent: RunGroup,
        model_instances: Optional[ModelInstances],
    ) -> Self:  # TODO make it more robust -> check for names and fmu or model
        self = cls(parent)
        models_config = config[cls.CONFIG_KEY]
        fmus_group = FmusGroup.from_config(models_config, self)
        self.fmus_group = fmus_group
        python_models_group = PythonModelsGroup.from_config(
            models_config, model_instances, self
        )
        self.python_models_group = python_models_group
        return self

    @classmethod
    def from_hdf5(cls, hdf5: HDF5, parent: RunGroup) -> Self:
        self = cls(
            parent
        )  # TODO maybe change order, first init sub classes without parent then assign, maybe not possible because parent attr need to be accessed
        fmus_group = FmusGroup.from_hdf5(hdf5, self)
        self.fmus_group = fmus_group
        python_models_group = PythonModelsGroup.from_hdf5(hdf5, self)
        self.python_models_group = python_models_group
        return self

    def to_hdf5(self, hdf5: HDF5) -> None:
        hdf5.create_group(self.path)
        self.fmus_group.to_hdf5(hdf5)
        self.python_models_group.to_hdf5(hdf5)


@dataclass
class FmusGroup(Group):
    parent: ModelsGroup
    fmu_groups: Optional[list[FmuGroup]] = None

    GROUP_NAME = "fmus"

    @property
    def path(self) -> str:
        return f"{self.parent.path}/{self.name}"

    @property
    def name(self) -> str:
        return self.GROUP_NAME

    @property
    def fmu_paths(self) -> FmuPaths:
        return {fmu.name: fmu.fmu_path for fmu in self.fmu_groups}

    @classmethod
    def from_run(cls, run: rdm_run.Run, parent: Group) -> Self:
        self = cls(parent)
        self.fmu_groups = [
            FmuGroup.from_run(fmu, self) for fmu in run._models.fmus.values()
        ]
        return self

    @classmethod
    def from_config(
        cls, models_config: dict[str, ModelConfig], parent: ModelsGroup
    ) -> Self:
        self = cls(parent)
        fmus_config = {
            model_name: model_config
            for model_name, model_config in models_config.items()
            if "fmu_path" in model_config
        }
        fmu_groups = []
        for fmu_name, fmu_config in fmus_config.items():
            fmu_groups.append(FmuGroup.from_config(fmu_name, fmu_config, self))
        self.fmu_groups = fmu_groups
        return self

    @classmethod
    def from_hdf5(cls, hdf5: HDF5, parent: ModelsGroup) -> Self:
        self = cls(parent)
        fmu_groups = []
        for group_name in hdf5.get_group_names(self.path):
            fmu_groups.append(FmuGroup.from_hdf5(hdf5, group_name, self))
        self.fmu_groups = fmu_groups
        return self

    def to_hdf5(self, hdf5: HDF5) -> None:
        hdf5.create_group(self.path)
        for fmu_group in self.fmu_groups:
            fmu_group.to_hdf5(hdf5)


@dataclass
class PythonModelsGroup(Group):
    parent: ModelsGroup
    python_model_groups: Optional[list[PythonModelGroup]] = None
    GROUP_NAME = "python_models"

    @property
    def path(self) -> str:
        return f"{self.parent.path}/{self.GROUP_NAME}"

    @property
    def name(self) -> str:
        return self.GROUP_NAME

    @property
    def model_instances(self) -> ModelInstances:
        return {
            python_model_group.name: python_model_group.model_instance
            for python_model_group in self.python_model_groups
        }

    @classmethod
    def from_run(cls, run: rdm_run.Run, parent: Group) -> Self:
        self = cls(parent)
        self.python_model_groups = [
            PythonModelGroup.from_run(python_model, self)
            for python_model in run._models.python_models.values()
        ]
        return self

    @classmethod
    def from_config(
        cls,
        models_config: dict[str, ModelConfig],
        model_instances: ModelInstances,
        parent: ModelsGroup,
    ) -> Self:
        assert model_instances is not None
        self = cls(parent)
        python_models_config = {
            model_name: model_config
            for model_name, model_config in models_config.items()
            if "fmu_path" not in model_config
        }
        python_model_groups = []
        for python_model_name, python_model_config in python_models_config.items():
            python_model_groups.append(
                PythonModelGroup.from_config(
                    python_model_name,
                    model_instances[python_model_name],
                    python_model_config,
                    self,
                )
            )
        self.python_model_groups = python_model_groups
        return self

    @classmethod
    def from_hdf5(cls, hdf5: HDF5, parent: ModelsGroup) -> Self:
        self = cls(parent)
        python_model_groups = []
        for group_name in hdf5.get_group_names(self.path):
            python_model_groups.append(
                PythonModelGroup.from_hdf5(hdf5, group_name, self)
            )
        self.python_model_groups = python_model_groups
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
    @abstractmethod
    def from_config(
        cls, model_config: ModelConfig, parent: Union[PythonModelGroup, FmuGroup]
    ) -> Self:
        ...

    @classmethod
    def from_hdf5(cls, hdf5: HDF5, parent: Union[PythonModelGroup, FmuGroup]) -> Self:
        return cls(
            parent,
            json.loads(hdf5.read_data(cls.DATASET_NAME, parent.path).decode("utf-8"))[
                "data"
            ],
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
    def from_run(cls, model: rdm_run.Model, parent: Group) -> Self:
        return cls(parent=parent, data=model.connections or [])

    @classmethod
    def from_config(
        cls, model_config: ModelConfig, parent: Union[PythonModelGroup, FmuGroup]
    ) -> Self:
        connections = model_config.get(cls.CONFIG_KEY) or []
        return cls(parent, connections)


@dataclass
class StartValuesDataset(ModelDataset):
    data: dict[str, StartValue]

    DATASET_NAME = "start_values"
    CONFIG_KEY = "start_values"

    @classmethod
    def from_run(cls, model: rdm_run.Model, parent: Group) -> Self:
        return cls(parent=parent, data=model.start_values or {})

    @classmethod
    def from_config(
        cls, model_config: ModelConfig, parent: Union[PythonModelGroup, FmuGroup]
    ) -> Self:
        start_values = model_config.get(cls.CONFIG_KEY) or {}
        return cls(parent, start_values)


@dataclass
class ParametersToLogDataset(ModelDataset):
    data: list[str]

    DATASET_NAME = "parameters_to_log"
    CONFIG_KEY = "parameters_to_log"

    @classmethod
    def from_run(cls, model: rdm_run.Model, parent: Group) -> Self:
        return cls(parent=parent, data=model.parameters_to_log or [])

    @classmethod
    def from_config(
        cls, model_config: ModelConfig, parent: Union[PythonModelGroup, FmuGroup]
    ) -> Self:
        parameters_to_log = model_config.get(cls.CONFIG_KEY) or []
        return cls(parent, parameters_to_log)


@dataclass
class FmuReferenceDataset(ModelDataset):
    data: str
    fmu_content: Optional[bytes] = None  # TODO maybe move this to FmuStorageDataset
    DATASET_NAME = "reference"

    CONFIG_KEY = "fmu_path"

    @classmethod
    def from_hdf5(cls, hdf5: HDF5, parent: FmuGroup) -> Self:
        return cls(parent=parent, data=hdf5.read_data(cls.DATASET_NAME, parent.path))

    @classmethod
    def from_run(cls, model: rdm_run.Fmu, parent: Group) -> Self:
        with open(model.fmu_path, "rb") as fmu:
            fmu_content = fmu.read()
        fmu_hash = hashlib.sha256(fmu_content).hexdigest()
        return cls(parent=parent, data=fmu_hash, fmu_content=fmu_content)

    @classmethod
    def from_config(
        cls, model_config: FmuConfig, parent: Union[PythonModelGroup, FmuGroup]
    ) -> Self:
        fmu_path = utils.convert_str_to_path(model_config[cls.CONFIG_KEY], "fmu_path")
        with open(fmu_path, "rb") as fmu:
            fmu_content = fmu.read()
        fmu_hash = hashlib.sha256(fmu_content).hexdigest()
        return cls(parent=parent, data=fmu_hash, fmu_content=fmu_content)

    @classmethod
    def from_hdf5(cls, hdf5: HDF5, parent: Union[PythonModelGroup, FmuGroup]) -> Self:
        fmu_hash = hdf5.read_data(cls.DATASET_NAME, parent.path).decode("utf-8")
        fmu_content = ModelStorageGroup.from_hdf5(
            hdf5
        ).fmus_storage_group.get_fmu_content_from_reference(hdf5, fmu_hash)
        return cls(parent, data=fmu_hash, fmu_content=fmu_content)

    def write_fmu_content_to_tmp_dir(self) -> Path:
        tmp_dir = Path(tempfile.mkdtemp())
        fmu_path = tmp_dir / f"{self.parent.model_name}.fmu"
        fmu_path.touch()
        with open(fmu_path, "wb") as fmu_file:
            fmu_file.write(self.fmu_content)
        self.fmu_content = None
        return fmu_path

    def to_hdf5(self, hdf5: HDF5) -> None:
        fmus_storage_group = ModelStorageGroup.from_hdf5(hdf5).fmus_storage_group
        hdf5.store_data(self.data, self.name, self.parent.path)
        if self.data in fmus_storage_group.get_references():
            return
        fmus_storage_group.store_fmu(hdf5, self.fmu_content, self.data)
        self.fmu_content = None  # for memory purposes


@dataclass
class PythonModelReferenceDataset(ModelDataset):
    data: str
    pickled_python_model: Optional[bytes] = None
    DATASET_NAME = "reference"

    @classmethod
    def from_run(cls, model: rdm_run.PythonModel, parent: Group) -> Self:
        cloudpickle.register_pickle_by_value(inspect.getmodule(model.model_instance))
        pickled_python_model = cloudpickle.dumps(model.model_instance)
        model_hash = hashlib.sha256(pickled_python_model).hexdigest()
        return cls(
            parent=parent, data=model_hash, pickled_python_model=pickled_python_model
        )

    @classmethod
    def from_config(
        cls, model_instance: SimulationEntity, parent: Union[PythonModelGroup, FmuGroup]
    ) -> Self:
        cloudpickle.register_pickle_by_value(inspect.getmodule(model_instance))
        pickled_python_model = cloudpickle.dumps(model_instance)
        model_hash = hashlib.sha256(pickled_python_model).hexdigest()
        return cls(
            parent=parent, data=model_hash, pickled_python_model=pickled_python_model
        )

    @classmethod
    def from_hdf5(cls, hdf5: HDF5, parent: Union[PythonModelGroup, FmuGroup]) -> Self:
        model_hash = hdf5.read_data(cls.DATASET_NAME, parent.path).decode("utf-8")
        pickled_python_model = ModelStorageGroup.from_hdf5(
            hdf5
        ).python_models_storage_group.get_pickled_model_by_reference(hdf5, model_hash)
        return cls(parent, data=model_hash, pickled_python_model=pickled_python_model)

    def unpickle_python_model(self) -> SimulationEntity:
        return cloudpickle.loads(self.pickled_python_model)

    def to_hdf5(self, hdf5: HDF5) -> None:
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
    connections_dataset: Optional[ConnectionDataset] = None
    start_values_dataset: Optional[StartValuesDataset] = None
    parameters_to_log_dataset: Optional[ParametersToLogDataset] = None

    @property
    def path(self) -> str:
        return f"{self.parent.path}/{self.name}"

    @property
    def name(self) -> str:
        return self.model_name

    @classmethod
    @abstractmethod
    def from_hdf5(cls, hdf5: HDF5, model_name: str, parent) -> Self:
        ...

    def to_hdf5(self, hdf5: HDF5) -> Self:
        hdf5.create_group(self.path)
        self.connections_dataset.to_hdf5(hdf5)
        self.start_values_dataset.to_hdf5(hdf5)
        self.parameters_to_log_dataset.to_hdf5(hdf5)


@dataclass
class FmuGroup(ModelGroup):
    reference_dataset: Optional[FmuReferenceDataset] = None
    fmu_path: Optional[Path] = None

    @classmethod
    def from_run(cls, model: rdm_run.Fmu, parent: Group) -> Self:
        self = cls(parent=parent, model_name=model.name, fmu_path=model.fmu_path)
        self.connections_dataset = ConnectionDataset.from_run(model, self)
        self.start_values_dataset = StartValuesDataset.from_run(model, self)
        self.parameters_to_log_dataset = ParametersToLogDataset.from_run(model, self)
        self.reference_dataset = FmuReferenceDataset.from_run(model, self)
        return self

    @classmethod
    def from_config(
        cls,
        model_name: str,
        model_config: FmuConfig,
        parent: Union[FmusGroup, PythonModelsGroup],
    ) -> Self:
        self = cls(
            parent=parent, model_name=model_name, fmu_path=model_config["fmu_path"]
        )
        self.connections_dataset = ConnectionDataset.from_config(model_config, self)
        self.start_values_dataset = StartValuesDataset.from_config(model_config, self)
        self.parameters_to_log_dataset = ParametersToLogDataset.from_config(
            model_config, self
        )
        self.reference_dataset = FmuReferenceDataset.from_config(model_config, self)
        return self

    @classmethod
    def from_hdf5(cls, hdf5: HDF5, group_name: str, parent: Group) -> Self:
        self = cls(parent=parent, model_name=group_name)
        self.connections_dataset = ConnectionDataset.from_hdf5(hdf5, self)
        self.start_values_dataset = StartValuesDataset.from_hdf5(hdf5, self)
        self.parameters_to_log_dataset = ParametersToLogDataset.from_hdf5(hdf5, self)
        self.reference_dataset = FmuReferenceDataset.from_hdf5(hdf5, self)
        self.fmu_path = self.reference_dataset.write_fmu_content_to_tmp_dir()
        return self

    def to_hdf5(self, hdf5: HDF5) -> Self:
        super().to_hdf5(hdf5)
        self.reference_dataset.to_hdf5(hdf5)


@dataclass
class PythonModelGroup(ModelGroup):
    reference_dataset: Optional[PythonModelReferenceDataset] = None
    model_instance: Optional[SimulationEntity] = None

    @property
    def path(self) -> str:
        return f"{self.parent.path}/{self.model_name}"

    @classmethod
    def from_run(cls, model: rdm_run.PythonModel, parent: Group) -> Self:
        self = cls(
            parent=parent, model_name=model.name, model_instance=model.model_instance
        )
        self.connections_dataset = ConnectionDataset.from_run(model, self)
        self.start_values_dataset = StartValuesDataset.from_run(model, self)
        self.parameters_to_log_dataset = ParametersToLogDataset.from_run(model, self)
        self.reference_dataset = PythonModelReferenceDataset.from_run(model, self)
        return self

    @classmethod
    def from_config(
        cls,
        model_name: str,
        model_instance: SimulationEntity,
        model_config: ModelConfig,
        parent: Union[FmusGroup, PythonModelsGroup],
    ) -> Self:
        self = cls(parent=parent, model_name=model_name, model_instance=model_instance)
        self.connections_dataset = ConnectionDataset.from_config(model_config, self)
        self.start_values_dataset = StartValuesDataset.from_config(model_config, self)
        self.parameters_to_log_dataset = ParametersToLogDataset.from_config(
            model_config, self
        )
        self.reference_dataset = PythonModelReferenceDataset.from_config(
            model_instance, self
        )
        return self

    @classmethod
    def from_hdf5(cls, hdf5: HDF5, group_name: str, parent: Group) -> Self:
        self = cls(parent=parent, model_name=group_name)
        self.connections_dataset = ConnectionDataset.from_hdf5(hdf5, self)
        self.start_values_dataset = StartValuesDataset.from_hdf5(hdf5, self)
        self.parameters_to_log_dataset = ParametersToLogDataset.from_hdf5(hdf5, self)
        self.reference_dataset = PythonModelReferenceDataset.from_hdf5(hdf5, self)
        self.model_instance = self.reference_dataset.unpickle_python_model()
        self.reference_dataset.pickled_python_model = None
        return self

    def to_hdf5(self, hdf5: HDF5) -> Self:
        super().to_hdf5(hdf5)
        self.reference_dataset.to_hdf5(hdf5)


@dataclass
class SimulationResultsGroup(Group):
    parent: RunGroup
    time_series: Optional[TimeSeriesDataset] = None
    attr: Optional[SimulationResultsAttr] = None

    GROUP_NAME = "simulation_results"

    @property
    def path(self) -> str:
        return f"{self.parent.path}/{self.name}"

    @property
    def name(self) -> str:
        return self.GROUP_NAME

    @property
    def simulation_config(self) -> SimulationConfig:
        return self.attr.to_dict()

    @classmethod
    def from_run(cls, run: rdm_run.Run, parent: Group) -> Self:
        self = cls(parent=parent)
        self.time_series = TimeSeriesDataset.from_run(run, self)
        self.attr = SimulationResultsAttr.from_run(run, self)
        return self

    @classmethod
    def from_config(cls, config: Config, parent: RunGroup) -> Self:
        self = cls(parent)
        attr = SimulationResultsAttr.from_config(config, self)
        self.attr = attr
        time_series_dataset = TimeSeriesDataset.from_config(self)
        self.time_series = time_series_dataset
        return self

    @classmethod
    def from_hdf5(cls, hdf5: HDF5, parent: RunGroup) -> Self:
        self = cls(parent)
        time_series_dataset = TimeSeriesDataset.from_hdf5(hdf5, self)
        self.time_series = time_series_dataset
        self.attr = SimulationResultsAttr.from_hdf5(hdf5, self)
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
    def from_run(cls, run: rdm_run.Run, parent: HDF5Object) -> Self:
        return cls(
            parent=parent, attributes=cls.Attrs(**run._simulation_config.to_dict())
        )

    @classmethod
    def from_config(cls, config: Config, parent: SimulationResultsGroup) -> Self:
        return cls(parent, cls.Attrs(**config[cls.CONFIG_KEY]))

    @classmethod
    def from_hdf5(cls, hdf5: HDF5, parent: SimulationResultsGroup) -> Self:
        return cls(parent, cls.Attrs(**hdf5.read_attributes(parent.path)))

    def to_dict(self) -> SimulationConfig:
        return asdict(self.attributes)

    def to_hdf5(self, hdf5: HDF5) -> None:
        hdf5.append_attributes(self.to_dict(), self.path)


@dataclass
class TimeSeriesDataset(Dataset):
    DATASET_NAME: ClassVar[str] = "time_series"

    parent: SimulationResultsGroup
    data: Optional[pd.DataFrame] = None
    _attr: Optional[TimeSeriesAttr] = None

    @property
    def path(self) -> str:
        return f"{self.parent.path}/{self.name}"

    @property
    def name(self) -> str:
        return self.DATASET_NAME

    @property
    def attr(self):
        return self._attr.attributes

    @attr.setter
    def attr(self, unit: Optional[Units]) -> None:  # TODO make this better/different
        self._attr.attributes = unit

    @classmethod
    def from_run(cls, run: rdm_run.Run, parent: Group) -> Self:
        self = cls(parent=parent)
        if run._results is None:
            raise ValueError
        self.data = run._results.time_series
        self._attr = TimeSeriesAttr.from_run(run, self)
        return self

    @classmethod
    def from_config(cls, parent: HDF5Entity) -> Self:
        self = cls(parent)
        self._attr = TimeSeriesAttr(self)
        return self

    @classmethod
    def from_hdf5(cls, hdf5: HDF5, parent: SimulationResultsGroup) -> Self:
        _time_series = hdf5.read_data(cls.DATASET_NAME, parent.path)
        time_series = pd.DataFrame.from_records(_time_series)
        self = cls(parent, time_series)
        attr = TimeSeriesAttr.from_hdf5(hdf5, self)
        self._attr = attr
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
        self._attr.to_hdf5(hdf5)


@dataclass
class TimeSeriesAttr(Attribute):
    parent: Optional[HDF5Object]
    attributes: Optional[Units] = None

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

    def to_dict(self) -> dict[str, Any]:
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
    def from_hdf5(cls, hdf5: HDF5, dataset_name: str, parent: Group) -> Self:
        return cls(parent, dataset_name)

    def to_hdf5(self, hdf5: HDF5) -> None:
        hdf5.store_data(np.void(self.data), self.dataset_name, self.parent.path)

    def read_data(self, hdf5: HDF5) -> None:
        return hdf5.read_data(self.name, self.parent.path)


@dataclass
class FmusStorageGroup(Group):
    parent: ModelStorageGroup
    fmus: Optional[list[FmuContentDataset]] = None

    @property
    def name(self) -> str:
        return "fmus"

    @property
    def path(self) -> str:
        return f"{self.parent.path}/{self.name}"

    @classmethod
    def from_hdf5(cls, hdf5: HDF5, parent: HDF5Entity) -> Self:
        self = cls(parent)
        fmus = []
        for dataset_name in hdf5.get_dataset_names(self.path):
            fmus.append(FmuContentDataset.from_hdf5(hdf5, dataset_name, self))
        self.fmus = fmus
        return self

    def to_hdf5(self, hdf5: HDF5) -> None:
        hdf5.create_group(self.path)

    def get_fmu_content_from_reference(self, hdf5: HDF5, reference: str) -> bytes:
        return hdf5.read_data(reference, self.path)

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
    def from_hdf5(cls, hdf5: HDF5, dataset_name: str, parent: Group) -> Self:
        return cls(parent, dataset_name)

    def to_hdf5(self, hdf5: HDF5) -> None:
        hdf5.store_data(np.void(self.data), self.dataset_name, self.parent.path)

    def read_data(self, hdf5: HDF5) -> None:
        return hdf5.read_data(self.name, self.parent.path)


@dataclass
class PythonModelsStorageGroup(Group):
    parent: ModelStorageGroup
    python_models: Optional[list[PythonModelsContentDataset]] = None

    @property
    def name(self) -> str:
        return "python_models"

    @property
    def path(self) -> str:
        return f"{self.parent.path}/{self.name}"

    @classmethod
    def from_hdf5(cls, hdf5: HDF5, parent: HDF5Entity) -> Self:
        self = cls(parent)
        python_models = []
        for dataset_name in hdf5.get_dataset_names(self.path):
            python_models.append(
                PythonModelsContentDataset.from_hdf5(hdf5, dataset_name, self)
            )
        self.python_models = python_models
        return self

    def get_pickled_model_by_reference(self, hdf5: HDF5, reference: str) -> bytes:
        return hdf5.read_data(reference, self.path)

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
class ModelStorageGroup(Group):
    fmus_storage_group: Optional[FmusStorageGroup] = None
    python_models_storage_group: Optional[PythonModelsStorageGroup] = None

    @property
    def name(self) -> str:
        return "models"

    @property
    def path(self) -> str:
        return self.name

    @classmethod
    def initialize(cls, hdf5: HDF5) -> Self:
        if is_hdf5_initialized(hdf5):
            return cls.from_hdf5(hdf5)
        self = cls(parent=None)
        self.fmus_storage_group = FmusStorageGroup(self)
        self.fmus_storage_group.to_hdf5(hdf5)
        self.python_models_storage_group = PythonModelsStorageGroup(self)
        self.python_models_storage_group.to_hdf5(hdf5)
        return self

    @classmethod
    def from_hdf5(cls, hdf5: HDF5) -> Self:
        self = cls(parent=None)
        fmus_storage_group = FmusStorageGroup.from_hdf5(hdf5, self)
        self.fmus_storage_group = fmus_storage_group
        python_models_storage_group = PythonModelsStorageGroup.from_hdf5(hdf5, self)
        self.python_models_storage_group = python_models_storage_group
        return self

    def to_hdf5(self, hdf5: HDF5) -> None:
        if self.path in hdf5:
            return
        hdf5.create_group(self.path)
        self.fmus_storage_group.to_hdf5()


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


def get_environment_information() -> list[str]:
    return list(freeze.freeze())


class HDF5NotInitialized(Exception):
    ...
