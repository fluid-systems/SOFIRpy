
import sys
sys.path.append('C:/Users/Daniele/Documents/GitLab/fair_sim_release/fair_sim_release')
import pytest
from src.fmu_export import ParameterImport
import os
current_dir = os.path.realpath('..')

@pytest.fixture
def data_import():
    return ParameterImport()
    
def test_datasheet_import(data_import):

    datasheet_dir = current_dir +r'\fair_sim_release\tests\test_data\datasheets'
    print(datasheet_dir)
    datasheets = { 'component1' : 'test_datasheet_1'}                
    data_import.read_datasheet(datasheet_dir, datasheets)
    expected  = {'component1.use_N_in': 'true', 'component1.flowCharacteristic.c': '{-0.31462,0.36629,5.0907}', 'component1.p_a_start': 1}

    assert data_import.parameters == expected 

