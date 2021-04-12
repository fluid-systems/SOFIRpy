#%% Import
import h5py
from datetime import datetime
import os
import shutil
import pandas as pd
import sys

def create_HDF5(project_number, project_owner, project_directory):
    """ Creates a new HDF5 file, if none exists already.

    Args:
        project_number (int):           Project number from FST Excel-sheet
        project_owner (string):         Abbreviation for owner type
        project_directory (string):     Path to hdf5 storing directory
    
    Returns:
        file_name (string):             PID of the HDF5-file created
    
    """
    
    for fname in os.listdir(project_directory):
        if fname.endswith('.hdf5'):
            print(f"Use existing hdf5-file '{fname}'")
            file_name = fname
            break
    else:
        #%% Nomenclature
        type_PID = 'HDF5'   # see list of types in gitlab
        run_PID = '0'       # 0 implies that this file contents multiple runs
        # create PID
        file_name = create_PID(type_PID, project_owner, project_number, run_PID) + '.hdf5'
        # create file
        hdf5 = h5py.File(f'{project_directory}\\{file_name}', 'a')
        print(f"File '{file_name}' created")
        hdf5.close()
    return file_name


def create_PID(type_PID, project_owner, project_number, run_PID):
    """Creates a PID, to reference to data.

    Args:
            type_PID (string):              Datatype of referenced data
            project_owner (string):         Abbreviation for owner type
            project_number (int):           Project number from FST Excel-sheet
            run_PID (int):                  Number of the run, a consecutive number
   
    Returns:
            file_name (string):             Created PID
    
    """

    # define time variables
    now = datetime.now()
    date = now.strftime('%y%m%d')
    signature_number = now.strftime('%H%M%S')  # if you safe more than one file per second please change '%H%M%S' to '%f'
    file_name = f'{type_PID}_{date}_{project_owner}{project_number}_{run_PID}_{signature_number}'
    return file_name


def create_new_run(project_directory, HDF5_file_name, input_run_name = False):
    """Creates a new run, if not already existing. 

    Args:
        project_directory (string):         Path to HDF5 storing directory
        HDF5_file_name (string):            Name of the HDF5 file
        input_run_name (string):            Number of the new run  
   
    Returns:
        run_name (string):                  Name of the created run
    
    """

    # Open file
    with h5py.File(f'{project_directory}\\{HDF5_file_name}', 'a') as hdf5:
        if not input_run_name:
            # Find next run number
            existing_runs = list(hdf5.keys())
            run_numbers = [int(run.split('_')[1]) for run in existing_runs]
            highest_num = max(run_numbers, default= 0)
            run_name = f'Run_{highest_num + 1}'
        else:
            run_name = input_run_name
        # Create folder for linked data
        if not os.path.isdir(f'{project_directory}\\Runs'):
            os.mkdir(f'{project_directory}\\Runs')
        if os.path.isdir(f'{project_directory}\\Runs\\{run_name}'):
            while True:
                overwrite = input(f'The folder {run_name} already exists in your '
                                    f'directory, but not in the HDF5 file. Do you '
                                    f'want to overwrite the folder? [y/n]')
                if (overwrite == 'y') or (overwrite == 'n'):
                    break
                else:
                    print('Not a valid input, try again.')
            if overwrite == 'y':
                shutil.rmtree(f'{project_directory}\\Runs\\{run_name}')
                os.mkdir(f'{project_directory}\\Runs\\{run_name}')
            elif overwrite == 'n':
                while True:
                    custom_run_num = input(f'Enter a custom run number. If you '
                                            f'want to cancel, enter "0"')
                    try:
                        if int(custom_run_num) > 0:
                            run_name = f'Run_{custom_run_num}'
                            run_name = create_new_run(project_directory, HDF5_file_name, run_name)
                            return run_name
                        else:
                            raise SystemExit
                    except SystemExit:
                            sys.exit('Execution canceled')
                    except:
                        print('Not a valid input, try again.')
        else:
            os.mkdir(f'{project_directory}\\Runs\\{run_name}')
        # subgroups
        subgroup1_name = run_name + '/1_digital_datasheet'
        subgroup2_name = run_name + '/2_model_data_fluid_system'
        subgroup3_name = run_name + '/3_simulation_data'
        subgroup4_name = run_name + '/4_results'
        subgroup5_name = run_name + '/5_code'
        # Create HDF5 structure
        hdf5.create_group(run_name)
        hdf5.create_group(subgroup1_name)
        hdf5.create_group(subgroup2_name)
        hdf5.create_group(subgroup3_name)
        hdf5.create_group(subgroup4_name)
        hdf5.create_group(subgroup5_name)
        print(f'{run_name} created')
        structure_of_run = list(hdf5[run_name])
        print(f'Structure of {run_name}: {structure_of_run}')

    return run_name


