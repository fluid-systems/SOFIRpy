import numpy as np
import pandas as pd
import copy
import os
from abstract_control import Control
from fmpy import read_model_description, extract
from fmpy.fmi2 import FMU2Slave 
from alive_progress import alive_bar


class Fmu:

    def __init__(self, model_name: str, fmu_directory: str) -> None:
        self.model_name = model_name
        self.fmu_path = os.path.join(fmu_directory, model_name + ".fmu")

    @property
    def model_name(self) -> str:
        return self._model_name

    @model_name.setter
    def model_name(self, model_name: str) -> None:
        if type(model_name) != str:
            raise TypeError("The model name needs to be a string.")
        self._model_name = model_name

    @property
    def fmu_path(self) -> str:
        return self._fmu_path

    @fmu_path.setter
    def fmu_path(self, fmu_path: str) -> None:
        
        if not os.path.exists(fmu_path):
            raise FileNotFoundError(f"The path '{fmu_path}' does not exist")
        self._fmu_path = fmu_path

    def initialize_fmu(self, start_time: float) -> None:

        self.model_description = read_model_description(self.fmu_path)
        self.create_model_vars_dict()
        self.create_unit_vars_dict()
        unzipdir = extract(self.fmu_path)
        self.fmu = FMU2Slave(guid=self.model_description.guid,
                    unzipDirectory=unzipdir,
                    modelIdentifier=self.model_description.coSimulation.modelIdentifier,
                    instanceName='instance1') 

        self.fmu.instantiate()
        self.fmu.setupExperiment(startTime=start_time)
        self.fmu.enterInitializationMode()
        self.fmu.exitInitializationMode()
        print(f'FMU {self.model_name} initialized.')
    
    def create_model_vars_dict(self) -> None:

        self.model_vars = {variable.name : variable.valueReference for variable in self.model_description.modelVariables}

    def create_unit_vars_dict(self) -> None:

        self.unit_vars = {variable.name : variable.unit for variable in self.model_description.modelVariables}
            
    def set_input(self,input_name: str, input_value: float) -> None:
        
        self.fmu.setReal([self.model_vars[input_name]], [input_value])

    def get_output(self, variable_name: str) -> float:
        
        return self.fmu.getReal([self.model_vars[variable_name]])[0]
         
    def do_step(self, time, step_size: float) -> None:

        self.fmu.doStep(currentCommunicationPoint=time,communicationStepSize=step_size)

    def conclude_simulation_process(self) -> None:

        self.fmu.terminate()
        self.fmu.freeInstance()

    def get_unit(self, variable: str) -> str:

        return self.unit_vars[variable]


class ConnectSystem:

    def __init__(self, fmus: list = [], controls: list = []):
        
        self.fmus = fmus
        self.controls = controls

    def create_all_system_classes_dict(self) -> None:

        self.all_system_classes = {**self.fmu_classes, **self.control_classes}

    def create_control_classes_dict(self) -> None:

        self.control_classes = {control["control name"]: control["control class"] for control in self.controls}

    def check_control_classes(self) -> None:

        for _class in self.control_classes.values():
            if not isinstance(_class, Control):
                raise ControlClassInheritError(f"The class '{type(_class).__name__}' needs to inherit from the Control class. Import Control from abstract_control to get the class")

    def initialise_fmus(self, start_time: float) -> None:

        self.fmu_classes = {}
        for fmu in self.fmus:
            model_name = fmu["model name"]
            model_directory = fmu["directory"]
            fmu_class = Fmu(model_name, model_directory)
            fmu_class.initialize_fmu(start_time)
            self.fmu_classes[model_name] = fmu_class

    def initialize_systems(self, start_time: float) -> None:

        self.initialise_fmus(start_time)
        self.create_control_classes_dict()
        self.check_control_classes()
        self.create_all_system_classes_dict()
   
        for fmu in self.fmus:
            for connection in fmu["connections"]:
                system_name = connection["connect to system"]
                connection["connect to system"] = self.all_system_classes[system_name]
        
        for control in self.controls:
            for connection in control["connections"]:
                system_name = connection["connect to system"]
                connection["connect to system"] = self.all_system_classes[system_name]
              
