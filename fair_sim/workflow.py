import shutil
import sys
from typing import Any, Callable, Optional
from fair_sim.fmu_export import export_fmu
from fair_sim.simulate import simulate
from fair_sim.plot import plot_results
from fair_sim.store_data import store_data, append_attributes
from fair_sim.project import Project
import os
import json
import time
import numpy as np


class WorkflowInitiation:
    def __init__(self, setup_file_path: str) -> None:

        self.setup_file_path = setup_file_path

    @property
    def setup_file_path(self) -> str:
        return self._setup_file_path

    @setup_file_path.setter
    def setup_file_path(self, path: str) -> None:

        file_extension = os.path.splitext(path)[1]
        if file_extension != ".json":
            raise FileTypeError("The 'setup_file_path' needs to end with .json")
        if not os.path.exists(path):
            raise FileNotFoundError(f"The path '{path}' does not exist.")

        self._setup_file_path = os.path.normpath(path)

    def initiate(self, hdf5_file_name: str, pid_generator, run_name_generator) -> None:

        with open(self.setup_file_path) as file:
            self.setup = json.load(file)

        working_directory = self.setup["project directory"]

        self.project = Project(
            working_directory, hdf5_file_name, pid_generator, run_name_generator
        )

    def create_run(
        self,
        run_groups: list = None,
        run_name: str = None,
        attr=None,
        create_run_folder=True,
    ) -> None:

        if not run_groups:
            run_groups = [
                "simulation_results",
                "plots",
                "datasheets",
                "code",
                "models",
                "fmus",
            ]

        self.project.create_run(run_groups, run_name, attr, create_run_folder)
        self.run_directory = os.path.join(
            self.project.working_directory, self.project.current_run_name
        )


class FmuSetup:
    def __init__(self, init: WorkflowInitiation) -> None:

        self.init = init

    def export_fmus(self) -> None:  # TODO if save_fmus set to false

        for fmu in self.init.setup["fmus"]:
            if not fmu["path"]:
                if not self.init.setup.get("fmu export"):
                    raise KeyError(
                        "If the path for a fmu is not defined the json file needs the key 'fmu export' for the corresponding fmu."
                    )
                else:
                    for exp_dict in self.init.setup["fmu export"]:
                        if exp_dict["model name"] == fmu["model name"]:
                            fmu["path"] = self._export_fmu(exp_dict)
                            if exp_dict.get("store copy"):
                                self.store_fmu_copy(
                                    fmu["path"],
                                    exp_dict["store copy"],
                                    fmu["model name"],
                                )
                            break

    def _export_fmu(self, export_dict: dict) -> str:

        modeling_environment = export_dict["modeling environment"]
        model_name = export_dict["model name"]
        model_directory = export_dict["model directory"]
        packages = export_dict.get("packages")
        datasheet_directory = export_dict.get("datasheet directory")
        datasheets = export_dict.get("datasheets")
        additional_parameters = export_dict.get("additional parameters")
        model_modifiers = export_dict.get("model modifiers")
        env_path = (
            self.init.setup.get("dymola path")
            if modeling_environment.lower().startswith("d")
            else None
        )
        output_directory = self.init.run_directory
        fmu = export_fmu(
            modeling_environment,
            model_name,
            model_directory,
            output_directory,
            env_path,
            datasheet_directory=datasheet_directory,
            datasheets=datasheets,
            additional_parameters=additional_parameters,
            model_modifiers=model_modifiers,
            packages=packages,
        )
        return fmu.fmu_path

    def store_fmu_copy(self, src_path: str, dest_dir: str, model_name: str) -> None:

        dest_path = os.path.join(dest_dir, os.path.basename(src_path))
        if os.path.exists(dest_path):
            while True:
                overwrite = input(
                    f"The path {dest_path} already exists. Overwrite? [y/n]"
                )
                if overwrite == "y" or overwrite == "n":
                    if overwrite == "y":
                        break
                    elif overwrite == "n":
                        raise FileExistsError
                    else:
                        print("Enter 'y' or 'n'.")
        shutil.copy(src_path, dest_path)
        self.add_path_to_json(dest_path, model_name)

    def add_path_to_json(self, path: str, model_name: str) -> None:

        with open(self.init.setup_file_path) as file:
            data = json.load(file)

        for fmu in data["fmus"]:
            if fmu["model name"] == model_name:
                fmu["path"] = path
                break

        with open(self.init.setup_file_path, "w") as file:
            json.dump(data, file)


