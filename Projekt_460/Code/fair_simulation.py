import data_import_fmu_export as exp
import sys



def fmu_export(create_new_fmu, modeling_environment,model_name, model_directory,
                    datasheet_directory, datasheets, additional_parameters,
                    output_directory, dymola_path, packages):

    if create_new_fmu:
        if modeling_environment.lower().startswith("d"):
            dy = exp.Dymola(model_name, "dymola", model_directory, datasheet_directory, datasheets, additional_parameters, output_directory, dymola_path, packages) 
            dy.make_dymola_available()
            dy.add_parameters()        
            dy.add_additional_parameters()
            dy.fmu_export()
            success = dy.check_fmu_export()
            if success:
                dy.files_management()
            
            else:
                _dy = exp.Dymola(model_name, "dymola", model_directory, datasheet_directory, datasheets, additional_parameters, output_directory, dymola_path, packages)
                _dy.make_dymola_available()
                _success = _dy.export_model_without_added_parameters()

                if _success:
                    print("Parameters were added which probalby do not exist.")
                    _dy.get_model_parameters()
                    _dy.check_if_parameters_exist()
                else: 
                    dy.show_possible_faults()
                    dy.files_management()
                    

            

        elif modeling_environment.lower().startswith("o"):
            om = exp.OpenModelica(model_name, model_directory, datasheet_directory, datasheets, additional_parameters, output_directory, packages)
        else:
            sys.exit("Stopping execution!\n Enter either dymola or openmodelica as the modelling environment.")
