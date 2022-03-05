from pathlib import Path
import json
from datetime import datetime
import pandas as pd
from fair_sim import simulate, Project, plot_results, HDF5

# This example illustrates how a workflow can be implemented to automatically 
# simulate and store the results.

def generate_run_name(number_of_runs: int) -> str:
    return f"Run_{number_of_runs+1}"

def generate_pid(file_name: str) -> str:
    time_stamp = datetime.now().strftime("%y%m%d%H%M%S") 
    return f"{time_stamp}_{file_name}"

def get_number_run_in_hdf5(hdf5: HDF5) -> int:
    return len(list(hdf5.get_hdf5_structure().keys()))

def store_simulation_resuts(results: pd.DataFrame, units: dict[str, str], hdf5: HDF5, folder_name) -> None:

    variable_list = list(results.columns)

    for var in variable_list:
        if var != "time":
            rec = results[["time", var]].to_records(index=False)
            attr = None
            if units.get(var):
                attr = {"unit": units[var]}
            
            hdf5.store_data(var, rec, folder_name, attr)
 
def store_plots() -> None:...


if __name__ == "__main__":
    json_path = ""
    simulation_data = json.load(json_path)["simulation"]
    fmu_infos = simulation_data["fmu_infos"]
    control_infos = simulation_data["control_infos"]
    parameters_to_log = simulation_data["parameters_to_log"]
    control_classes = {}
    stop_time = 10
    step_size = 1e-3
    results, units = simulate(
        stop_time,
        step_size,
        fmu_infos,
        control_infos,
        control_classes,
        parameters_to_log, 
        get_units=True)

    # initialize the project
    hdf5_path = Path()
    project_directory = Path()
    project = Project(project_directory, hdf5_path)

    # create a new folder
    number_of_runs = get_number_run_in_hdf5(project.hdf5)
    folder_name = generate_run_name(number_of_runs)
    project.create_folder(folder_name)

    # store results
    store_simulation_resuts(results, units, project.hdf5, folder_name)
    # plot results and store them
    store_plots(json_path["plots"], results)

    # store additional files
