import os
import h5py
import shutil
import sys
from datetime import datetime
import time
from pandas.core.frame import DataFrame
import matplotlib.pyplot as plt

class InitiateProject:

    def __init__(self, project_directory, hdf5_file_name = None, pid_generator = None, sub_project_folder = None):

        self.project_directory = project_directory
        if sub_project_folder:
            self.sub_project_folder = sub_project_folder
        self.working_directory = os.path.join(self.project_directory, self.sub_project_folder) if sub_project_folder else self.project_directory
        self.pid_generator = pid_generator if pid_generator else generate_default_pid
        self.hdf5_file_name = hdf5_file_name
        self.hdf5_path = os.path.join(self.working_directory, self.hdf5_file_name)

    @property
    def project_directory(self):
        return self._project_directory

    @project_directory.setter
    def project_directory(self, project_directory):

        if os.path.exists(project_directory):
            self._project_directory = project_directory

        else:
            raise DirectoryDoesNotExistError(f"The directory {project_directory} does not exist. Create it first.")
    
    @property
    def sub_project_folder(self):
        return self._sub_project_folder

    @sub_project_folder.setter
    def sub_project_folder(self, sub_project_folder):
        path = os.path.join(self.project_directory + sub_project_folder)
        if not os.path.exists(path):
            os.makedirs(path)
        self._sub_project_folder = sub_project_folder

    @property
    def hdf5_file_name(self):
        return self._hdf5_file_name

    @hdf5_file_name.setter
    def hdf5_file_name(self, hdf5_file_name):

        files = os.listdir(self.working_directory)
        hdf5s = list(filter(lambda file: file.endswith(".hdf5"), files))
        if len(hdf5s) > 1:
            raise MoreThenOneHdf5Error(f"'{self.working_directory}' should only have one hdf5 inside.")

        if hdf5_file_name:
            name = hdf5_file_name if hdf5_file_name.endswith(".hdf5") else hdf5_file_name + ".hdf5"
            if not hdf5s:
                self.create_hdf5(os.path.join(self.working_directory, name))
                self._hdf5_file_name = name
            else:
                if hdf5s[0] == name:
                    self._hdf5_file_name = name
                    print(f"Using existing hdf5 '{self._hdf5_file_name}'")
                else:
                    raise MoreThenOneHdf5Error(f"In '{self.working_directory}' already exists a hdf5 file with the name '{hdf5s[0]}'. Can't create a second one with the name '{name}'.")        
        else:
            if hdf5s:
                self._hdf5_file_name = hdf5s[0]
                print(f"Using existing hdf5 '{self._hdf5_file_name}'")
            else:
                name = self.pid_generator("hdf5") + ".hdf5"
                self.create_hdf5(os.path.join(self.working_directory, name))
                self._hdf5_file_name = name
    
    def create_hdf5(self, hdf5_path):
        hdf5 = h5py.File(f'{hdf5_path}', 'a')
        print(f"File '{hdf5_path}' created")
        hdf5.close()

