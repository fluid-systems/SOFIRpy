
import numpy as np
import copy
import sys
from alive_progress import alive_bar
from numpy.core.records import record


class FMU():

    def __init__(self, model_name, fmu_directory):
        self.model_name = model_name
        self.fmu_path = fmu_directory + model_name +".fmu"
        self.model_vars = {}
        
    
    def init_fmu(self):
        
        from fmpy import read_model_description, extract
        from fmpy.fmi2 import FMU2Slave 

        model_description = read_model_description(self.fmu_path)

        for variable in model_description.modelVariables:
            self.model_vars[variable.name] = variable.valueReference
        
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
    
    def __init__(self, fmu_dic, controls, stop_time, step_size, var_dict):

        self.fmu_model_names = list(fmu_dic.keys())
        self.fmu_directorys = [sub["directory"] for sub in list(fmu_dic.values())]
        self.fmu_connections = [sub["inputs"] for sub in list(fmu_dic.values())]
        self.fmu_dic = copy.deepcopy(fmu_dic)
        self.fmu_classes_dic= copy.deepcopy(fmu_dic)
        for name in self.fmu_classes_dic.keys():
            self.fmu_classes_dic[name] = ""
        for name, con in zip(fmu_dic.keys(), self.fmu_connections):
            self.fmu_dic[name] = con   
        

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
        self.var_dict = var_dict
        self.result_dict = copy.deepcopy(var_dict)

    
    def check_control_class(self):
        
        must_contain_methods = ["set_input", "generate_output", "get_output"]  #TODO if no outputs o inputs in control dict, must_contain_methods can be different
        for _class in self.control_classes: 
            method_missing = [meth for meth in must_contain_methods if not getattr(_class, meth, None)]
            if method_missing:
                s = ""
                for mis in method_missing:
                    s +=  "\n" + mis
                sys.exit(f"The class '{type(_class).__name__}' is missing the following methodes:" + s)     
            else:
                print(f"The class '{type(_class).__name__}' contains all the necessary methods.")        

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
        
        
        for name in self.fmu_dic:
            for connected_system in self.fmu_dic[name]:
                connected_system[1] = self.all_system_classes[connected_system[1]] 
            

        print("All systems connected.")


    def set_control_inputs(self):
        
        for name in self.control_dic:
            for inp in self.control_dic[name]:
                self.control_classes_dic[name].set_input(inp[0],inp[1].get_output(inp[2]))

    
    def generate_control_output(self):
        
        for control in self.control_classes:
            control.generate_output()
    
    def set_fmu_inputs(self):
        
        for name in self.fmu_dic:
            for inp in self.fmu_dic[name]:
                self.fmu_classes_dic[name].set_input(inp[0],inp[1].get_output(inp[2]))

    def simulate(self):

        print("Starting Simulation.")

        with alive_bar(len(self.time_series), bar= 'blocks', spinner='classic') as bar:
            for time_step, time in enumerate(self.time_series):

                self.set_control_inputs()
                self.generate_control_output()
                self.set_fmu_inputs()
                self.record_values(time_step, time)
                for fmu in self.fmu_classes_dic.values():
                    fmu.do_step(time, self.step_size)
                
                bar()

        for fmu in self.fmu_classes_dic.values():
            fmu.conclude_simulation_process()

        print("Simulation completed.")

        return  self.result_dict
        
    
    def create_result_dict(self):
        
        for system in self.var_dict:
            zero_list = [np.zeros((len(self.time_series), 2)) for i in range(len(self.result_dict[system]))]
            self.result_dict[system] = {variable_name:zero_array for (variable_name, zero_array) in zip(self.var_dict[system], zero_list)}
            
                
        
    def record_values(self,time_step, time):
        
        for system_name in self.result_dict:
            for var in self.result_dict[system_name]:
                value = self.all_system_classes[system_name].get_output(var) 
                self.result_dict[system_name][var][time_step] = [time, value]
            
