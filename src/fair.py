import os
import h5py
import shutil
import sys
from datetime import datetime
from h5py._hl import group
import time

from pandas.core.frame import DataFrame


class Fair():
    def __init__(self, project_directory ,pid_generator  = None, sub_project_folder = None, prints = True, hdf5_file_name = None):
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

        self.prints = prints

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

        if self.prints:
            
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