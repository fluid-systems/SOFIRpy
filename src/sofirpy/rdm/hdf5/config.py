from enum import Enum


class HDF5FileMetaKey(str, Enum):
    CREATED_WITH_SOFIRPY = "created with"
    INITIALIZATION_DATE = "initialization date"
    SOFIRPY_VERSION = "sofirpy version"

    @classmethod
    def get_values(cls) -> set[str]:
        return {key.value for key in HDF5FileMetaKey}


class ModelStorageGroupName(str, Enum):
    MODELS = "models"
    FMUS = "fmus"
    PYTHON_MODELS = "python_models"
    CLASSES = "classes"
    SOURCE_CODE = "source_code"

    @classmethod
    def absolute_paths(cls) -> set[str]:
        return {
            str(cls.MODELS.value),
            f"{cls.MODELS.value}/{cls.FMUS.value}",
            f"{cls.MODELS.value}/{cls.PYTHON_MODELS.value}",
            f"{cls.MODELS.value}/{cls.PYTHON_MODELS.value}/{cls.CLASSES.value}",
            f"{cls.MODELS.value}/{cls.PYTHON_MODELS.value}/{cls.SOURCE_CODE.value}",
        }

    @classmethod
    def get_fmu_path(cls) -> str:
        return f"{cls.MODELS.value}/{cls.FMUS.value}"

    @classmethod
    def get_source_code_path(cls) -> str:
        return f"{cls.MODELS.value}/{cls.PYTHON_MODELS.value}/{cls.SOURCE_CODE.value}"

    @classmethod
    def get_classes_path(cls) -> str:
        return f"{cls.MODELS.value}/{cls.PYTHON_MODELS.value}/{cls.CLASSES.value}"


class RunGroupName(str, Enum):
    SIMULATION_RESULTS = "simulation_results"
    MODELS = "models"
    FMUS = "fmus"
    PYTHON_MODELS = "python_models"

    @classmethod
    def get_fmu_models_path(cls) -> str:
        return f"{cls.MODELS.value}/{cls.FMUS.value}"

    @classmethod
    def get_python_models_path(cls) -> str:
        return f"{cls.MODELS.value}/{cls.PYTHON_MODELS.value}"


class RunDatasetName(Enum):
    CONFIG = "config"
    DEPENDENCIES = "dependencies"
    INIT_CONFIG = "init_config"
    CONNECTIONS = "connections"
    PARAMETERS_TO_LOG = "parameters_to_log"
    FMU_REFERENCE = "reference"
    TIME_SERIES = "time_series"
    REFERENCE_CLASS = "reference_model_class"
    REFERENCE_SOURCE_CODE = "reference_source_code"
