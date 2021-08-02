
import sys
from typing import Set, Tuple
sys.path.append('C:/Users/Daniele/Documents/GitLab/fair_sim_release/fair_sim_release')
#sys.path.append('/Users/danieleinturri/Documents/Gitlab/fair_sim_release')
import pytest
from src.fmu_export import ParameterImport
from src.fmu_export import ModelModifierFormatError
import os
current_dir = os.path.realpath('..')

@pytest.fixture
def data_import():
    return ParameterImport()

@pytest.fixture
def data_import_datasheet():
    datasheet_dir = current_dir +r'/fair_sim_release/tests/test_data/datasheets'
    datasheets = { 'component1' : 'test_datasheet_1'} 
    return ParameterImport(datasheets= datasheets, datasheet_directory= datasheet_dir)

@pytest.fixture
def data_import_parameters():
    paramaters = {'component1.use_N_in': 'true', 'component1.flowCharacteristic.c': '{-0.31462,0.36629,5.0907}', 'component1.p_a_start': 1}
    return ParameterImport(parameters_dict= paramaters)
    
@pytest.fixture
def data_import_model_modifiers():
    model_modifiers = [ "   redeclare    package    medium   =     Modelica.Media.Water.ConstantPropertyLiquidWater    ", 
                        "   redeclare function    flowCharacteristic =   Custom_Pump_V2.BaseClasses_Custom.PumpCharacteristics.quadraticFlow  ",  
                        "redeclare model HeatTransfer = Modelica.Fluid.Vessels.BaseClasses.HeatTransfer.IdealHeatTransfer"]
    return ParameterImport(model_modifier_list= model_modifiers)

def test_datasheet_import(data_import_datasheet):

    data_import_datasheet.read_datasheet()
    expected  = {'component1.use_N_in': 'true', 'component1.flowCharacteristic.c': '{-0.31462,0.36629,5.0907}', 'component1.p_a_start': 1}

    assert data_import_datasheet.parameters == expected 

def test_parameter_import(data_import_parameters):
    
    expected  = {'component1.use_N_in': 'true', 'component1.flowCharacteristic.c': '{-0.31462,0.36629,5.0907}', 'component1.p_a_start': 1}
    assert data_import_parameters.parameters == expected

def test_model_modifier_import(data_import_model_modifiers):

    expected = ["redeclare package medium = Modelica.Media.Water.ConstantPropertyLiquidWater", 
                "redeclare function flowCharacteristic = Custom_Pump_V2.BaseClasses_Custom.PumpCharacteristics.quadraticFlow",  
                "redeclare model HeatTransfer = Modelica.Fluid.Vessels.BaseClasses.HeatTransfer.IdealHeatTransfer"]

    assert data_import_model_modifiers.model_modifiers == expected


@pytest.mark.parametrize('input', ['=234', 'redeclare= ', 'redeclare package medium == abc ggg', 'abc'])
def test_model_modifiers_setter_raises_format_exception(data_import, input):
    
    with pytest.raises(ModelModifierFormatError):
        data_import.model_modifiers = [input]


@pytest.mark.parametrize('input', [{'key' :'value'}, 1, 'string', True, (1,2), {1,2,3}])
def test_model_modifiers_setter_raises_type_exception(data_import, input):

    with pytest.raises(TypeError):
        data_import.model_modifiers = input