class RunCreation:

    def __init__(self,name_data: InitiateProject, generate_run_name = None):

        self.name_data = name_data
        self.generate_run_name = generate_run_name if generate_run_name else self.generate_default_run_name
        self.current_run_name = None

    def create_run(self, run_name = None, hdf5_sub_groups = None):

        number_of_runs = self.get_number_of_runs()
        self.current_run_name = self.generate_run_name(run_name, number_of_runs)
        self.check_run_exists()
        self.create_hdf5_run(hdf5_sub_groups)
        self.create_run_folder()

    def create_hdf5_run(self, hdf5_sub_groups):
        
       with h5py.File(f'{self.name_data.hdf5_path}', 'a') as hdf5:
            
            #TODO maybe add number for a specific order
            group = hdf5.create_group(self.current_run_name)
            group.attrs['creation date'] = datetime.now().strftime('%A, %d. %B %Y, %H:%M:%S')
            if not hdf5_sub_groups:
                hdf5_sub_groups = ['/digital_datasheet', '/model_data', '/simulation_data', '/code', '/plots']
            else:
                x = lambda sub: "/" + sub if not sub.startswith("/") else sub
                hdf5_sub_groups = list(map(x, hdf5_sub_groups))
                
            for sub in hdf5_sub_groups:
                hdf5.create_group(self.current_run_name + sub)
            
            print(f"{self.current_run_name} created")

    def create_run_folder(self):
        
        folder_path = os.path.join(self.name_data.working_directory, self.current_run_name) 
        
        os.mkdir(folder_path)

    def check_run_exists(self):
        
        with h5py.File(self.name_data.hdf5_path, 'a') as hdf5:
            runs = list(hdf5.keys())

        exists_in_hdf5 = False
        if self.current_run_name in runs:
            exists_in_hdf5 = True

        folder_path = os.path.join(self.name_data.working_directory, self.current_run_name) 
        exists_as_folder = False
        if os.path.exists(folder_path):
            exists_as_folder = True

        if exists_as_folder:
            if exists_in_hdf5:
                while True:
                    overwrite = input(f"The run '{self.current_run_name}' already exists in the hdf5 and as a folder in {self.name_data.working_directory}. Overwrite? [y/n]")
                    if overwrite == "y":
                        self.delete_run(self.current_run_name)
                        break
                    elif overwrite == "n":
                        raise RunAlreadyExistError("Runs already exist.")

            else:
                overwrite = input(f"The run '{self.current_run_name}' exists as a folder but not in the hdf5. Overwrite? [y/n]")
                while True:
                    if overwrite == "y":
                        self.delete_run_folder(self.current_run_name)
                        break
                    elif overwrite == "n":
                        raise RunAlreadyExistError("Run already exist.")

        else:
            if exists_in_hdf5:
                while True:
                    overwrite = input(f"The run '{self.current_run_name}' already exists in the hdf5 but not as a folder. Overwrite = [y/n]")
                    if overwrite == "y":
                        self.delete_hdf5_run(self.current_run_name)
                        break
                    elif overwrite == "n":
                        raise RunAlreadyExistError("Run already exist.")

    def delete_run_folder(self, run_name):

        try:
            shutil.rmtree(os.path.join(self.name_data.working_directory, run_name))
        except FileNotFoundError as err:
            print(err)

    def delete_hdf5_run(self, run_name):
        
        with h5py.File(self.name_data.hdf5_path, 'a') as hdf5:
            try:
                del hdf5[run_name]
            except KeyError as err:
                print(err, f". '{run_name}' doesn't exists.")
                
    def delete_run(self, run_name):

        self.delete_run_folder(run_name)
        self.delete_hdf5_run(run_name)

    def generate_default_run_name(self, run_name: str, number_of_runs: int) -> str:

        if run_name:
            return f'Run_{number_of_runs + 1}_' + run_name
        return f'Run_{number_of_runs + 1}'
        
    def get_number_of_runs(self) -> int:

        return len(self.get_hdf5_runs())

    def get_hdf5_runs(self) -> list:

        with h5py.File(self.name_data.hdf5_path, 'a') as hdf5:
            return list(hdf5.keys())

class ReadWriteHDF5Data:

    def __init__(self, hdf5_path):

        self.hdf5_path = hdf5_path

    def save_data(self, data, data_name, hdf5_folder_name,  attributes: dict = None):

        with h5py.File(self.hdf5_path, 'a') as hdf5:
            folder = hdf5[hdf5_folder_name]
            dset = folder.create_dataset(data_name, data = data)
            if attributes:
                for name, attr in attributes.items():
                    dset.attrs[name] = attr

    def get_data(self, name , get_attribute = False):
    
        with h5py.File(self.hdf5_path, 'a') as hdf5:
            _data = hdf5.get(name)
            if isinstance(_data, h5py.Dataset):
                data = _data[()]

            if isinstance(_data, h5py.Group):
                data =list(_data.keys())
            
            if get_attribute:
                attr = dict(_data.attrs)
                return data, attr
        return data 


