from fmu_export import export_fmu
from simulate import simulate
from analyze import plot_results

def workflow(json_file, new_fmu = True):

    if new_fmu:
        export_fmu()

    


