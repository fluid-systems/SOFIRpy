# %%


from simulate import Simulation, ConnectSystem, simulate
import matplotlib.pyplot as plt
from control import _Control
from mas import MAS
import numpy as np

nummer1_dir = r"C:/Users/Daniele/Desktop/"
nummer2_dir = r"C:/Users/Daniele/Desktop/"


#con = _Control()
mas = MAS()
controls = {"MAS":{"class": mas, "inputs" : [["agent1.u_in1", "nummer1", "y_out"]]}, 
           "Control": {"class": "", "inputs" : [],  "input_connect_to_output": []}}
time = 5
step_size = 1e-04
#record = {"nummer1": ["inductor.i", "inductor.v", "u_in2"], "nummer2":["sine.y"], "MAS": ["one"]}
record = {"nummer1": ["inductor.i", "inductor.v", "u_in2"], "nummer2":["sine.y"]}

setup = {
"project directory" : "",

"dymola path" : "",

"fmu export" :  [{"model name" : "", 
                "model directory": "", 
                "packages" : [],
                "datasheet_directory" : "", 
                "datasheets" : {}, 
                "additional_parameters" : {}}
                ],

"fmus" : [{"model name": "nummer1", "directory" : r"C:/Users/Daniele/Desktop/", "connections" :[{"input name": "u_in", "connect to system": "nummer2", "connect to variable": "y_out"}
                                                                         #,{"input name": "u_in2", "connect to system": "MAS", "connect to variable": "agent"}
                                                                        ]
                    },  
                    {"model name": "nummer2", "directory" : r"C:/Users/Daniele/Desktop/", "connections" :[]
                    }
                    ],    

"controls" :[{"control name": "MAS", "control class" : mas, "connections" :[ {"input name": "agent_u_in", "connect to system": "nummer1", "connect to variable": "y_out"}]
                        }                                                                           
                        ],
"simulation stop time" : 10,
"simulation step size" : 1e-4
                    

}

# %%

results = simulate(10, 0.0001, fmus_info  = setup["fmus"], result_var= record)

# %%

import fair_simulation as fs
from simulate import Simulation
 
create_new_fmu = True       
dymola_path = r"C:/Program Files/Dymola 2018 FD01/bin64"                        
datasheet_directory = r'C:/Users/Daniele/Documents/GitLab/ADP_FAIR_Sim/Datasheets'
model_directory = r"C:/Users/Daniele/Documents/GitLab/ADP_FAIR_Sim/Projekt_460/Fluid_model/" #TODO find out why / is needed
output_directory = r"C:/Users/Daniele/Desktop/test"
model_name = "Hochhaus"
datasheets = {
    #'YONOS': 'datasheet_20210105_pump_manufacturer_productname',
    'YONOS': 'dymola_datasheet_210111_pump_wilo_Yonos-ECO-25-1-5-BMS',
    #'Valve_floor1': 'dymola_datasheet_210111_valve_xxx_somevalve',
    #'R9': 'dymola_datasheet_210111_pipe_xxx_staticpipe',
    #"asf": "dymola_datasheet_210111_pipe_xxx_staticpipe"
}                                                            
model_modifiers = ['redeclare package Medium = Modelica.Media.Water.ConstantPropertyLiquidWater']
parameters = {"bla.a": 2}
packages = []



# %%
from fmu_export import export_fmu

fmu = export_fmu('d', model_name, model_directory, dymola_path, output_directory, model_modifiers= model_modifiers, additional_parameters=parameters)


# %%


c = ConnectSystem(setup["fmus"], setup["controls"])
 
# %%
from store_data import Fair
fair = Fair(r"C:/Users/Daniele/Desktop/", sub_project_folder= "FluidSystem1")
# %%
fair.create_project_folder()
fair.create_HDF5_file()


# %%
fair.create_run_name()
fair.create_new_run_folder()
fair.create_new_group_hdf5()

# %%
fair.save_results_in_hdf5(result_dataframe, units = units) 
# %%
#fair.save_datasheets_name_in_hdf5()
fair.copy_models(r"C:/Users/Daniele/Desktop/", ["nummer1"])

# %%
from analyze import Analyze

style_sheet_path = "./FST.mplstyle"
ax = Analyze.plot_results(style_sheet_path,result_dataframe ,["nummer1.inductor.v", "nummer1.inductor.i"] ,y_label= "bla" ,x_label=r'TIME in $s$' , title = "Test")