class FolderStore:

    def __init__(self, folder_path, pid_generator = None):

        self.folder_path = folder_path
        self.pid_generator = pid_generator if pid_generator else generate_default_pid

    def save_fmu(self, fmu_path):

        fmu_pid = self.pid_generator("fmu") 
        paste_path = os.path.join(self.folder_path, fmu_pid + ".fmu")
        shutil.copy(fmu_path, paste_path)

        return fmu_pid

    def save_models(self, models):

        # models = [{"model name": "", "model directory": "" , "custom elements": []}, ...]
        
        models_meta_data = []

        for model in models:

            model_meta_data = {}
            copy_path_model = os.path.join(model["model directory"], model["model name"] + ".mo")
            model_pid = self.pid_generator("mo")
            model_meta_data["model pid"] = model_pid 
            paste_path_model = os.path.join(self.folder_path, model_pid + ".mo")
            shutil.copyfile(copy_path_model, paste_path_model)

            model_meta_data["custom element": model["custom_elements"] if model["custom_elements"] else None]
            for custom_element in model["custom_elements"]:
                copy_path_element = os.path.join(model["model directory"], custom_element + ".mo")
                paste_path_element = os.path.join(self.folder_path, custom_element + ".mo")
                shutil.copyfile(copy_path_element, paste_path_element)
            models_meta_data.append(model_meta_data)

        return model_meta_data

    def save_plots(self, plots, image_type = "png"):

        plots_meta_data = []
        
        for plot in plots:
            plot_pid = self.pid_generator("plot")
            plt.savefig(os.path.join(self.folder_path, plot_pid + "." + image_type)) 
            plot_title = plot.get_title()
            x_label = plot.get_xlabel()
            y_label = plot.get_ylabel()
            plot_meta_data = {"plot pid": plot_pid, "plot title" : plot_title, "x label": x_label, "y_label": y_label}
            plots_meta_data.append(plot_meta_data)

        return plots_meta_data


def generate_default_pid(type: str):
    now = datetime.now()
    date = now.strftime('%y%m%d')
    signature_number = now.strftime('%H%M%S')
    
    return f'{type}_{date}_{signature_number}'

def store_date(project_directory, data, hdf5_file_name = None, pid_generator = None, sub_project_folder = None, 
                generate_run_name = None, current_run_name = None, run_name = None, run_groups = None):

    # data  = [{"data": , "data name": "", "hdf5_folder_name": "", attr: {} oder None }]

    h5 = InitiateProject(project_directory, hdf5_file_name, pid_generator, sub_project_folder)
    run = RunCreation(h5, generate_run_name)
    if current_run_name:
        run.current_run_name = current_run_name
    else:
        run.create_run(run_name, run_groups)
    write_hdf5 = ReadWriteHDF5Data(h5.hdf5_path)

    try:
        for _data in data:
            dt = _data["data"]
            data_name = _data["data name"]
            folder = _data["hdf5_folder_name"]
            loc = f"{run.current_run_name}/{folder}"
            attr = _data["attr"]
            write_hdf5.save_data(dt, data_name, loc, attr)
    except Exception as e:
        run.delete_run()
        raise e

def read_data(project_directory, data_name, get_attribute = False, hdf5_file_name = None, sub_project_folder = None):

    h5 = InitiateProject(project_directory, hdf5_file_name, sub_project_folder=sub_project_folder)
    read_hdf5 = ReadWriteHDF5Data(h5.hdf5_path)
    if get_attribute:
        return read_hdf5.get_data(data_name, get_attribute)
    return read_hdf5.get_data(data_name)