def save_datasheets(datasheets, datasheet_directory, project_directory,
                                                    HDF5_file_name, run_name):
    """Saves the Datasheets with a PID in the HDF5 file.

    Args:
        datasheets (string):                Name of the datasheet
        datasheet_directory (string):       Path, where the datasheet is saved
        project_directory (string):         Path of the project
        HDF5_file_name (string):            Name of HDF5 file to save the PID
        run_name (string):                  Name of the group of the HDF5-file, the datasheet belongs to
    
    Returns:
        -

    """

    with h5py.File(f'{project_directory}\\{HDF5_file_name}', 'a') as hdf5:
        # save PIDs in dataset
        for component, PID in datasheets.items():
            dset = hdf5.create_dataset(f'./{run_name}/1_digital_datasheet/{component}', data= PID)
            dset.attrs['created on'] = PID.split('_')[2]
            dset.attrs['element type'] = PID.split('_')[3]
            dset.attrs['manufacturer'] = PID.split('_')[4]
            dset.attrs['product name'] = PID.split('_')[5]
            dset.attrs['datatype'] = 'json'
    print('PIDs of datasheets saved')


def save_fmu_data(PIDs, simulator_log, custom_settings, project_directory,
                                            HDF5_file_name, run_name, name_of_packages):
    """ Saves the PID of the fmu in the HDF5 file.

    Args:
        PIDs (list):                    PIDs of the fmu
        simulator_log (string):         Simulationprotocoll
        custom_settings (string):       Custom settings of the fmu
        project_directory (string):     Path of the project
        HDF5_file_name (string):        Name of the HDF5 file
        run_name (string):              Name of the group of the HDF5-file, where the fmu PID is saved
    
    Returns:
        -

    """

    with h5py.File(f'{project_directory}/{HDF5_file_name}', 'a') as hdf5:
        category = '2_model_data_fluid_system'
        folder = hdf5[f'{run_name}/{category}']
        hdf5 = h5py.File(f'{project_directory}\\{HDF5_file_name}', 'a')
        # save PIDs as dataset
        #asciiList = [n.encode("ascii", "ignore") for n in PIDs]
        #hdf5.create_dataset(f'./{run_name}/{category}/PIDs', data= asciiList)
        data_type = ['mo', 'fmu', 'mos']
        for PID, typ in zip(PIDs, data_type):
            PID_type = PID.split('_')[0]
            dset = hdf5.create_dataset(f'./{run_name}/{category}/{PID_type}', data= PID.encode("ascii", "ignore"))
            # add meta data
            dset.attrs['created on'] = PID.split('_')[1]
            dset.attrs['data type'] = typ
            
        # save used packages and version of package as meta data
        for package, version in name_of_packages.items(): 
            folder.attrs[package] = version
        # save custom settings as metadata
        for setting in custom_settings:
            key, value = setting.split('=')
            folder.attrs[key] = value
        # save log as metadata
        folder.attrs['simulator_log'] = simulator_log.encode("ascii", "ignore")
    print('Data and metadata of the fluid model saved in HDF5.')


def delete_run(project_directory, HDF5_file_name, run_name):
    """Deletes run in directory of HDF5-file.

    Args:   
        project_directory (string):          Path of project directory
        HDF5_file_name (string):             Name of the HDF5 file
        run_name (string):                   Name of the run in the HDF5-file
    
    Returns:
        -

    """

    # Delete run in directory and HDF5-file
    with h5py.File(f'{project_directory}/{HDF5_file_name}', 'a') as hdf5:
        del hdf5[run_name]
        shutil.rmtree(f'{project_directory}/Runs/{run_name}', ignore_errors=True)
    print(f'{run_name} deleted\n')