class Record:... #TODO

class Simulation:
    
    def __init__(self,systems: ConnectSystem, result_var_dict: dict = {}): #TODO check if works with empty dict

        self.systems = systems
        self.result_var_dict = result_var_dict
        self.result_dict = copy.deepcopy(result_var_dict)
          
    def simulate(self,stop_time, step_size, start_time = 0):

        self.systems.initialize_systems(start_time)
        self.time_series = np.arange(start_time, stop_time + step_size, step_size)
        self.create_result_dict()

        print("Starting Simulation...")
        with alive_bar(len(self.time_series), bar= 'blocks', spinner='classic') as bar:
            for time_step, time in enumerate(self.time_series):

                self.set_control_inputs()
                self.generate_control_output()
                self.set_fmu_inputs()
                self.record_values(time_step, time)
                self.fmu_do_step(time, step_size)
                bar()
                
        self.conclude_fmu_simulation()
       
        print("Simulation completed.")

        return  self.convert_results_to_pandas()
        
    def set_control_inputs(self):
        
        for control in self.systems.controls:
            for connection in control["connections"]:
                input_name = connection["input name"]
                connected_system = connection["connect to system"]
                connected_variable = connection["connect to variable"]
                input_value = connected_system.get_output(connected_variable)
                self.systems.control_classes[control["control name"]].set_input(input_name,input_value)

    def fmu_do_step(self, time, step_size):

        for fmu in self.systems.fmu_classes.values():
                fmu.do_step(time, step_size)

    def generate_control_output(self):
        
        for control in self.systems.control_classes.values():
            control.generate_output()
    
    def set_fmu_inputs(self):
        
        for fmu in self.systems.fmus:
            for connection in fmu["connections"]:
                input_name = connection["input name"]
                connected_system = connection["connect to system"]
                connected_variable = connection["connect to variable"]
                input_value = connected_system.get_output(connected_variable)
                self.systems.fmu_classes[fmu["model name"]].set_input(input_name,input_value)
                
    def conclude_fmu_simulation(self):

         for fmu in self.systems.fmu_classes.values():
            fmu.conclude_simulation_process()

    def create_result_dict(self):
        
        for system in self.result_var_dict:
            zero_list = [np.zeros((len(self.time_series), 2)) for i in range(len(self.result_dict[system]))]
            self.result_dict[system] = {variable_name:zero_array for (variable_name, zero_array) in zip(self.result_var_dict[system], zero_list)}

    def record_values(self,time_step, time):
        
        for system_name in self.result_dict:
            for var in self.result_dict[system_name]:
                value = self.systems.all_system_classes[system_name].get_output(var) 
                self.result_dict[system_name][var][time_step] = [time, value]
            
    def convert_results_to_pandas(self):

        result_dataframe = pd.DataFrame(self.time_series, columns = ["time"])

        for system_name in self.result_dict:
            for var in self.result_dict[system_name]:
                result_dataframe[system_name +"." + var] = self.result_dict[system_name][var][:,1] 

        return result_dataframe

    def get_units(self):

        units = {}
        for system_name in self.result_dict:
            for var in self.result_dict[system_name]:
                unit = self.systems.all_system_classes[system_name].get_unit(var)
                units[system_name + "." + var] = unit

        return units

def simulate(stop_time, step_size, fmus: list = [], controls: list = [], result_var: dict = {}, start_time = 0, get_units = False):

    if not fmus and not controls:
        raise NoSystemToSimulateDefined("No System to simulate given as argument.")
    systems = ConnectSystem(fmus, controls)
    sim = Simulation(systems, result_var)
    results = sim.simulate(stop_time, step_size, start_time)
    if get_units:
        units = sim.get_units()
        return results, units
    return results

class ControlClassInheritError(Exception):

    def __init__(self, message):
        self.message = message
        super().__init__(message)

class NoSystemToSimulateDefined(Exception):

    def __init__(self, message):
        self.message = message
        super().__init__(message)

