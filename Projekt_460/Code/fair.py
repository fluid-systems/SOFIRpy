import os
import h5py
import shutil
import sys
import time

from pandas.core.frame import DataFrame


class FAIR():
    def __init__(self, project_directory ,pid_generator  = None, sub_project_folder_name = None, prints = True, hdf5_file_name = None):
        self.project_directory = project_directory
        self.pid_generator = pid_generator

        if hdf5_file_name:
            self.hdf5_file_name = hdf5_file_name +".hdf5"
        else:
            self.hdf5_file_name = hdf5_file_name

        if sub_project_folder_name:
            self.sub_project_folder_name = sub_project_folder_name
            self.sub_project_directory = self.project_directory + "//" + sub_project_folder_name
        else: 
            self.sub_project_folder_name = self.pid_generator_default("Project_Folder")
            self.sub_project_directory = self.project_directory + "//" + self.sub_project_folder_name  
        self.run_name = None
        
        if pid_generator:
            self.pid_generator = pid_generator
        else:
            self.pid_generator = self.pid_generator_default

        self.prints = prints
        

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
                
    def set_hdf5_file_name(self):

        if not self.hdf5_file_name:
            files = os.listdir(self.sub_project_directory)
            hdf5s = list(filter( lambda file: file.endswith(".hdf5"), files))
            if not hdf5s:
                print("The hdf5 has not been created yet.")

            if len(hdf5s) > 1:
                sys.exit(f"There should only be one hdf5 file in {self.sub_project_directory}")

                #print(hdf5s)
                # while True:
                #     index = input("Chose hdf5s --> input index")
                #     try:
                #         _index = int(index)
                #     except ValueError: 
                #         print("Inputs needs to be an integer")
                #     if _index in range(len(hdf5s)):
                #         self.hdf5_file_name = hdf5s[_index]
                #         break
                #     else:
                #         print(f"The index needs to be in the range of 0 to {len(hdf5s)-1}")
                    
                
            else:
                self.hdf5_file_name = hdf5s[0]
        

    def create_run_name(self, run_name = None, name_generator = None):

        if not self.hdf5_file_name:
            self.set_hdf5_file_name(self)

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
            hdf5.create_group(self.run_name)
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

    # def _save_results_in_hdf5(self, results, category = 'simulation_data', independent_variable = "time", run_name = None):
        
    #     import pandas as pd

    #     variable_list = list(results.columns)
    #     if independent_variable in variable_list:
    #         for variable in variable_list:
    #             data = results[[independent_variable, variable]]
    #             data.to_hdf(f'{self.sub_project_directory}\\{self.hdf5_file_name}', key = "df", mode = "w")




    def copy_models(self, model_directory, fmus_names, custom_elements = []):
        
        model_files = os.listdir(model_directory)
        copied_models = []
        copied_custom_elements = []
        for model in model_files:
            if model.endswith(".mo"):
                if model[:-3] in fmus_names and fmus_names:
                    if len(fmus_names) == 1:
                        _model = "model"
                    else:
                        _model = model[:-3] 
                    time.sleep(1)
                    model_copy_path = f'{model_directory}/{model}'
                    model_paste_path = f'{self.sub_project_directory}/{self.run_name}/{self.pid_generator(_model)}.mo'
                    shutil.copyfile(model_copy_path, model_paste_path)
                    copied_models.append(model)
                elif model[:-3] in custom_elements and custom_elements:
                    model_copy_path = f'{model_directory}/{model}'
                    model_paste_path = f'{self.sub_project_directory}/{self.run_name}/{model}'
                    shutil.copyfile(model_copy_path, model_paste_path)
                    copied_custom_elements.append(model)
                
    
        if self.prints:
            if copied_custom_elements:
                cus = ",".join(copied_custom_elements)
            else:
                cus = "None"
            print("Models copied: " + ",".join(copied_models) + "\nCustom elements copied: " + cus)
            

    def save_element_in_folder(self):
        pass
    def save_pid_in_hdf5(self):

        category = {"model": "model_data", "code": "code_data", "plot" : "plots"}

        with h5py.File(f'{self.sub_project_directory}\\{self.hdf5_file_name}', 'a') as hdf5:

            pass

        
        
    def save_datasheets_in_folder(self, datasheets_directory):
        pass
    def save_datasheets_name_in_hdf5(self, datasheets):
        
        with h5py.File(f'{self.sub_project_directory}\\{self.hdf5_file_name}', 'a') as hdf5:
            for component, name in datasheets.items():
                dset = hdf5.create_dataset(f'./{self.run_name}/digital_datasheet/{component}', data = name)

        print('Names of used datasheets saved in hdf5')

    def save_fmu_pid(self):
        pass
    def copy_code(self):
        pass
    def save_pid_code(self):
        pass

    def save_plots(self, plots):
        pass
    def save_pid_plots():
        pass

    def pid_generator_default(self, type):
        from datetime import datetime
        now = datetime.now()
        date = now.strftime('%y%m%d')
        signature_number = now.strftime('%H%M%S')
        
        return f'{type}_{date}_{signature_number}'

    
    def get_data(self, run_name,dataset_name, category = "simulation_data"):
        
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
