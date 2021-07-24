
import numpy as np
import copy
import sys
import os
from abstract_control import Control



class FMU():

    def __init__(self, model_name, fmu_directory):
        self.model_name = model_name
        self.fmu_path = os.path.join(fmu_directory, model_name + ".fmu")
        
    def init_fmu(self):
        
        from fmpy import read_model_description, extract
        from fmpy.fmi2 import FMU2Slave 

        model_description = read_model_description(self.fmu_path)

        self.model_vars = {variable.name : variable.valueReference for variable in model_description.modelVariables}
        
        self.unit_vars = {variable.name : variable.unit for variable in model_description.modelVariables}
        
        
        unzipdir = extract(self.fmu_path)
        self.fmu = FMU2Slave(guid=model_description.guid,
                    unzipDirectory=unzipdir,
                    modelIdentifier=model_description.coSimulation.modelIdentifier,
                    instanceName='instance1') 

        self.fmu.instantiate()
        self.fmu.setupExperiment(startTime=0)
        self.fmu.enterInitializationMode()
        self.fmu.exitInitializationMode()
        print(f'FMU {self.model_name} initialized.')
            
    def set_input(self,input_name, input_value):
        
        self.fmu.setReal([self.model_vars[input_name]], [input_value])

    def get_output(self, variable_name):
        
        return self.fmu.getReal([self.model_vars[variable_name]])[0]
         
    def do_step(self, time, step_size):

        self.fmu.doStep(currentCommunicationPoint=time,communicationStepSize=step_size)

    def conclude_simulation_process(self):

        self.fmu.terminate()
        self.fmu.freeInstance()





class Simulation():
    
    def __init__(self, stop_time, step_size, result_var_dict = {}, fmu_dict = {}, controls = {}): #TODO check if works with empty dict

        self.fmu_model_names = list(fmu_dict.keys())
        self.fmu_directorys = [sub["directory"] for sub in list(fmu_dict.values())]
        self.fmu_connections = [sub["inputs"] for sub in list(fmu_dict.values())]
        self.fmu_dict = copy.deepcopy(fmu_dict)
        self.fmu_classes_dic= copy.deepcopy(fmu_dict)
        for name in self.fmu_classes_dic.keys():
            self.fmu_classes_dic[name] = ""
        for name, con in zip(fmu_dict.keys(), self.fmu_connections):
            self.fmu_dict[name] = con   
        

        self.control_connections = [sub["inputs"] for sub in list(controls.values())]
        self.control_dic = copy.deepcopy(controls)
        for name, con in zip(self.control_dic, self.control_connections):
            self.control_dic[name] = con 
        self.control_classes_dic = copy.deepcopy(controls)
        self.control_classes = [sub["class"] for sub in list(controls.values())]
        for name, _class in zip(self.control_classes_dic.keys(), self.control_classes):
            self.control_classes_dic[name] = _class
        
        self.time_series = np.arange(0, stop_time + step_size, step_size)
        self.step_size = step_size
        self.stop_time = stop_time
        self.result_var_dict = result_var_dict
        self.result_dict = copy.deepcopy(result_var_dict)

    
    def check_control_class(self):
        
        for _class in self.control_classes:
            if not isinstance(_class, Control):
                raise ControlClassInheritError(f"The class '{type(_class).__name__}' needs to inherit from the Control class. Import Control from abstract_control to get the class")

    def initialise_fmus(self):

        print("Initialise FMUs...")
        for name, direc in zip(self.fmu_model_names, self.fmu_directorys):
            fmu = FMU(name, direc)
            fmu.init_fmu()
            self.fmu_classes_dic[name] = fmu   
        print("FMUs initialised.")

    def connect_systems(self):
        
        print("Connecting Systems...")

        self.all_system_classes = self.fmu_classes_dic.copy()
        self.all_system_classes.update(self.control_classes_dic)
        
        for name in self.control_dic:
            for connected_system in self.control_dic[name]:
                connected_system[1] = self.all_system_classes[connected_system[1]]
        
        
        for name in self.fmu_dict:
            for connected_system in self.fmu_dict[name]:
                connected_system[1] = self.all_system_classes[connected_system[1]] 
            

        print("All systems connected.")

    def simulate(self):

        from alive_progress import alive_bar
        print("Starting Simulation...")

        with alive_bar(len(self.time_series), bar= 'blocks', spinner='classic') as bar:
            for time_step, time in enumerate(self.time_series):

                self.set_control_inputs()
                self.generate_control_output()
                self.set_fmu_inputs()
                self.record_values(time_step, time)
                self.fmu_do_step(time)
                
                bar()

        for fmu in self.fmu_classes_dic.values():
            fmu.conclude_simulation_process()

        print("Simulation completed.")

        return  self.result_dict, self.convert_results_to_pandas()
        
    def set_control_inputs(self):
        
        for name in self.control_dic:
            for inp in self.control_dic[name]:
                input_name = inp[0]
                connected_system = inp[1]
                connected_variable = inp[2]
                input_value = connected_system.get_output(connected_variable)
                self.control_classes_dic[name].set_input(input_name,input_value)

    def fmu_do_step(self, time):

        for fmu in self.fmu_classes_dic.values():
                fmu.do_step(time, self.step_size)

    def generate_control_output(self):
        
        for control in self.control_classes:
            control.generate_output()
    
    def set_fmu_inputs(self):
        
        for name in self.fmu_dict:
            for inp in self.fmu_dict[name]:
                input_name = inp[0]
                connected_system = inp[1]
                connected_variable = inp[2]
                input_value = connected_system.get_output(connected_variable)
                self.fmu_classes_dic[name].set_input(input_name,input_value)
    
    def create_result_dict(self):
        
        for system in self.result_var_dict:
            zero_list = [np.zeros((len(self.time_series), 2)) for i in range(len(self.result_dict[system]))]
            self.result_dict[system] = {variable_name:zero_array for (variable_name, zero_array) in zip(self.result_var_dict[system], zero_list)}
            
                
        
    def record_values(self,time_step, time):
        
        for system_name in self.result_dict:
            for var in self.result_dict[system_name]:
                value = self.all_system_classes[system_name].get_output(var) 
                self.result_dict[system_name][var][time_step] = [time, value]
            
    def convert_results_to_pandas(self):

        import pandas as pd

        result_dataframe = pd.DataFrame(self.time_series, columns = ["time"])

        for system_name in self.result_dict:
            for var in self.result_dict[system_name]:
                result_dataframe[system_name +"." + var] = self.result_dict[system_name][var][:,1] 

        return result_dataframe

    def create_unit_dic(self):

        unit_dic = {}
        for system_name in self.result_dict:
            for var in self.result_dict[system_name]:
                if system_name in self.fmu_classes_dic:
                    unit = self.fmu_classes_dic[system_name].unit_vars[var]
                    unit_dic[system_name + "." + var] = unit


        return unit_dic


class ControlClassInheritError(Exception):

    def __init__(self, message):
        self.message = message
        super().__init__(message)
