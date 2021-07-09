
import sys
sys.path.append('C:/Users/Daniele/Documents/GitLab/fair_sim_release/fair_sim_release')
import pytest
from src.simulate import Simulation
import os
current_dir = os.getcwd()



@pytest.fixture
def simulation_fmus():

    fmu_dir = os.path.join(current_dir, 'tests/models')
    

    fmu_dict = {"nummer1": {"directory": fmu_dir, "inputs": [["u_in", "nummer2", "y_out"]]},
                "nummer2": {"directory": fmu_dir, "inputs": []}}
    var_dict = {"nummer1": ["inductor.i", "inductor.v", "u_in2"], "nummer2":["sine.y"]}

    stop_time = 10
    step_size = 1e-4
    
    return Simulation(stop_time, step_size, fmu_dict= fmu_dict, result_var_dict= var_dict)

@pytest.fixture
def simulation_fmu_control():
    pass    

def test_fmu_simulation_result(simulation_fmus):

    import pandas as pd

    expected_results = pd.read_excel(os.path.join(current_dir, 'tests/test_data', 'fmu_simulation_results.xlsx'))

    
    simulation_fmus.initialise_fmus()
    simulation_fmus.connect_systems()
    simulation_fmus.create_result_dict()
    result, result_dataframe = simulation_fmus.simulate()

    assert round(result_dataframe['time'][50], 7) == round(expected_results['time'][50], 7)
    assert round(result_dataframe['nummer1.inductor.i'][98], 7) == round(expected_results['nummer1.inductor.i'][98], 7)
    

def test_fmu_control_simulation(simulation_fmu_control):
    pass
    



