#%%
import sys
sys.path.append('C:/Users/Daniele/Documents/GitLab/fair_sim_release/fair_sim_release')
from src.abstract_control import Control
import math

class ControlTest(Control):
    def __init__(self):
        self.conections = {'sininput' : 'sinoutput'}
        self.inputs = {'sininput': 0}
        self.outputs = {'sinoutput': 0}

    def set_input(self, input_name, input_value):
        self.inputs[input_name] = input_value
        
    def generate_output(self):
        for inp in self.conections:
            self.outputs[self.conections[inp]] = math.sin(self.inputs[inp])
 
    def get_output(self, output_name):
        return self.outputs[output_name]

    def get_unit(self, variable_name):
        pass

    

# %%
