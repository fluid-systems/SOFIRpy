# %%
from fair_sim.workflow import delete_data_in_run
from workflow import delete_run

path = r"C:\Users\Daniele\Desktop\Motor_Control1"

name = "Run_8/simulation_results/pid.u"

delete_run(path, name)
# %%
from read_hdf5_data import read_data
path = r"C:\Users\Daniele\Desktop\Motor_Control1\hdf5_210913_212013.hdf5"
name = "Run_24/datasheets/k_p_datasheet"
data = read_data(path,name)

# %%
from workflow import delete_data_in_run
path = r"C:\Users\Daniele\Desktop\Motor_Control1"
run_name = "Run_30/"
data_name = "code/simulation_results"
data  =delete_data_in_run(path, run_name, data_name)
# %%
from workflow import get_hdf5_project
pr = get_hdf5_project(r"C:\Users\Daniele\Desktop\Motor_Control1")
pr.delete_data_in_run("Run_34", "plots/Speed, Voltage over time")
# %%
    
# %%
