import shutil
from typing import Optional
import sys
from abstract_control import Control
from fmu_export import export_fmu
from simulate import simulate
from analyze import plot_results
from store_data import store_data, Project
import os
import json
import time


class Workflow:

    def __init__(self, setup_file_path):

        self.setup_file_path = setup_file_path
        self.data = []
        
    def initiate(self, hdf5_file_name, pid_generator, run_name_generator):

        with open(self.setup_file_path) as file:
            self.setup = json.load(file)  
        
        working_directory = self.setup["project directory"]

        self.project = Project(working_directory, hdf5_file_name, pid_generator, run_name_generator)

    def create_run(self, run_name, run_groups: list = None, attr = None):

        if not run_groups:
            run_groups = ["simulation_results", "plots", "datasheets", "code", "models", "fmus"]

        self.project.create_run(run_groups, run_name, attr)
        self.run_directory = os.path.join(self.project.working_directory, self.project.current_run_name)

    def fmu_setup(self):

        for fmu in self.setup["fmus"]:
            if not fmu["path"]:
                for exp in self.setup["fmu export"]:
                    if exp["model name"] == fmu["model name"]:
                        export_dict = exp
                        break
                modeling_environment = export_dict["modeling environment"]
                model_name = export_dict["model name"]
                model_directory = export_dict["model directory"]
                packages = export_dict.get("packages")
                datasheet_directory = export_dict.get("datasheet directory")
                datasheets = export_dict.get("datasheets")
                additional_parameters = export_dict.get("additional parameters")
                model_modifiers = export_dict.get("model modifiers")
                env_path = self.setup["dymola path"] if modeling_environment == "d" else None
                output_directory =  self.run_directory
                fmu_export = export_fmu(modeling_environment, model_name, model_directory, env_path, output_directory, 
                                        datasheet_directory = datasheet_directory, datasheets = datasheets, 
                                        additional_parameters = additional_parameters, model_modifiers = model_modifiers, packages = packages)
                fmu["path"] = fmu_export.fmu_path
                fmu["store copy"] = export_dict.get("store copy")
                # add new path to json file
                self.add_path_to_json(os.path.join(fmu["store copy"], os.path.basename(fmu["path"])), fmu["model name"])

    def add_path_to_json(self, path, name):

        with open(self.setup_file_path) as file:
            data = json.load(file) 

        for fmu in data["fmus"]:
            if fmu["model name"] == name:
                fmu["path"] = path
                break

        with open(self.setup_file_path, "w") as file:
            json.dump(data, file)       

    def control_setup(self, control_classes):

        if self.setup.get("controls"):
            for control in self.setup["controls"]:
                control_name = control["control name"]
                control["control class"] = control_classes[control_name]

    def simulate(self, stop_time, step_size, start_time = None):

        if not start_time:
            start_time = 0
        self.results, self.units = simulate(stop_time, step_size, fmus_info = self.setup.get("fmus"), controls_info = self.setup.get("controls"), result_var= self.setup.get("record"), start_time= start_time, get_units= True)

    def save_plots(self, type = None, group: str = None):

        if not type:
            type = "png"
        if not group:
            group = self.project.current_run_name + "/plots"

        plots = []
        if self.setup.get("plots"):
            for plot in self.setup["plots"]:
                x_data = self.results[plot["x"]] 
                if isinstance(plot["y"], list):
                    y_data = [self.results[sub] for sub in plot["y"]]
                    ax = plot_results(y = y_data, x= x_data, title= plot["title"], x_label= plot.get("x_label"), 
                                        y_label = plot.get("y_label"), legend= plot.get("legend"), 
                                        style_sheet_path = self.setup.get("style sheet path"))
                else:
                    y_data = self.results[plot["y"]]
                    ax = plot_results(y = [y_data], x= x_data, title= plot["title"], x_label= plot.get("x_label"), 
                                        y_label = plot.get("y_label"), legend= plot.get("legend"), 
                                        style_sheet_path = self.setup.get("style sheet path"))
                pid = self.project.pid_generator("plot")
                plot_data = {"pid": pid, "title" : plot["title"], "x_label": plot.get("x_label"), "y_label": plot.get("y_label")}
                plots.append(plot_data)
                fig = ax.get_figure()
                pid = self.project.pid_generator("plot")
                path = os.path.join(self.run_directory, pid +"." + type)
                if os.path.exists(path):
                    time.sleep(1)
                    pid = self.project.pid_generator("plot", title = plot["title"])
                    path = os.path.join(self.run_directory, pid +"." + type)
                fig.savefig(path)

        for plot in plots:
            attr = {k:v for k,v in plot.items() if k not in ["pid", "title"]}
            self.append_data(plot["title"], plot["pid"], group, attr)

    def save_simulation_results(self, group: str = None):

        if not group:
            group =  self.project.current_run_name + "/simulation_results"
        variable_list = list(self.results.columns)

        for var in variable_list:
            if var != "time":
                rec = self.results[["time", var]].to_records(index= False)
                if self.units.get(var):
                    attr = {"unit": self.units[var]}
                    self.append_data(var, rec, group, attr)
                else:
                    self.append_data(var, rec, group)

                

    def save_fmus(self, group = None):
        
        if not group:
            group =  self.project.current_run_name +"/fmus"
        self.fmus = []
        for fmu in self.setup["fmus"]:
            fmu_pid = self.project.pid_generator("fmu", model_name = fmu["model name"])
            old_path = fmu["path"]
            if fmu.get("store copy"):
                fmu_copy_path = os.path.normpath(fmu.get("store copy") + "/" + os.path.basename(old_path))
                if os.path.exists(fmu_copy_path):
                    while True:
                        overwrite = input(f"The path {fmu_copy_path} already exists. Overwrite? [y/n]")
                        if overwrite == "y" or overwrite == "n":
                            if overwrite == "y":
                                break
                            elif overwrite == "n":
                                raise FileExistsError
                            else:
                                print("Enter 'y' or 'n'.")
                shutil.copy(old_path, fmu["store copy"])

            new_path = os.path.join(self.run_directory, fmu_pid +".fmu")
            if os.path.exists(new_path):
                time.sleep(1)
                fmu_pid = self.project.pid_generator("fmu")
                new_path = os.path.join(self.run_directory, fmu_pid +".fmu")
            if os.path.normpath(os.path.dirname(old_path)) == os.path.normpath(self.run_directory):
                os.rename(old_path, new_path)
            else:
                shutil.copy(old_path, new_path)
            self.append_data(fmu["model name"], fmu_pid, group)

    def append_data(self, data_name, data, hdf5_folder_name, attr = None):

            data_dict = {}
            data_dict["data_name"] = data_name
            data_dict["data"] = data
            data_dict["hdf5_folder_name"] = hdf5_folder_name
            if attr:
                data_dict["attr"] = attr          
            self.data.append(data_dict)

    def save_models(self):
        pass

    def store_data_in_hdf5(self):

        for data in self.data:

            store_data(self.project.hdf5_path,data["data"], data["data_name"], data["hdf5_folder_name"], data.get("attr"))

def workflow(setup_file_path,stop_time, step_size, control_classes = None, hdf5_group_attr = None, **kwargs):


    try:
        wf = Workflow(setup_file_path)
        wf.initiate(kwargs.get("hdf5_file_name"), kwargs.get("pid_generator"), kwargs.get("run_name_generator"))
        wf.create_run(kwargs.get("generate_run_name"), kwargs.get("run_name"), hdf5_group_attr)
        wf.fmu_setup()
        if control_classes:
            wf.control_setup(control_classes)
        wf.simulate(stop_time, step_size, kwargs.get("start_time"))
        wf.save_plots(kwargs.get("plot_type"), kwargs.get("plotting_function"))
        wf.save_simulation_results(kwargs.get("result_group"))
        wf.save_fmus(kwargs.get("fmu_group"))
        wf.store_data_in_hdf5()

    except Exception as e:
        ecx_type, value, _  = sys.exc_info()
        while True:
            delete = input(f"Following error occurred: {ecx_type.__name__}: {value}. Delete run? [y/n]")
            if delete == "y" or delete == "n":
                if delete == "y":
                    wf.project.delete_run(wf.project.current_run_name)
                else:
                    print("The run will not be deleted.")
                break
            else:
                print("Enter 'y' or 'n'")
        raise e