#ax.set_yticks()
#ax.set_xticks([0,2.5, 5])
plt.legend( ["v", "i"], title = "Legend Titel", loc = "lower right")

#plt.savefig(r"C:/Users/Daniele/Desktop/test1.png")
#plt.ylim([-0.1,0.15])
plt.show()


# %%
df = fair.get_data("Run_1", "nummer1.inductor.v")

# %%

# %%
fair.set_hdf5_file_name(hdf5_file_name="hdf5_210618_17051")
# %%
# %% 
c = ConnectSystem(setup["fmus"], setup["controls"])
c.initialize_systems()

# %%

# %%
from analyze import Analyze

style_sheet_path = "./FST.mplstyle"
plots = []
ax = Analyze.plot_results(style_sheet_path,result_dataframe ,["nummer1.inductor.v", "nummer1.inductor.i"] ,y_label= "bla" ,x_label=r'TIME in $s$' , title = "Test")

#ax.set_yticks()
#ax.set_xticks([0,2.5, 5])
plt.legend( ["v", "i"], title = "Legend Titel", loc = "lower right")

#plt.savefig(r"C:/Users/Daniele/Desktop/test1.png")
#plt.ylim([-0.1,0.15])
#plt.show()
plots.append(ax)

fair.save_plots(plots)
# %%
import OMPython as om

nummer1_dir = r"C:/Users/Daniele/Desktop/"
mo = om.ModelicaSystem(nummer1_dir + "nummer1.mo", "nummer1")


# %%

# %%
from fmu_export import ParameterImport

# %%
from simple_pid import PID
from abstract_control import Control

class PID(Control):

    def __init__(self):
        self.pid = PID(1, 0.1, 0.05)
        self.pid.set_point = 100
        self.pid.sample_time = 0.01
        self.inputs = {"speed" : 0}
        self.outputs = {"u"}

    def set_input(self, input_name, input_value):
        self.inputs[input_name] = input_value 

    def generate_output(self):
        self.outputs["u"] = self.pid(self.inputs["speed"])

    def get_output(self, output_name):
        return self.outputs[output_name]

    def get_unit(self, variable_name):...

pid = PID()

# %%
from fmu_export import export_fmu
model_directory = "C:/Users/Daniele/Desktop/"
model_name = "DC_Motor"
modeling_environment = "d"
datasheet_directory = "C:/Users/Daniele/Documents/GitLab/fair_sim_release/fair_sim_release/examples"
datasheets = {"damper" : "damper_datasheet"} #{component name : datasheet name}
parameters = {"inertia.J" : 0.5}
dymola_path = "C:/Program Files/Dymola 2018 FD01/bin64"       
output_directory = "C:/Users/Daniele/Desktop/test"
fmu = export_fmu(modeling_environment, model_name, model_directory,dymola_path, output_directory, datasheet_directory= datasheet_directory, datasheets= datasheets, additional_parameters= parameters)   
# %%
def name_generator(run_name, num):
    return "Run_9"

# %%
from store_data import InitiateProject, RunCreation, ReadWriteHDF5Data
v
s = InitiateProject(dir, sub_project_folder= sub)
h = RunCreation(s)
path = h.name_data.hdf5_path


# %%
import numpy as np
d = ReadWriteHDF5Data()
data = np.random.random_sample((3,3))
run_name = "Run_1"
sub_group = "code"
attr = {"created on": "12.12.12", "son": 1}
data_name = "test6"
d.save_data(data, data_name, run_name, "plots", attr)
# %%

x = d.get_data("Run_1")

# %%
from store_data import store_date, read_data
dir = "C:\\Users\\Daniele\\Desktop"
sub = "FluidSystem1"
data = [{"data": 2, "data name": "ein test", "hdf5_folder_name": "plots", "attr": {"created on": "20.08.21"}}, 
        {"data": 2, "data name": "ein test", "hdf5_folder_name": "simulation_data", "attr": {"created on": "20.08.21"}}]
# %%        
store_date(dir, data, sub_project_folder= sub)
# %%
data, attr = read_data(dir,"Run_1/simulation_data/nummer1.inductor.i" , sub_project_folder= sub, get_attribute= True)
# %%
