import data_import_fmu_export as exp
import sys



def fmu_export(modeling_environment,dymola_path, model_name, model_directory,
                output_directory,datasheet_directory = None, datasheets = {},
                additional_parameters = {},  packages = []):

    
    if modeling_environment.lower().startswith("d"):
        dy = exp.Dymola(model_name,dymola_path, model_directory, output_directory,
                        datasheet_directory, datasheets, additional_parameters, packages) 
        dy.make_dymola_available()
        if datasheets:
            dy.add_parameters()  
        if additional_parameters:
            dy.add_additional_parameters()
        dy.fmu_export()
        
        success = dy.check_fmu_export()
        if success:
            dy.files_management()
        
        else:
            
            _dy = exp.Dymola(model_name,dymola_path, model_directory, output_directory,
                        datasheet_directory, datasheets, additional_parameters, packages)
            _dy.make_dymola_available()
            _success = _dy.export_model_without_added_parameters()

            if _success:
                print("Parameters were added which probalby do not exist.")
                _dy.get_model_parameters()

                _dy.check_if_parameters_exist(dy.getParameters())
            else: 
                dy.show_possible_faults()
                dy.files_management()
                

        

    elif modeling_environment.lower().startswith("o"):
        om = exp.OpenModelica(model_name, model_directory, datasheet_directory, datasheets, additional_parameters, output_directory, packages)
    else:
        raise ValueError("Stopping execution!\n Enter either dymola or openmodelica as the modelling environment.")

def simulation(time, step_size, fmu_dict = {}, controls = {}, result_var_dict = {}):

    from simulate import Simulation

    sim = Simulation(time, step_size, fmu_dic= fmu_dict, controls= controls, result_var_dict = result_var_dict,)
    sim.check_control_class()
    sim.initialise_fmus()
    sim.connect_systems()
    sim.create_result_dict()
    result_dataframe = sim.simulate()[1]
    units = sim.create_unit_dic()

    return result_dataframe, units

def analyze(style_sheet_path,results ,plots):
    pass

def fair(project_directory, pid_generator = None,  sub_project_folder = None, prints = True, hdf5_file_name = None):
    
    from fair import Fair

    fr = Fair(project_directory, pid_generator= pid_generator, sub_project_folder= sub_project_folder,prints= prints , hdf5_file_name=hdf5_file_name)



def fair_simulation(
    plotter = None, custom = {}, custom_analyze = None):
    
    fmu_export()
    simulation()
    if custom_analyze:
        custom_analyze()
    else:
        analyze()
    fair()
