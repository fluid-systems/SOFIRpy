print(r'////////// Starting Program \\\\\\\\\\')
# %% Imports
from pathlib import Path
import matplotlib.pyplot as plt
from alive_progress import alive_bar
import utils_Data as Data
from utils_fluidsystem import create_fmu
import utils_FMU as FMU
import utils_MAS as MAS
import utils_Agent_classes as New_Agent
import utils_analyze as analyze
from FST_colors import set_FST_template

# %% --------------------------- S E T U P ------------------------------------##
# General                                                                       #
create_new_fmu = True                                                          
use_run = 'Run_1'                                                               # Run to use if no new fmu should be created
dymola_path = r"C:/Program Files/Dymola 2018 FD01/bin64"                        
#datasheet_directory = r'C:/Users/Daniele/Documents/GitLab/ADP_FAIR_Sim/Datasheets'
datasheet_directory = r'C:/Users/Tim/Documents/MasterStudium/WiSe20_21/ADP/Gitlab_Ordner/ADP_FAIR_Sim/Datasheets'
project_directory = str(Path(__file__).resolve().parents[1]).replace("\\","/")  #
project_number = 460                                                            
project_owner = 'A'                                                             
# Fluid model                                                                   
datasheets = {
    #'YONOS': 'datasheet_20210105_pump_manufacturer_productname',
    'YONOS': 'dymola_datasheet_210111_pump_wilo_Yonos-ECO-25-1-5-BMS',
    'Valve_floor1': 'dymola_datasheet_210111_valve_xxx_somevalve',
    'R9': 'dymola_datasheet_210111_pipe_xxx_staticpipe'
}                                                                               
model_name = 'Hochhaus' 
packages = [] # Path to package
name_of_packages = {'Modelica Standard Library' : '3.2.2'}                                                        
additional_parameters = {                                                       
    'redeclare package Medium': 'Modelica.Media.Water.ConstantPropertyLiquidWater'
}
# Simulation / MAS                                                              
stop_time = 20                                                                   
step_size = 1e-1                                                                # Intervall for communication with fmu
agent_step_size = 1                                                             # Intervall for activity of agents
memory_time = 0.1                                                               # Agents remember their proplems for this amount of time
k_p = 0.0025                                                                    # proportional gain of local controllers
k_i = 0.6                                                                       # integral gain of local controllers
valve_1 = New_Agent.Valve_Agent(name= 'valve_1',                                
                    u_name= 'u_v_1', y_name= 'y_v_1', memory_time= memory_time,
                    agent_step_size= agent_step_size, u_bounds = [0, 1],
                    step_size= step_size, k_p= k_p, k_i= k_i, threshold= 0.1,
                    w_user= 2, w_bounds= [1.5,3])
valve_3 = New_Agent.Valve_Agent(name = 'valve_3', 
                    u_name= 'u_v_3', y_name= 'y_v_3', memory_time= memory_time,
                    agent_step_size= agent_step_size, u_bounds = [0, 1],
                    step_size= step_size, k_p= k_p, k_i= k_i, threshold= 0.1,
                    w_user= 2, w_bounds= [1.5,3])
valve_5 = New_Agent.Valve_Agent(name = 'valve_5', 
                    u_name= 'u_v_5', y_name= 'y_v_5', memory_time= memory_time,
                    agent_step_size= agent_step_size, u_bounds = [0, 1],
                    step_size= step_size, k_p= k_p, k_i= k_i, threshold= 0.1,
                    w_user= 2, w_bounds= [1,3])
# Pump Agents
pump_1 = New_Agent.Pump_Agent(name = 'pump_1', 
                    u_name= 'u_p_1', y_name='y_p_1', memory_time= memory_time,
                    agent_step_size= agent_step_size, u_bounds= [0.35,1],
                    u_init = 1)
pump_2 = New_Agent.Pump_Agent(name = 'pump_2', 
                    u_name= 'u_p_2', y_name= 'y_p_2', memory_time= memory_time,
                    agent_step_size= agent_step_size, u_bounds= [0.38,1],
                    u_init = 0.5)
valve_agents = [valve_1, valve_3, valve_5]
pump_agents = [pump_1, pump_2]
agents = valve_agents + pump_agents                                             
print('----- Setup done -----')                                                 #
#################################################################################