def copy_run(project_directory, use_run, run_name, HDF5_file_name):
    """Copies the run.

    Args:
        project_directory (string):      Path of project directory
        use_run (string):                Name of the used run
        run_name (string):               Name of the new run
        HDF5_file_name (string):         Name of the HDF5 file
    
    Returns:
        PIDs (list):                     Existing PIDs
    
    """

    # copy all model files and the fmu from old run
    old_dir = f'{project_directory}/Runs/{use_run}'
    new_dir = f'{project_directory}/Runs/{run_name}'
    file_names = os.listdir(old_dir)
    if not file_names:
        delete_run(project_directory, HDF5_file_name, run_name)
        sys.exit(f'Error: Directory {old_dir} is empty.\n'
                'Please select another run to copy from or use create_new_fmu = True')
    for file_name in file_names:
        if (file_name.split('.')[-1] == 'fmu') or (file_name.split('.')[-1] == 'mo') or (file_name.split('.')[-1] == 'mos'):
            file_name_copy_path = f'{old_dir}/{file_name}'
            file_name_paste_path = f'{new_dir}/{file_name}'
            shutil.copyfile(file_name_copy_path, file_name_paste_path)
    # copy the first two folders of the hdf5 file
    with h5py.File(f'{project_directory}/{HDF5_file_name}', 'a') as hdf5:
        folders = ['1_digital_datasheet', '2_model_data_fluid_system']
        for folder in folders:
            #read data from old run
            del hdf5[f'{run_name}/{folder}']
            try:
                hdf5[f'{run_name}/{folder}'] = hdf5[f'{use_run}/{folder}']
            except:
                delete_run(project_directory, HDF5_file_name, run_name)
                sys.exit(f'Error: Directory {use_run}/{folder} does not exists in HDF5 file.')
        # return the PIDs of models
        PID_types = list(hdf5[f'{run_name}/{folder}'].keys())
        PIDs = []
        for PID_type in PID_types:
            PIDs.append(hdf5[f'{run_name}/{folder}/{PID_type}'][()].decode("utf-8"))
    print(f'{use_run} copied.')
    return PIDs

def copy_code(project_directory, run_name, project_owner, project_number):
    """Copies the Code into the project directory and returns the PID of the used main.py-file.

    Args:
        project_directory (string):             Path of project directory for the code
        run_name (string):                      Name of the run, the code should be paste
    
    Returns:
        {'main_code' : code_pid} (dictionary):  Dictionary with the PID of the used main.py-file as a value

    """

    run_PID = run_name.split("_")[1]

    code_pid = create_PID('code', project_owner, project_number, run_PID)

    code_files_master_directory = f'{project_directory}/Code'
    code_files = os.listdir(code_files_master_directory)
    code_files_run_directory = f'{project_directory}/Runs/{run_name}'

    for code_name in code_files:
        if code_name != '__pycache__':
            code_copy_path = f'{code_files_master_directory}/{code_name}'
            code_paste_path = f'{code_files_run_directory}/{code_name}'
            shutil.copyfile(code_copy_path, code_paste_path)
    
    os.rename(f'{code_files_run_directory}/main.py', f'{code_files_run_directory}/{code_pid}.py')
    
    print('Code copied and PID assigned')
    return {'main_code' : code_pid}

def save_MAS_metadata(agents, project_directory, HDF5_file_name, run_name):
    """ Saves the metadata from the MAS.

    Args:
        agents (list):                      Pump agents and valve agents
        project_directory (string):         Path of project directory
        HDF5_file_name (string):            Name of the HDF5 file
        run_name (string):                  Name of the Run

    Returns:
        -

    """

    agent_attributes = ['u_name', 'y_name', 'u_bounds', 'memory_time',
                                                            'agent_step_size']
    valve_agent_attributes = ['w_user', 'min_state', 'max_state', 'k_p', 'k_i',
                                                    'step_size', 'threshold']
    pump_agent_attributes = ['u_init']
    category = '3_simulation_data'
    with h5py.File(f'{project_directory}/{HDF5_file_name}', 'a') as hdf5:
        folder = hdf5[f'{run_name}/{category}']
        for agent in agents:
            agent_name = getattr(agent, '_name')
            agent_type = type(agent).__name__
            if agent_type == 'Valve_Agent':
                attributes = agent_attributes + valve_agent_attributes
            elif agent_type == 'Pump_Agent':
                attributes = agent_attributes + pump_agent_attributes
            for attribute in attributes:
                folder.attrs[f'{agent_name}.{attribute}'] = getattr(agent, attribute)
    print('Metadata of the MAS saved in HDF5')


