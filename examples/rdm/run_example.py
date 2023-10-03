import os
import sys
from pathlib import Path

from sofirpy import Run

sys.path.append(os.path.join(os.path.dirname(__file__), "../"))

from discrete_pid import PID

# Simulating and storing a run to a hdf5
run_name = "Run_1"

config_path = Path(__file__).parent / "example_config.json"

model_classes = {"pid": PID}

if sys.platform == "win32":
    fmu_path = Path(__file__).parent.parent / "DC_Motor.fmu"
elif sys.platform == "darwin":
    fmu_path = Path(__file__).parent.parent / "DC_Motor_mac.fmu"

fmu_paths = {"DC_Motor": fmu_path}

run = Run.from_config_file(run_name, config_path, fmu_paths, model_classes)

run.simulate()

hdf5_path = Path(__file__).parent / "run_example.hdf5"

run.to_hdf5(hdf5_path)

# Loading the run from the hdf5
run_loaded = Run.from_hdf5(run_name, hdf5_path)
