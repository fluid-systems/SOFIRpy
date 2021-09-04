from typing import Type
import numpy as np
import pandas as pd
import copy
import os
from pandas.core.frame import DataFrame
from fmpy import read_model_description, extract
from fmpy.fmi2 import FMU2Slave 
from alive_progress import alive_bar


class Fmu:

    def __init__(self, model_path) -> None:
        self.fmu_path = model_path

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
        print(f'FMU {os.path.basename(self.fmu_path)} initialized.')
    
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

def connections_checker(connection):

    for con in connection:
        connections_keys = ["input name", "connect to system", "connect to variable"]
        valid, mes = key_checker(connections_keys, list(con.keys()), "connections")
        if not valid:
            raise ConnectionFormatError(mes)
        for name in list(con.values()):
            if type(name) != str:
                raise TypeError(f"{name} should be a string.")

def key_checker(must_keys: list, given_keys: list, info):
    if not all(key in given_keys for key in must_keys):
        invalid_name = [name for name in given_keys if name not in must_keys]
        mes = f"The dictionaries in the list, where the {info} information's are stored, should have the following keys: {must_keys}"
        if invalid_name:
            mes+= "\n Invalid: " + ", ".join(invalid_name)
        return False, mes
    return True, None

class ConnectSystem:

    def __init__(self, fmus_info: list = None, controls_info: list = None):
        
        if not fmus_info:
            self.fmus_info = []
        self.fmus_info = fmus_info
        if not controls_info:
            self.controls_info = []
        self.controls_info = controls_info

    @property
    def fmus_info(self) -> list:
        return self._fmus_info

    @fmus_info.setter
    def fmus_info(self, fmus_info: list) -> None:
        
        if type(fmus_info) != list:
            raise TypeError("The fmu information needs to be list.")
        fmu_info_keys = ["model name", "path", "connections"]
        for fmu in fmus_info:
            valid, mes = key_checker(fmu_info_keys, list(fmu.keys()), "fmus")
            if not valid:
                raise FmuInfoFormatError(mes)
            if type(fmu["connections"]) != list:
                raise TypeError("The values of the key 'connections' should be a list.")
            connections_checker(fmu["connections"])

        self._fmus_info = fmus_info

    @property
    def controls_info(self) -> list:
        return self._controls_info

    @controls_info.setter
    def controls_info(self, controls_info: list) -> None:

        if type(controls_info) != list:
            raise TypeError("The control information needs to be list.")
        control_info_keys = ["control name", "control class", "connections"]
        for control in controls_info:
            valid, mes = key_checker(control_info_keys, list(control.keys()), "controls")
            if not valid:
                raise ControlInfoFormatError(mes)
            connections_checker(control["connections"])

            if not hasattr(control["control class"], "__dict__"):
                raise TypeError("The key 'control class' needs to have an instance of a class as value.")

        self._controls_info = controls_info

    def create_all_system_classes_dict(self) -> None:

        self.all_system_classes = {**self.fmu_classes, **self.control_classes}

    def create_control_classes_dict(self) -> None:

        self.control_classes = {control["control name"]: control["control class"] for control in self.controls_info}

    def check_control_classes(self) -> None:

        must_contain_methods = ["set_input", "generate_output", "get_output"]
        for _class in self.control_classes.values():
            method_missing = [meth for meth in must_contain_methods if not getattr(_class, meth, None)]
            if method_missing:
                s = ""
                for mis in method_missing:
                    s +=  "\n" + mis
                raise AttributeError(f"The class '{type(_class).__name__}' is missing the following methodes:" + s)     
            else:
                print(f"The class '{type(_class).__name__}' contains all the necessary methods.")




    def initialise_fmus(self, start_time: float) -> None:

        self.fmu_classes = {}
        for fmu in self.fmus_info:
            model_path = fmu["path"]
            fmu_class = Fmu(model_path)
            fmu_class.initialize_fmu(start_time)
            model_name = fmu["model name"]
            self.fmu_classes[model_name] = fmu_class

    def initialize_systems(self, start_time: float) -> None:

        self.initialise_fmus(start_time)
        self.create_control_classes_dict()
        self.check_control_classes()
        self.create_all_system_classes_dict()
   
        for fmu in self.fmus_info:
            for connection in fmu["connections"]:
                system_name = connection["connect to system"]
                connection["connect to system"] = self.all_system_classes[system_name]
        
        for control in self.controls_info:
            for connection in control["connections"]:
                system_name = connection["connect to system"]
                connection["connect to system"] = self.all_system_classes[system_name]

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
        
        for control in self.systems.controls_info:
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
        
        for fmu in self.systems.fmus_info:
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
            
    def convert_results_to_pandas(self) -> DataFrame:

        result_dataframe = pd.DataFrame(self.time_series, columns = ["time"])

        for system_name in self.result_dict:
            for var in self.result_dict[system_name]:
                result_dataframe[system_name +"." + var] = self.result_dict[system_name][var][:,1] 

        return result_dataframe

    def get_units(self) -> dict:

        units = {}
        for system_name in self.result_dict:
            for var in self.result_dict[system_name]:
                if self.systems.fmu_classes.get(system_name):
                    unit = self.systems.fmu_classes[system_name].get_unit(var)
                    units[system_name + "." + var] = unit

        return units

def simulate(stop_time, step_size, fmus_info: list = [], controls_info: list = [], result_var: dict = {}, start_time = 0, get_units = False):

    if not fmus_info and not controls_info:
        raise NoSystemToSimulateDefined("No System to simulate given as argument.")
    systems = ConnectSystem(fmus_info, controls_info)
    sim = Simulation(systems, result_var)
    results = sim.simulate(stop_time, step_size, start_time)
    if get_units:
        units = sim.get_units()
        return results, units
    return results

class NoSystemToSimulateDefined(Exception):

    def __init__(self, message):
        self.message = message
        super().__init__(message)


        
class FmuInfoFormatError(Exception):

    def __init__(self, message):
        self.message = message
        super().__init__(message)

class ConnectionFormatError(Exception):

    def __init__(self, message):
        self.message = message
        super().__init__(message)

class ControlInfoFormatError(Exception):

    def __init__(self, message):
        self.message = message
        super().__init__(message)