def save_MAS_data(recorded_values, project_directory, HDF5_file_name, run_name):
    """Saves data of the MAS in the HDF5 file.

    Args:
        recorded_values (dict):             As returned by "return_record()" of "Recorder"
        project_directory (string):         Path of project directory
        HDF5_file_name (string):            Name of the HDF5 file
        run_name (string):                  Name of the Run
    
    Retuns:
        -

    """

    category = '3_simulation_data'
    record = dict(recorded_values)  # create copy of dict, so changes won't have global effect
    valve_agents = record['valve_agent_names']
    pump_agents = record['pump_agent_names']
    time_series = record['time_series']
    del record['valve_agent_names']
    del record['pump_agent_names']
    del record['time_series']
    with h5py.File(f'{project_directory}/{HDF5_file_name}', 'a') as hdf5:
        folder = hdf5[f'{run_name}/{category}']
        for key, value in record.items():
            if 'user' not in key.split('_'):
                series_type = key.split('_')[0]
            else:
                series_type = key.split('_')[0] + '_user'
            agent_type = key.split('_')[-1]
            if agent_type == 'valves':
                for i, agent in enumerate(valve_agents):
                    dset = folder.create_dataset(f'{series_type}.{agent}',
                                                            data= value[:,i])
                    dset.attrs['time-series'] = time_series
                    dset.attrs['unit'] = 1 if series_type == 'u' else 'm^3/h'
            elif agent_type == 'pumps':
                for i, agent in enumerate(pump_agents):
                    dset = folder.create_dataset(f'{series_type}.{agent}',
                                                            data= value[:,i])
                    dset.attrs['time-series'] = time_series
                    dset.attrs['unit'] = 1 if series_type == 'u' else 'Pa'
    print('Data of the MAS saved in HDF5')


def save_rmse(rmse, project_directory, HDF5_file_name, run_name):
    """Saves Root-mean-square deviation in HDF5 file.

    Args:
        rmse (function):                    Function to calculate the root-mean-square
        project_directory (string):         Path of project directory
        HDF5_file_name (string):            Name of the HDF5 file
        run_name (string):                  Name of the Run
    
    Retuns:
        -

    """

    category = '4_results'
    with h5py.File(f'{project_directory}/{HDF5_file_name}', 'a') as hdf5:
        folder = hdf5[f'{run_name}/{category}']
        for agent_name, rmse in rmse.items():
            folder.attrs[f'{agent_name}.rmse'] = rmse
    print('RMSE of the valve agents saved in HDF5')

def save_PIDs_plots(PIDs, project_directory, HDF5_file_name, run_name):
    """ Saves PIDs of the generated plots.

    Args:
        PIDs (list):                        PIDs of the plots
        project_directory (string):         Path of project directory
        HDF5_file_name (string):            Name of the HDF5 file
        run_name (string):                  Name of the Run                 
    
    Returns: 
        -
    """

    category = '4_results'
    with h5py.File(f'{project_directory}/{HDF5_file_name}', 'a') as hdf5:
        folder = hdf5[f'{run_name}/{category}']
        for PID_name, PID in PIDs.items():
            folder.create_dataset(f'{PID_name}', data= PID)
    print(f'Plot PIDs saved in HDF5.')

def save_PID_code(PID, project_directory, HDF5_file_name, run_name):
    """ Saves PID of the main code file.

    Args:
        PID (dict):                         Dictionary with the PID of the used main.py-file as a value
        project_directory (string):         Path of project directory
        HDF5_file_name (string):            Name of the HDF5 file
        run_name (string):                  Name of the Run                 
    
    Returns: 
        -
    """
    category = '5_code'
    with h5py.File(f'{project_directory}/{HDF5_file_name}', 'a') as hdf5:
        folder = hdf5[f'{run_name}/{category}']
        for PID_name, PID in PID.items():
            dset = folder.create_dataset(f'{PID_name}', data= PID)
            dset.attrs['data type'] = 'py'
    print(f'Code PID saved in HDF5.')