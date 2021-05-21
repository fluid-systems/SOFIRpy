# %%

import fair_simulation as fs
from simulate import Simulation

# %%   
create_new_fmu = True       
dymola_path = r"C:/Program Files/Dymola 2018 FD01/bin64"                        
datasheet_directory = r'C:/Users/Daniele/Documents/GitLab/fair_sim_release/fair_sim_release/Datasheets'
model_directory = r"C:/Users/Daniele/Documents/GitLab/fair_sim_release/fair_sim_release/Projekt_460/Fluid_model/"
output_directory = r"C:/Users/Daniele/Desktop/"
model_name = "Hochhaus"
datasheets = {
    #'YONOS': 'datasheet_20210105_pump_manufacturer_productname',
    'YONOS': 'dymola_datasheet_210111_pump_wilo_Yonos-ECO-25-1-5-BMS',
    'Valve_floor1': 'dymola_datasheet_210111_valve_xxx_somevalve',
    'R9': 'dymola_datasheet_210111_pipe_xxx_staticpipe',
    "asf": "dymola_datasheet_210111_pipe_xxx_staticpipe"
}                                                            
additional_parameters = {                                                       
    'redeclare package Medium': 'Modelica.Media.Water.ConstantPropertyLiquidWater'
}
packages = []

# %%
fs.fmu_export(create_new_fmu, "dymola", model_name, model_directory, datasheet_directory, datasheets, 
                additional_parameters, output_directory, dymola_path, packages)




# %%
fmus = {"nummer1": {"directory": "asfafa", "inputs": ["sdf", "asdfsd", "ikhv"],"input_connect_to_output": ["tiefhaus.klo", "tiefhaus.223", "mittelhaus.aöööö"] , "outputs": ["bla"]},
        "nummer2": {"directory": "kkkkk", "inputs": ["kla"],"input_connect_to_output": ["Hochhaus.bla"] , "outputs": ["klo", "223", "fff"]},
        "mittelhaus": {"directory": "asd", "inputs": ["ggh"],"input_connect_to_output": ["Hochhaus.fff"] , "outputs": ["aöööö"]}}

#%%
import numpy as np
from simulate import Simulation
from Agent import Agent
import matplotlib.pyplot as plt

nummer1_dir = r"C:/Users/Daniele/Desktop/"
nummer2_dir = r"C:/Users/Daniele/Desktop/"
fmus = {"nummer1": {"directory": nummer1_dir, "inputs": ["u_in"],"input_connect_to_output": ["nummer2.y_out"] , "outputs": []},
        "nummer2": {"directory": nummer2_dir, "inputs": [],"input_connect_to_output": [] , "outputs": ["y_out"]}}

#fmus = {"fmutest": {"directory": nummer1_dir, "inputs": [],"input_connect_to_output": [] , "outputs": []}}
time = 5
step_size = 1e-04
ag = Agent("lw", ["nummer1.u_in2"], ["nummer1.y_out"])
agents = [ag]
record = {"nummer1": ["inductor.i", "inductor.v"], "nummer2":["sine.y"]}

sim = Simulation(fmus, time, step_size, record, agents)
sim.initialise()
sim.create_result_dict()


#%%

result = sim.simulate()

# %%

connect = {"nummer1": {"directory": nummer1_dir, "inputs": ["u_in"],"input_connect_to_output": ["nummer2.y_out"] , "outputs": []},
        "nummer2": {"directory": nummer2_dir, "inputs": [],"input_connect_to_output": [] , "outputs": ["y_out"]}}

# %%

x = result["nummer1"][1][:,0]
y = result["nummer1"][1][:,1]
plt.plot(x,y)
plt.show()
# %%

# %%