class Fair:
    def __init__(self, project_directory ,pid_generator  = None, sub_project_folder = None, hdf5_file_name = None):
        self.project_directory = project_directory
        self.pid_generator = pid_generator

        if hdf5_file_name:
            self.hdf5_file_name = hdf5_file_name +".hdf5"
        else:
            self.hdf5_file_name = None

        if sub_project_folder:
            self.sub_project_folder = sub_project_folder
            self.sub_project_directory = self.project_directory + "/" + sub_project_folder
        else: 
            self.sub_project_folder = self.pid_generator_default("Project_Folder")
            self.sub_project_directory = self.project_directory + "/" + self.sub_project_folder  
        self.run_name = None #TODO check 
        
        if pid_generator:
            self.pid_generator = pid_generator
        else:
            self.pid_generator = self.pid_generator_default

     

    @property
    def hdf5_file_name(self):
        return self.hdf5_file_name
        
    def get_project_directory(self):
        return self.project_directory

    def set_project_directory(self, project_directory):
        if os.path.exists(project_directory):
            self.project_directory = project_directory
        else:
             raise OSError(f"The direcotry '{project_directory}' does not exist.")

    def get_sub_project_folder(self):
        return self.sub_project_folder

    def set_sub_project_folder(self, sub_project_folder):
        if os.path.exists(self.project_directory + "/" +sub_project_folder):
             self.sub_project_folder = sub_project_folder
             self.sub_project_directory = self.project_directory + "/" + sub_project_folder
        else:
            raise OSError(f"The direcotry '{self.project_directory}/{sub_project_folder}' does not exist.")
        
    

    def create_project_folder(self):
        
        if not os.path.isdir(f'{self.sub_project_directory}'):
            os.mkdir(f'{self.sub_project_directory}')


    def create_HDF5_file(self, hdf5_file_name = None):
        
        def create_HDF5(hdf5_file_name):
            hdf5 = h5py.File(f'{self.sub_project_directory}\\{hdf5_file_name}', 'a')
            print(f"File '{hdf5_file_name}' created")
            hdf5.close()

        for fname in os.listdir(self.sub_project_directory):
            if fname.endswith('.hdf5'):
                print(f"Use existing hdf5-file '{fname}'")
                self.hdf5_file_name = fname
                break
        else:
            if hdf5_file_name:
                self.hdf5_file_name = hdf5_file_name
                create_HDF5(self.hdf5_file_name)
            else:
                
                self.hdf5_file_name = self.pid_generator("hdf5")+".hdf5"
                create_HDF5(self.hdf5_file_name)
                #else:
                    #self.hdf5_file_name = self.pid_generator_default("hdf5")+".hdf5"
                    #create_HDF5(hdf5_file_name)
                
    def set_hdf5_file_name(self, hdf5_file_name = None):

        if hdf5_file_name:
                if os.path.exists(f'{self.sub_project_directory}\\{hdf5_file_name}.hdf5'):
                    self.hdf5_file_name = hdf5_file_name
                else:
                    raise FileNotFoundError(f"The hdf5 '{hdf5_file_name}'' does not exists in '{self.sub_project_directory}'.")
        else:
            if not self.hdf5_file_name:
                files = os.listdir(self.sub_project_directory)
                hdf5s = list(filter( lambda file: file.endswith(".hdf5"), files))
                if not hdf5s:
                    print("The hdf5 has not been created yet.")

                if len(hdf5s) > 1:
                    raise SystemExit(f"There should only be one hdf5 file in {self.sub_project_directory}")

                else:
                    self.hdf5_file_name = hdf5s[0]

    def get_hdf5_file_name(self):
        return self.hdf5_file_name

    def set_run_name(self, run_name):
        self.run_name = run_name

    def get_run_name(self):
        return self.run_name

    def create_run_name(self, run_name = None, name_generator = None):

        if not self.hdf5_file_name:
            self.set_hdf5_file_name()

        with h5py.File(f'{self.sub_project_directory}\\{self.hdf5_file_name}', 'a') as hdf5:
            number_of_runs = len(list(hdf5.keys()))
       
        if name_generator:
            self.run_name = name_generator(number_of_runs) # possibility to add own naming function
            
        else:
            if run_name:
                self.run_name = f'Run_{number_of_runs + 1}_' + run_name             
            else:
                self.run_name = f'Run_{number_of_runs + 1}'
        

    def create_new_group_hdf5(self, datasheets = True, model_data  = True, code = True, plots = True):
        
      
        with h5py.File(f'{self.sub_project_directory}\\{self.hdf5_file_name}', 'a') as hdf5:
            
            #TODO maybe add number for a specific order
            group = hdf5.create_group(self.run_name)
            group.attrs['creation date'] = datetime.now().strftime('%A, %d. %B %Y, %H:%M:%S')
            if datasheets:
                hdf5.create_group(self.run_name + '/digital_datasheet')
            if model_data:
                hdf5.create_group(self.run_name + '/model_data')
            hdf5.create_group(self.run_name +'/simulation_data')
            if code:
                hdf5.create_group(self.run_name + '/code')
            if plots:
                hdf5.create_group(self.run_name + '/plots')
            
            print(f"{self.run_name} created")
            print(f"Structure of {self.run_name} in {self.hdf5_file_name}:{list(hdf5[self.run_name])}")

            

    def create_new_run_folder(self):

            if os.path.isdir(f'{self.sub_project_directory}\\{self.run_name}'):

                while True:
                    overwrite = input(f"The folder {self.run_name} already exists in your directory. Do you want to overwrite the folder? [y/n]")
                    if (overwrite == 'y') or (overwrite == 'n'):
                        break
                    else:
                        print("Enter 'y' or 'n'")
                if overwrite == 'y':
                    shutil.rmtree(f'{self.sub_project_directory}\\{self.run_name}')
                    os.mkdir(f'{self.sub_project_directory}\\{self.run_name}')
                elif overwrite == 'n':
                    while True:
                        run_name = input(f'Enter a custom run name. If you want to cancel, enter "0"')

                        if run_name == '0': 
                            sys.exit('Execution canceled')
                        else:
                            self.run_name = run_name
                            worked = self.create_new_run_folder()
                            if worked:
                                break



            else:
                os.mkdir(f'{self.sub_project_directory}\\{self.run_name}')

                return True

    def delete_run(self, run_name):

        with h5py.File(f'{self.sub_project_directory}\\{self.hdf5_file_name}', 'a') as hdf5:
            del hdf5[run_name]

        shutil.rmtree(f'{self.sub_project_directory}\\{run_name}')

        print(f'{run_name} in folder and hdf5 deleted\n')
        
    def save_results_in_hdf5(self, results, units = {}, category = 'simulation_data', independent_variable = "time", run_name = None):
        
        #TODO maye add a function for non time series results
        if not run_name:
            run_name = self.run_name
        

        with h5py.File(f'{self.sub_project_directory}\\{self.hdf5_file_name}', 'a') as hdf5:
            folder = hdf5[f'{run_name}/{category}']
            variable_list = list(results.columns)
            if independent_variable in variable_list:
                for variable in variable_list:
                    if variable != independent_variable:
                        rec_arr = results[[independent_variable, variable]].to_records()
                        dset = folder.create_dataset(variable, data = rec_arr)
                        if variable in units:
                            if units[variable]:
                                dset.attrs['unit'] = units[variable] 
                            else:
                                dset.attrs['unit'] = "None"                       
            else:
                for variable in variable_list:
                    rec_arr = results[[variable]].to_records()
                    dset = folder.create_dataset(variable, data = rec_arr)

    def _save_results_in_hdf5(self, results, category = 'simulation_data', independent_variable = "time", run_name = None):
        
        import pandas as pd

        variable_list = list(results.columns)
        if independent_variable in variable_list:
            for variable in variable_list:
                data = results[[independent_variable, variable]]
                data.to_hdf(f'{self.sub_project_directory}\\{self.hdf5_file_name}', key = "df", mode = "w")




    def copy_models(self, model_directory, fmus_names, custom_elements = []):
        
        model_files = os.listdir(model_directory)
        copied_models = []
        copied_custom_elements = []
        model_pids = []
        custom_element_pids = []
        category = "model_data"
        with h5py.File(f'{self.sub_project_directory}\\{self.hdf5_file_name}', 'a') as hdf5:
            folder = hdf5[f'{self.run_name}/{category}']
            for model in model_files:
                if model.endswith(".mo"):
                    if model[:-3] in fmus_names:
                        _model = model[:-3] 
                        time.sleep(1)
                        model_copy_path = f'{model_directory}/{model}'
                        pid = self.pid_generator(_model)
                        model_pids.append(pid)
                        model_paste_path = f'{self.sub_project_directory}/{self.run_name}/{pid}.mo'
                        shutil.copyfile(model_copy_path, model_paste_path)
                        copied_models.append(model)

                        folder.create_dataset(_model, data = pid) 

                    elif model[:-3] in custom_elements:
                        model_copy_path = f'{model_directory}/{model}'
                        model_paste_path = f'{self.sub_project_directory}/{self.run_name}/{model}'
                        shutil.copyfile(model_copy_path, model_paste_path)
                        copied_custom_elements.append(model)
            
            folder.attrs["models used"] = ",".join(copied_models) #TODO add packages used

            if copied_custom_elements:
                cus = ",".join(copied_custom_elements)
            else:
                cus = "None"
            folder.attrs["custom elements used"] = cus

        
            
        print("Models copied: " + ",".join(copied_models) + "\nCustom elements copied: " + cus)

    def save_datasheets_name_in_hdf5(self, datasheets):
        
        with h5py.File(f'{self.sub_project_directory}\\{self.hdf5_file_name}', 'a') as hdf5:
            for component, name in datasheets.items():
                dset = hdf5.create_dataset(f'./{self.run_name}/digital_datasheet/{component}', data = name)

        print('Names of used datasheets saved in hdf5')

    def save_fmu(self, fmu_path, creat_new_fmu, use_run = None, move = True):

        pid = self.pid_generator("fmu")
        if creat_new_fmu:
            mew_fmu_path = f'{self.sub_project_directory}/{self.run_name}/{pid}.fmu'
            if move:
                shutil.move(fmu_path, mew_fmu_path)
            else:
                shutil.copy(fmu_path, mew_fmu_path)
        else:
            if not use_run:
                raise ValueError("If the variable 'creat_new_fmu' is set to false the variable 'use_run' has to be specified.")
            else:
                fmus = []
                for fname in os.listdir(f'{self.sub_project_directory}/{use_run}'):
                    if fname.endswith(".fmu"):
                        fmus.append(fname)
                if len(fmus) == 1:
                    fmu_name = fmus[0]
                elif len(fmus) ==0:
                    raise Exception(f"No fmu in directory '{self.sub_project_directory}/{use_run}'.")
                elif len(fmus) >1:
                    raise Exception(f"There should only be one fmu in '{self.sub_project_directory}/{use_run}'.")
                
                copy_path = f'{self.sub_project_directory}/{use_run}/{fmu_name}'
                paste_path = f'{self.sub_project_directory}/{self.run_name}/{pid}.fmu'
                shutil.copy(copy_path, paste_path)

        category = "model_data"

        with h5py.File(f'{self.sub_project_directory}\\{self.hdf5_file_name}', 'a') as hdf5:
            folder = hdf5[f'{self.run_name}/{category}']
            dset = folder.create_dataset("fmu", data = pid)
            #date_cre = self.get_creation_date(fmu_path)
            #dset.attrs["creation date"] = date_cre
   
    def copy_code(self):
        pass
    def save_pid_code(self):
        pass

    def save_plots(self, plots):
        
        import matplotlib.pyplot as plt

        category = 'plots'
        with h5py.File(f'{self.sub_project_directory}\\{self.hdf5_file_name}', 'a') as hdf5:
            folder = hdf5[f'{self.run_name}/{category}']
            for plot in plots:
                pid = self.pid_generator("plot")
                plt.savefig(f'{self.sub_project_directory}/{self.run_name}/{pid}.png')
                plot_title = plot.get_title()
                x_label = plot.get_xlabel()
                y_label = plot.get_ylabel()
                dset = folder.create_dataset(plot_title, data= pid)
                dset.attrs['x_label'] = x_label
                dset.attrs['y_label'] =y_label

    def pid_generator_default(self, type):
        
        now = datetime.now()
        date = now.strftime('%y%m%d')
        signature_number = now.strftime('%H%M%S')
        
        return f'{type}_{date}_{signature_number}'

    
    def get_data(self, run_name,dataset_name, category = "simulation_data"): #TODO read other data besides time series
        
        import numpy as np
        import pandas as pd

        if not self.hdf5_file_name:
            self.set_hdf5_file_name()

        with h5py.File(f'{self.sub_project_directory}\\{self.hdf5_file_name}', 'r') as hdf5:
            runs = list(hdf5.keys())
            if run_name not in runs:
                raise Exception(f"{run_name} doesnt exist in {self.hdf5_file_name}")
            
            dataset_names = list(hdf5.get(f'{run_name}/{category}').keys())

            if dataset_name not in dataset_names:
                raise Exception(f'{dataset_name} not part of {run_name}/{category} in {self.hdf5_file_name}.') 
            
            data = hdf5.get(f'{run_name}/{category}/{dataset_name}')
            df = pd.DataFrame(np.array(data))
            df.pop("index")

        return df

    def get_last_modified_date(self, path):

        ti_m = os.path.getmtime(path)
        m_ti = time.ctime(ti_m)
        t_last_mod = time.strftime('%A, %d. %B %Y, %H:%M:%S', time.strptime(m_ti))
    	
        return t_last_mod
        
    def get_creation_date(self, path):
        ti_c = os.path.getctime(path)
        m_ti = time.ctime(ti_c)
        t_created = time.strftime('%A, %d. %B %Y, %H:%M:%S', time.strptime(m_ti))
    	
        return t_created

class DirectoryDoesNotExistError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)

class MoreThenOneHdf5Error(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)

class RunNotFoundError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)

class RunAlreadyExistError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)