
import sys
from typing import Set, Tuple
#sys.path.append('C:/Users/Daniele/Documents/GitLab/fair_sim_release/fair_sim_release')
sys.path.append('/Users/danieleinturri/Documents/Gitlab/fair_sim_release')
import pytest
from src.fmu_export import ParameterImport
from src.fmu_export import ModelModifierFormatError
import os
current_dir = os.path.realpath('..')

@pytest.fixture
def data_import():
    return ParameterImport()
    
def test_datasheet_import(data_import):

    datasheet_dir = current_dir +r'/Gitlab/fair_sim_release/tests/test_data/datasheets'
    datasheets = { 'component1' : 'test_datasheet_1'}                
    data_import.read_datasheet(datasheet_dir, datasheets)
    expected  = {'component1.use_N_in': 'true', 'component1.flowCharacteristic.c': '{-0.31462,0.36629,5.0907}', 'component1.p_a_start': 1}

    assert data_import.parameters == expected 

@pytest.mark.parametrize('input', ['=234', 'redeclare= ', 'redeclare package medium == abc', 'abc'])
def test_model_modifiers_setter_raises_format_exception(data_import, input):
    
    with pytest.raises(ModelModifierFormatError):
        data_import.model_modifiers = [input]


@pytest.mark.parametrize('input', [{'key' :'value'}, 1, 'string', True, (1,2), {1,2,3}])
def test_model_moodifiers_setter_raises_type_exception(data_import, input):

    with pytest.raises(TypeError):
        data_import.model_modifiers = input


def test_model_modifiers_setter(data_import, input = ['  redeclare  package  medium =  medium', '  redeclare package medium = fluid   ']):

    data_import.model_modifiers = input

