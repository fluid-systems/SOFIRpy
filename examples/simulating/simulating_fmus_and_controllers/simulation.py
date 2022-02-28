from fair_sim import simulate
from controller import PID
import os
import json

setup_file = os.path.join(os.path.dirname(__file__), 'setup.json'),
system_infos = json.load(setup_file)
fmu_infos = system_infos["fmu_infos"]
control_infos = system_infos["control_infos"]
parameters_to_log = system_infos["parameters to log"]
pid = PID()
control_classes = {"name": PID}

stop_time = 20
step_size = 1e-4

results, unit = simulate(stop_time, step_size, fmu_infos, control_infos, control_classes, parameters_to_log, get_units=True)