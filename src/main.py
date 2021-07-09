# && 

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

"fmus" : [{"model name": "", "directory" : "", "connections" :[{"input name": "", "connect to system": "", "connect to variable": ""},
                                                                         {"input name": "", "connect to system": "", "connect to variable": ""}
                                                                        ]
                    },  
                    {"model name": "", "directory" : "", "connections" :[{"input name": "", "connect to system": "", "connect to variable": ""},
                                                                        {"input name": "", "connect to system": "", "connect to variable": ""}
                                                                        ]
                    }
                    ],    

"controls" :[{"control name": "", "control class" : "", "connections" :[ {"input name": "", "connect to system": "", "connect to variable": ""},
                                                                                    {"input name": "", "connect to system": "", "connect to variable": ""}
                                                                                    ]
                        }                                                                           
                        ],
"simulation stop time" : 10,
"simulation step size" : 1e-4
                    

}




# %%

import fair_simulation as fs
from simulate import Simulation
 
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
    #"asf": "dymola_datasheet_210111_pipe_xxx_staticpipe"
}                                                            
additional_parameters = {                                                       
    'redeclare package Medium': 'Modelica.Media.Water.ConstantPropertyLiquidWater'
}
packages = []



# %%
#fs.fmu_export(create_new_fmu, "dymola",dymola_path, model_name, model_directory,output_directory,
                #datasheet_directory,datasheets, additional_parameters,packages) #TODO clean up -> deleting files (delete simulator.log)


#%%


from simulate import Simulation
import matplotlib.pyplot as plt
from control import Control
from mas import MAS
import numpy as np
 
nummer1_dir = r"C:/Users/Daniele/Desktop/"
nummer2_dir = r"C:/Users/Daniele/Desktop/"

fmus = {"nummer1": {"directory": nummer1_dir, "inputs": [["u_in", "nummer2", "y_out"], ["u_in2", "MAS", "agent1.y_out"]]},
        "nummer2": {"directory": nummer2_dir, "inputs": []}}
#fmus = {"Hochhaus": {"directory": nummer1_dir, "inputs": []}}
#_fmus = {"nummer1": {"directory": nummer1_dir, "inputs": [{"input":"u_in", "output_from_system":"nummer2", "output_name":"y_out"}, ["u_in2", "MAS", "agent1.y_out"]]},
        #"nummer2": {"directory": nummer2_dir, "inputs": []}}
con = Control()
mas = MAS()
controls = {"MAS":{"class": mas, "inputs" : [["agent1.u_in1", "nummer1", "y_out"]]}, 
           "Control": {"class": con, "inputs" : [],  "input_connect_to_output": []}}
time = 5
step_size = 1e-04
record = {"nummer1": ["inductor.i", "inductor.v", "u_in2"], "nummer2":["sine.y"], "MAS": ["one"]}
record = {"nummer1": ["inductor.i", "inductor.v", "u_in2"], "nummer2":["sine.y"]}


sim = Simulation(time, step_size, record, fmu_dict= fmus, controls= controls)
sim.check_control_class()
sim.initialise_fmus()
sim.connect_systems()
sim.create_result_dict()




result, result_dataframe = sim.simulate()
units = sim.create_unit_dic()



 
# %%
from fair import Fair
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