class Simulation:
    def __init__(self, init: WorkflowInitiation):

        self.init = init

    def control_setup(self, control_classes: dict = None) -> None:

        if control_classes:
            if self.init.setup.get("controls"):
                for control in self.init.setup["controls"]:
                    control_name = control["control name"]
                    control["control class"] = control_classes[control_name]

            else:
                raise KeyError("The setup file is missing the key 'controls'")

        if not control_classes and self.init.setup.get(
            "controls"
        ):  # TODO name Exception
            raise Exception(
                "Controllers are specified in json file but no control classes are passed to the workflow function."
            )

    def _simulate(
        self, stop_time: float, step_size: float, control_classes: dict = None, start_time: float=None
    ) -> None:

        if not start_time:
            start_time = 0
        self.control_setup(control_classes)

        self.results, self.units = simulate(
            stop_time,
            step_size,
            fmus_info=self.init.setup.get("fmus"),
            controls_info=self.init.setup.get("controls"),
            result_var=self.init.setup.get("record"),
            start_time=start_time,
            get_units=True,
        )


class SaveData:
    def __init__(self, init: WorkflowInitiation, sim: Simulation) -> None:

        self.init = init
        self.sim = sim

    def plot(self, plot_func=None, img_type: str = None, group: str = None) -> None:

        if not plot_func:
            plot_func = plot_results

        if self.init.setup.get("plots"):
            for plot in self.init.setup["plots"]:
                x_data = self.sim.results[plot["x"]]
                title = plot["title"]
                if isinstance(plot["y"], list):
                    y_data = [self.sim.results[sub] for sub in plot["y"]]
                    ax = plot_results(
                        y=y_data,
                        x=x_data,
                        title=title,
                        x_label=plot.get("x_label"),
                        y_label=plot.get("y_label"),
                        legend=plot.get("legend"),
                        style_sheet_path=self.init.setup.get("style sheet path"),
                    )
                else:
                    y_data = self.sim.results[plot["y"]]
                    ax = plot_results(
                        y=y_data,
                        x=x_data,
                        title=title,
                        x_label=plot.get("x_label"),
                        y_label=plot.get("y_label"),
                        legend=plot.get("legend"),
                        style_sheet_path=self.init.setup.get("style sheet path"),
                    )
                attr = {k: v for k, v in plot.items() if k not in ["title"]}
                self.save_plot(ax.get_figure(), title, img_type, group, attr)

    def save_plot(self, fig, title: str, img_type: str, group: str, attr: dict) -> None:

        if not img_type:
            img_type = "png"

        if not group:
            group = "plots"

        group = self.init.project.current_run_name + "/" + group

        plot_pid = self.init.project.pid_generator("plot", title=title)
        plot_path = os.path.join(self.init.run_directory, plot_pid + "." + img_type)
        if os.path.exists(plot_path):
            time.sleep(1)
            plot_pid = self.init.project.pid_generator("plot", title=title)
            plot_path = os.path.join(self.init.run_directory, plot_pid + "." + img_type)
        fig.savefig(plot_path)

        self.store_data_in_hdf5([['file name',plot_pid]], title, group, attr)

    def save_simulation_results(self, group: str = None) -> None:

        if not group:
            group = "simulation_results"
        
        group = self.init.project.current_run_name + "/" + group

        variable_list = list(self.sim.results.columns)

        for var in variable_list:
            if var != "time":
                rec = self.sim.results[["time", var]].to_records(index=False)
                if self.sim.units.get(var):
                    attr = {"unit": self.sim.units[var]}
                    self.store_data_in_hdf5(rec, var, group, attr)
                else:
                    self.store_data_in_hdf5(rec, var, group)

    def save_fmus(self, group: str = None) -> None:

        if not group:
            group = "fmus"
        
        group = self.init.project.current_run_name + "/" + group
        

        for fmu in self.init.setup["fmus"]:
            fmu_pid = self.init.project.pid_generator(
                "fmu", model_name=fmu["model name"]
            )
            old_path = fmu["path"]
            new_path = os.path.join(self.init.run_directory, fmu_pid + ".fmu")
            if os.path.exists(new_path):
                time.sleep(1)
                fmu_pid = self.init.project.pid_generator(
                    "fmus", model_name=fmu["model name"]
                )
                new_path = os.path.join(self.init.run_directory, fmu_pid + ".fmu")
            if os.path.normpath(os.path.dirname(old_path)) == os.path.normpath(
                self.init.run_directory
            ):
                os.rename(old_path, new_path)
            else:
                shutil.copy(old_path, new_path)

            self.store_data_in_hdf5([['file name',fmu_pid]], fmu["model name"], group)

    def save_controller_data(self, control_classes: dict, group: str = None):

        if not control_classes:
            return
        if not group:
            group = "code/instances"

        loc = self.init.project.current_run_name + "/" + group
        self.init.project.create_hdf5_group(loc)
        
        for name, controller in control_classes.items():
            self.store_data_in_hdf5([['class name', type(controller).__name__]], name, loc)
            if hasattr(controller, "__input_arguments__"):
                data_path = loc + "/" + name
                for input_name, input_value in controller.__input_arguments__.items():
                    try:
                        append_attributes(self.init.project.hdf5_path, data_path, {input_name: input_value})
                    except TypeError:
                        append_attributes(self.init.project.hdf5_path, data_path, {input_name: f'Type {type(input_value)} can not be stored'})
                        
    def save_files(self) -> None:

        if self.init.setup["save additional files"]:
            for file in self.init.setup["save additional files"]:
                group = self.init.project.current_run_name + "/" + file["group"]
                _, extension = os.path.splitext(file["path"])
                file_name = os.path.basename(file["path"]).split(".")[0]
                if file["pid"]:
                    pid = name = self.init.project.pid_generator(file["type"])
                    copy_path = os.path.join(self.init.run_directory, pid + extension)
                    if os.path.exists(copy_path):
                        time.sleep(1)
                        pid = name = self.init.project.pid_generator(file["type"])
                        copy_path = os.path.join(
                            self.init.run_directory, pid + extension
                        )
                else:
                    name = file_name
                    copy_path = os.path.join(
                        self.init.run_directory, os.path.basename(file["path"])
                    )

                shutil.copy(file["path"], copy_path)
                self.store_data_in_hdf5([['file name', name]], file_name, group)

    def store_data_in_hdf5(self, data: Any, data_name: str, folder: str, attr: dict =None) -> None:

        store_data(self.init.project.hdf5_path, data, data_name, folder, attr)