# %% --------------- P R E P A R E  S I M U L A T I O N -----------------------##
print('----- Preparing simulation ----- ')                                      #
HDF5_file_name = Data.create_HDF5(project_number, project_owner,                #
                                                            project_directory)  # (1a) # 1_digital_datasheet, 2_model_data_fluid_system (fmu + metadata), 3_simulation_data (raw data + metadata), 4_results, 5_code
run_name = Data.create_new_run(project_directory, HDF5_file_name)               # (1b)                                   
if create_new_fmu:                                                              #
    Data.save_datasheets(datasheets, datasheet_directory, project_directory,    #
                                                    HDF5_file_name, run_name)   # (1c)
    PIDs, simulator_log, custom_settings = create_fmu(model_name,               #  
                            project_directory, datasheet_directory, datasheets, #
                            additional_parameters, project_owner,               #
                            project_number, run_name, dymola_path,              #
                            HDF5_file_name, packages)                           # (2a, 2b, 2c)
    Data.save_fmu_data(PIDs, simulator_log, custom_settings, project_directory, #
                                  HDF5_file_name, run_name, name_of_packages)   # (2d)
else:                                                                           #
    PIDs = Data.copy_run(project_directory, use_run, run_name, HDF5_file_name)  #
fmu, model_vars = FMU.init_fmu(project_directory, run_name, PIDs)               # (3a)
MAS.connect_MAS_to_FMU(agents, model_vars)                                      #
record = MAS.Recorder(valve_agents, pump_agents, stop_time, step_size)          #
print('----- Preparation completed -----')                                      #
#################################################################################

# %% ------------------------- S I M U L A T I O N ----------------------------##
print('----- Starting simulation -----')                                        #
with alive_bar(len(record.time_series), bar= 'classic', spinner='classic') as bar:
    for time_step, time in enumerate(record.time_series):                       # (3c)
        # MAS: Send new fluid-system input to the FMU                           #
        MAS.agent_routine(agents, fmu, time_step, agent_step_size, step_size)   #
        # Save the important values                                             #
        record.record_agents(time_step)                                         #
        # perform one step                                                      #
        fmu.doStep(currentCommunicationPoint=time,                              #
                                                communicationStepSize=step_size)#
        bar()                                                                   #
# Conclude simulation process                                                   #
fmu.terminate()                                                                 #
fmu.freeInstance()                                                              #
recorded_values = record.return_record()                                        #
print('----- Simulation completed -----')                                       #
# Save data and metadata                                                        #
Data.save_MAS_metadata(agents, project_directory, HDF5_file_name, run_name)     # (3d)
Data.save_MAS_data(recorded_values, project_directory, HDF5_file_name, run_name)#
#################################################################################

# %% --------------------------- A N A L Y S I S ------------------------------##
rmse = analyze.RMSE(recorded_values)                                            # (4)
Data.save_rmse(rmse, project_directory, HDF5_file_name, run_name)               #   
set_FST_template(project_directory)                                             #          
PID_plot_w_y = analyze.plot_w_y_valves(recorded_values, project_owner,          #
                                     project_number,run_name, project_directory)#
PID_plot_u=analyze.plot_u(recorded_values, project_owner, project_number,       #
                                                run_name, project_directory)    #
PID_plot_y_pumps=analyze.plot_y_pumps(recorded_values, project_owner,           #
                                project_number, run_name, project_directory)    #
Data.save_PIDs_plots(PID_plot_w_y, project_directory, HDF5_file_name, run_name) #
Data.save_PIDs_plots(PID_plot_u, project_directory, HDF5_file_name, run_name)   #
Data.save_PIDs_plots(PID_plot_y_pumps, project_directory,                       #
                                            HDF5_file_name, run_name)           #
PID_code = Data.copy_code(project_directory, run_name,                          # (5)
                                    project_owner, project_number)              #
Data.save_PID_code(PID_code, project_directory, HDF5_file_name, run_name)       #
#################################################################################

# %% Delete runs
# runs = [2,3,4,5]
# for run in runs:
#     Data.delete_run(project_directory, HDF5_file_name, f'Run_{run}')
# %%
