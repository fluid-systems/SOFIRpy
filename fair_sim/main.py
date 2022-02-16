# # # %%
# # from fair_sim.workflow import delete_data_in_run
# # from workflow import delete_run

# # path = r"C:\Users\Daniele\Desktop\Motor_Control1"

# # name = "Run_8/simulation_results/pid.u"

# # delete_run(path, name)
# # # %%
# # from read_hdf5_data import read_data
# # path = r"C:\Users\Daniele\Desktop\Motor_Control1\hdf5_210913_212013.hdf5"
# # name = "Run_24/datasheets/k_p_datasheet"
# # data = read_data(path,name)

# # # %%
# # from workflow import delete_data_in_run
# # path = r"C:\Users\Daniele\Desktop\Motor_Control1"
# # run_name = "Run_30/"
# # data_name = "code/simulation_results"
# # data  =delete_data_in_run(path, run_name, data_name)
# # # %%
# # from workflow import get_hdf5_project
# # pr = get_hdf5_project(r"C:\Users\Daniele\Desktop\Motor_Control1")
# # pr.delete_data_in_run("Run_34", "plots/Speed, Voltage over time")
# # # %%
# # from workflow import workflow
# # path = r"C:\Users\Daniele\Desktop\Fluidsystem1\test.json"
# # workflow(path, 10, 0.01)
# # # %%
# # from workflow import workflow
# # from discrete_pid import PID
# # pid = PID(0.001, 3, 20, 0.1, 100, 100, 0)
# # c = {"pid": pid}
# # path = r"C:\Users\Daniele\Documents\GitLab\fair_sim_release\fair_sim_release\examples\motor_control\workflow.json"
# # workflow(path, 10, .001,c, store_fmu_copy= False)
# # %%
# from simulation import simulate
# from discrete_pid import PID
# from plot import plot_results

# fmu_infos =  [
#         {
#             "name": "DC_Motor",
#             "path": "C:\\Users\\Daniele\\Documents\\GitLab\\fair_sim_release\\fair_sim_release\\examples\\motor_control\\DC_0Motor.fmu",
#             "connections": [
#                 {
#                     "parameter name": "u",
#                     "connect to system": "pid",
#                     "connect to external parameter": "u"
#                 }
#             ]
#         }
#     ]

# control_infos =  [
#         {
#             "name": "pid",
#             "connections": [
#                 {
#                     "parameter name": "speed",
#                     "connect to system": "DC_Motor",
#                     "connect to external parameter": "y"
#                 }
#             ]
#         }
#     ]

# pid = PID(0.001, 3, 20, 0.1, 100, 100, 0)

# control_classes = {"pid": pid}
# log = {
#         "DC_Motor": [
#             "y",
#             "MotorTorque.tau"
#         ],
#         "pid": [
#             "u"
#         ]
#     }
# results, units = simulate(10, 0.001, fmu_infos, control_infos, control_classes, log, get_units=True)

# print(results)
# print(units)
# plot_results([results["pid.u"], results["DC_Motor.y"]], results["time"])
# import matplotlib
# matplotlib.pyplot.show()
# %%
from fair_sim.fmu_export.dymola_export import export_dymola_fmu
# %%

# %%