def workflow(
    setup_file_path: str,
    stop_time: float,
    step_size: float,
    control_classes: dict=None,
    hdf5_groups: list=None,
    hdf5_group_attr: dict=None,
    create_run_folder: bool=True,
    save_fmus: bool=True,
    save_plots: bool=True,
    save_simulation_results: bool=True,
    save_controller_data: bool = True,
    **kwargs,
) -> None:

    init = WorkflowInitiation(setup_file_path)
    init.initiate(
        kwargs.get("hdf5_file_name"),
        kwargs.get("pid_generator"),
        kwargs.get("run_name_generator"),
    )

    try:
        init.create_run(
            hdf5_groups, kwargs.get("run_name"), hdf5_group_attr, create_run_folder
        )
        fmu_setup = FmuSetup(init)
        fmu_setup.export_fmus()
        sim = Simulation(init)
        sim._simulate(stop_time, step_size, control_classes, kwargs.get("start_time"))
        save = SaveData(init, sim)
        if save_plots:
            save.plot(
                kwargs.get("plotting_function"),
                kwargs.get("img_type"),
                kwargs.get("plot_group"),
            )  # TODO arguments
        if save_fmus:
            save.save_fmus(kwargs.get("fmu_group"))
        if save_simulation_results:
            save.save_simulation_results(kwargs.get("simulation_results_group"))
        if save_controller_data:
            save.save_controller_data(control_classes)

        save.save_files()
    except Exception as e:
        ecx_type, value, _ = sys.exc_info()
        while True:
            delete = input(
                f"Following error occurred: {ecx_type.__name__}: {value}. Delete run? [y/n]"
            )
            if delete == "y" or delete == "n":
                if delete == "y":
                    init.project.delete_run(init.project.current_run_name)
                else:
                    print("The run will not be deleted.")
                break
            else:
                print("Enter 'y' or 'n'")
        raise e

def get_hdf5_project(working_directory):
    return Project(working_directory)

class FileTypeError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)

class NothingToDeleteError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)