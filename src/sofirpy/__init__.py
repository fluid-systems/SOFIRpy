"""Framework for simulating FMUs and custom models written in python."""

__author__ = "Daniele Inturri"
__email__ = "daniele.inturri@stud.tu-darmstadt.de"
__version__ = "2.0.0a2"

__all__ = [
    "HDF5",
    "BaseRecorder",
    "BaseSimulator",
    "FixedSizedRecorder",
    "Run",
    "SimulationEntity",
    "VariableSizeRecorder",
    "export_dymola_model",
    "export_open_modelica_model",
    "plot_results",
    "simulate",
]

from .fmu_export.dymola_fmu_export import export_dymola_model
from .fmu_export.open_modelica_fmu_export import export_open_modelica_model
from .rdm.hdf5.hdf5 import HDF5
from .rdm.run import Run
from .simulation.plot import plot_results
from .simulation.recorder import BaseRecorder, FixedSizedRecorder, VariableSizeRecorder
from .simulation.simulation import BaseSimulator, simulate
from .simulation.simulation_entity import SimulationEntity
