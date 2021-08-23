import shutil
from store_data import FolderStore
from typing import Optional
from abstract_control import Control
from fmu_export import export_fmu
from simulate import simulate
from analyze import plot_results
from store_data import store_date, initiate_project, RunCreation
import os
import json
import time


class Workflow:

    def __init__(self):

        self.data = []
        
    def initiate(self, setup_file_path, hdf5_file_name, pid_generator):

        with open(setup_file_path) as file:
            self.setup = json.load(file)  
        
        project_directory = self.setup["project_directory"]
        if self.setup.get("sub_project_folder"):
            working_directory = os.path.join(project_directory, self.setup.get("sub_project_folder"))
        else:
            working_directory = project_directory

        self.project = initiate_project(working_directory, hdf5_file_name, pid_generator)

    def create_run(self, generate_run_name, run_name):

        if self.setup.get("hdf5_run_groups"):
            run_groups = self.setup.get("hdf5_run_groups") 
        else:
            run_groups = ["simulation_results", "plots", "datasheets", "code", "models", "fmus"]
        self.run = RunCreation(self.project, generate_run_name)
        self.run.create_run(run_groups, run_name)
        self.run_directory = os.path.join(self.project.working_directory, self.run.current_run_name)

    def fmu_setup(self):

        for fmu in self.setup["fmus"]:
            if not fmu["directory"]:
                for exp in self.setup["fmu export"]:
                    if exp["model name"] == fmu["model name"]:
                        export_dict = exp
                modeling_environment = export_dict["modeling environment"]
                model_name = export_dict["model name"]
                model_directory = export_dict["model direcotry"]
                packages = export_dict.get("packages")
                datasheet_directory = export_dict.get("datasheet_directory")
                datasheets = export_dict.get("datasheets")
                additional_parameters = export_dict.get("additional_parameters")
                model_modifiers = export_dict.get("model_modifiers")
                env_path = self.setup["dymola path"] if modeling_environment == "d" else None
                export_fmu(modeling_environment, model_name, model_directory, env_path, self.run_directory, 
                                        datasheet_directory, datasheets, additional_parameters, model_modifiers, packages)
                fmu["directory"] = self.run_directory 

    def control_setup(self, control_classes):

        if self.setup.get("controls"):
            for control in self.setup["controls"]:
                control_name = control["control name"]
                control["control class"] = control_classes[control_name]

    def simulate(self, stop_time, step_size, start_time = 0):

        self.results = simulate(stop_time, step_size, fmus_info = self.setup.get("fmus"), controls_info = self.setup.get("controls"), result_var= self.setup.get("record"), start_time= start_time)

    def save_plots(self, type = "png", group: str = "plots"):

        plots = []
        if self.setup.get("plots"):
            for plot in self.setup["plots"]:
                x_data = self.results[plot["x"]] 
                if isinstance(plot["y"], list):
                    y_data = [self.results[sub] for sub in plot["y"]]
                    ax = plot_results(y = y_data, x= x_data, title= plot["title"], x_label= plot.get("x_label"), 
                                        y_label = plot.get("y_label"), legend= plot.get("legend"), 
                                        style_sheet_path = self.setup["style_sheet_path"])
                else:
                    y_data = self.results[plot["y"]]
                    ax = plot_results(y = [y_data], x= x_data, title= plot["title"], x_label= plot.get("x_label"), 
                                        y_label = plot.get("y_label"), legend= plot.get("legend"), 
                                        style_sheet_path = self.setup["style_sheet_path"])
                pid = self.project.pid_generator("plot")
                plot_data = {"pid": pid, "title" : plot["title"], "x_label": plot.get("x_label"), "y_label": plot.get("y_label")}
                plots.append(plot_data)
                fig = ax.get_figure()
                pid = self.project.pid_generator("plot")
                path = os.path.join(self.run_directory, pid +"." + type)
                if os.path.exists(path):
                    time.sleep(1)
                    pid = self.project.pid_generator("plot")
                    path = os.path.join(self.run_directory, pid +"." + type)
                fig.savefig(path)

        for plot in plots:
            attr = {k:v for k,v in plot.items() if k not in ["pid", "title"]}
            self.append_data(plot["title"], plot["pid"], group, attr)

    def save_simulation_results(self, group: str = "simulation_results"):

        variable_list = list(self.results.columns)

        for var in variable_list:
            if var != "time":
                rec = self.results[["time", var]].to_records(index= False)
                self.append_data(var, rec, group) #TODO attr

    def save_fmus(self, group = "fmus"):
        
        self.fmus = []
        for fmu in self.setup["fmus"]:
            fmu_pid = self.project.pid_generator("fmu")
            old_path = os.path.join(fmu["directory"], fmu["model name"] +".fmu")
            new_path = os.path.join(self.run_directory, fmu_pid +".fmu")
            if os.path.exists(new_path):
                time.sleep(1)
                fmu_pid = self.project.pid_generator("fmu")
                new_path = os.path.join(self.run_directory, fmu_pid +".fmu")
            if os.path.normpath(fmu["directory"]) == os.path.normpath(self.run_directory):
                os.rename(old_path, new_path)
            else:
                shutil.copy(old_path, new_path)
            self.append_data(fmu["model name"], fmu_pid, group)

    def append_data(self, data_name, data, hdf5_folder_name, attr = None):

            data_dict = {}
            data_dict["data name"] = data_name
            data_dict["data"] = data
            data_dict["hdf5_folder_name"] = hdf5_folder_name
            if attr:
                data_dict["attr"] = attr          
            self.data.append(data_dict)

    def store_data_in_hdf5(self):

        store_date(self.project, self.run, self.data)

def workflow(setup_file_path,stop_time, step_size, plot_type= "png",start_time = 0, control_classes = None, hdf5_file_name = None, pid_generator = None, generate_run_name = None, run_name = None):

    wf = Workflow()
    wf.initiate(setup_file_path, hdf5_file_name, pid_generator)
    wf.create_run(generate_run_name, run_name)
    wf.fmu_setup()
    if control_classes:
        wf.control_setup(control_classes)

    wf.simulate(stop_time, step_size, start_time)
    wf.save_plots(plot_type)
    wf.save_simulation_results()
    wf.save_fmus()
    wf.store_data_in_hdf5()

