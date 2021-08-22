from typing import Optional
from fmu_export import export_fmu
from simulate import simulate
from analyze import plot_results
from store_data import store_date
import os
import json

def workflow(setup_file_path: str, stop_time: float, step_size: float, get_units, use_existing_fmus: Optional[dict[str, str]], plotting_func = None):

    with open(setup_file_path) as file:
            setup = json.load(file)    
    
    for fmu in setup.get("fmus"):
        if fmu["model name"] not in list(use_existing_fmus.keys()): #TODO wo eingeben wo welche fmus liegt
            fmu = export_fmu()
            fmu_path = os.path.join(fmu.output_directory, fmu.modeling_env.model_name + ".fmu")
            fmu["directory"] = fmu_path
        else:  
            fmu["directoy"] = use_existing_fmus[fmu["model name"]]
            
    
    results = simulate(stop_time, step_size, fmus_info = setup.get("fmus"), controls_info = setup.get("controls"), result_var= setup.get("record"))

    if not plotting_func:
        plotting_func = plot_results
    for plot in setup.get("to plot"): # "to plot" : [{"y": var names as list, "x" : optional, "x_label": "", "y_label": "", "title" : ""}, ...]
        plotting_func(setup.get("style sheet"), results, y = plot.get("y"), x = plot.get("x"), x_label= plot.get("x_label"), 
                    y_label= plot.get("y_label"), titel = plot.get("title"))

        # save results
        # store name of plots in data dict
    
    # store all data
    store_date()
    
        

    


