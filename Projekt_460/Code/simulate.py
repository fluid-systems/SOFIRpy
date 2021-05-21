# %%
from fmpy import read_model_description, extract
from fmpy.fmi2 import FMU2Slave
import numpy as np
import copy



class FMU():

    def __init__(self, model_name, fmu_directory, inputs, outputs):
        self.model_name = model_name
        self.fmu_path = fmu_directory + model_name +".fmu"
        self.model_vars = {}
        self.output_refnums = []
        self.input_refnums = []
        self.inputs = inputs
        self.outputs = outputs
        self.output_values = [0]*len(self.outputs)
       
    def init_fmu(self):

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
        
    def get_refnum(self):

        for out in self.outputs:
            if out in self.model_vars:
                self.output_refnums.append(self.model_vars[out])
            else: 
                print(f"The fmu {self.model_name} doesn't has an output called {out}")

        for inp in self.inputs:
            if inp in self.model_vars:
                self.input_refnums.append(self.model_vars[inp])
            else:
                print(f"The fmu {self.model_name} doesn't has an input called {inp}")

    def get_fmu_output(self):

        for out_num, i in zip(self.output_refnums, range(len(self.output_values))):
            self.output_values[i] = self.fmu.getReal([out_num])[0] 
            
    def _set_fmu_input(self, value, input_name):
        pass

    def _get_fmu_output(self, output_name):
        pass

       
    def set_fmu_input(self, values):
        
        for val, inp_num in zip(values, self.input_refnums): 
            self.fmu.setReal([inp_num], [val])
            
    
    def do_step(self, time, step_size):

        self.fmu.doStep(currentCommunicationPoint=time,communicationStepSize=step_size)

    def conclude_simulation_process(self):

        self.fmu.terminate()
        self.fmu.freeInstance()

    def get_any_value(self, name):
               
        return self.fmu.getReal([self.model_vars[name]])[0]




class Simulation():
    
    def __init__(self, fmu_dic, stop_time, step_size, var_dict, agents):

        self.model_names = list(fmu_dic.keys())
        self.fmu_directorys = [sub["directory"] for sub in list(fmu_dic.values())]
        self.fmu_input_names = [sub["inputs"] for sub in list(fmu_dic.values())]
        self.fmu_output_names = [sub["outputs"] for sub in list(fmu_dic.values())]
        self.fmu_connect_to = [sub["input_connect_to_output"] for sub in list(fmu_dic.values())]
        self.class_fmu = []
        self.time_series = np.arange(0, stop_time + step_size, step_size)
        self.step_size = step_size
        self.stop_time = stop_time
        self.var_dict = var_dict
        self.result_dict = copy.deepcopy(var_dict)
        self.agents = agents
        self.agent_outputs = []*len(agents)
        


    def initialise(self):

        for name, direc, inp, out in zip(self.model_names, self.fmu_directorys, self.fmu_input_names, self.fmu_output_names):
            fmu = FMU(name, direc, inp, out)
            fmu.init_fmu()
            fmu.get_refnum()
            self.class_fmu.append(fmu)      


    def connect_systems(self):
        pass


    def get_fmu_outputs(self):

        for fmu in self.class_fmu:
            fmu.get_fmu_output()
        
    def send_agents_inputs(self):
        pass

    def get_agents_outputs(self):

        for (agent, i) in zip(self.agents, range(len(self.agents))):
            self.agent_ouputs[i] = agent.get_agent_output()
            
    def set_fmu_inputs(self):
    

        for fmu,con in zip(self.class_fmu, self.fmu_connect_to):
            values = [0]*len(con)
            for inp, i in zip(con, range(len(values))):
                fmu_name = inp.split(".")[0]
                output_name = inp.split(".")[1]
                # get corresponding index of model_names list
                index_model_name = self.model_names.index(fmu_name)
                _fmu = self.class_fmu[index_model_name]
                index_output = _fmu.outputs.index(output_name)
                values[i] = _fmu.output_values[index_output]
            fmu.set_fmu_input(values)


    def simulate(self):

        

        for time_step, time in enumerate(self.time_series):
            self.get_fmu_outputs()
            #if self.agents:
                #self.send_agents_inputs()
                #mas.agent_routine()
                #self.get_agents_outputs()
            self.set_fmu_inputs()
            self.record_values(time_step, time)
            for fmu in self.class_fmu:
                fmu.do_step(time, self.step_size)
            
            
        for fmu in self.class_fmu:
            fmu.conclude_simulation_process()

        return  self.result_dict
        
    def create_result_dict(self):
        
        
        for  fmu_names in self.result_dict.keys():
            
            for i in range(len(self.result_dict[fmu_names])):         
                self.result_dict[fmu_names][i] = np.zeros((len(self.time_series), 2))   
                
        
    def record_values(self,time_step, time):
        
        for fmu_name, var_list in zip(list(self.var_dict.keys()), list(self.var_dict.values())):
            
            index_model_name = self.model_names.index(fmu_name)
            fmu = self.class_fmu[index_model_name]
            for var, i in zip(var_list, range(len(var_list))):
                value = fmu.get_any_value(var)
                self.result_dict[fmu_name][i][time_step] = [time, value]
                

        




    



# %%
