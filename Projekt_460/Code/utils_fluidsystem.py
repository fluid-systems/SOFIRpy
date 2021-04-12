from utils_dymolapy import Dymolapy
import utils_Data as Data
import sys

def create_fmu(model_name, project_directory, datasheet_directory, datasheets,
                additional_parameters, project_owner,
                project_number, run_name, dymola_path, HDF5_file_name, packages):
    """Creates a FMU of a given Dymola model.

    Arg:
        model_name (string):                    The Name of the Modelica model.
        project_directory (string):                The path where the hdf5 file is stored.
        datasheet_directory (string):           The path where the data sheets are stored.
        datasheets (dictionary):                The name of the dymola component and the corresponding data sheet name. 
        additional_parameters (dictionary):     Optional parameters that can be added.
        project_owner (string):                 Abbreviation for owner type    
        project_number (int):                   Project number from FST Excel-sheet     
        run_name (string):                      Name of the simulation run.  
        dymola_path (string):                   The path where the dymola.exe is located.
        packages (list):                        Path to the packages used.

    Returns:
        PIDs (list):                            The PIDs of the output files.
        simulator_log (string):                 The log file from the fmu export.
        custom_settings (list):                 Dictionary with parameters and values.         

    """

    print('Creating the FMU...')
    model_directory =  f'{project_directory}/Fluid_model/'
    output_directory = f'{project_directory}/Runs/{run_name}/'  # was created with new run
    s = Dymolapy(model_name, "dymola", model_directory, datasheet_directory,
                datasheets, additional_parameters,
                output_directory, dymola_path, packages)
    s.make_dymola_available()
    s.add_parameters()
    s.add_additional_parameters()
    s.fmu_export()
    s.move_files()
    success = s.checkFMUexport()
    if not success:
        # Delete created run and exit
        Data.delete_run(project_directory, HDF5_file_name, run_name)
        sys.exit('Stopping execution!')
    s.copy_model()
    s.rename_files(project_owner, project_number, run_name)
    simulator_log = s.read_log_file()
    s.delete_files()
    return s.PIDs, simulator_log, s.custom_settings