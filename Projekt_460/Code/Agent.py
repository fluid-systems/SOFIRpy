import numpy as np

class Agent():

    def __init__(self, name, output_connect_to, input_connect_to):
        
        self.name = name
        self.output_connect_to = output_connect_to
        self.input_connect_to = input_connect_to

    def set_agent_input(self, value):

        self.input = value

    def get_agent_output(self):    
           
        return self.output



