import os
import h5py
import shutil
import sys


class FAIR():
    def __init__(self, project_directory, pid_generator  = None, sub_project_folder_name = None):
        self.project_directory = project_directory
        self.pid_generator = pid_generator

        if sub_project_folder_name:
            self.sub_project_folder_name = sub_project_folder_name
            self.sub_project_directory = self.project_directory + "//" + sub_project_folder_name
        else: 
            self.sub_project_folder_name = self.pid_generator_default("Project_Folder")
            self.sub_project_directory = self.project_directory + "//" + self.sub_project_folder_name  
        self.run_name = None
        self.hdf5_file_name = None

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
                if self.pid_generator:
                    self.hdf5_file_name = self.pid_generator("hdf5")+".hdf5"
                    create_HDF5(hdf5_file_name)

                else:
                    self.hdf5_file_name = self.pid_generator_default("hdf5") +".hdf5"
                    create_HDF5(self.hdf5_file_name)

    def create_run_name(self, run_name = None, name_generator = None):

        
        with h5py.File(f'{self.sub_project_directory}\\{self.hdf5_file_name}', 'a') as hdf5:
            number_of_runs = len(list(hdf5.keys()))
       
        if name_generator:
            self.run_name = name_generator(number_of_runs) # possibility to add own naming function
            
        else:
            if run_name:
                self.run_name = f'Run_{number_of_runs + 1}_' + run_name             
            else:
                self.run_name = f'Run_{number_of_runs + 1}'
        

    def create_new_group_hdf5(self, datasheets = True, model_data  = True, code = True):
        
      
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

                        if run_name == 0:
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
        
    def save_results_in_hdf5(self, results, category = 'simulation_data', independent_variable = "time", run_name = None):
        
        #TODO maye add a function for non time series results
        if not run_name:
            run_name = self.run_name
        

        with h5py.File(f'{self.sub_project_directory}\\{self.hdf5_file_name}', 'a') as hdf5:
            folder = hdf5[f'{run_name}/{category}']
            variable_list = list(results.columns)
            if independent_variable in variable_list:
                for variable in list(results.columns):
                    if variable != independent_variable:
                        rec_arr = results[[independent_variable, variable]].to_records()
                        dset = folder.create_dataset(variable, data = rec_arr)
                        
            else:
                for variable in list(results.columns):
                    rec_arr = results[[variable]].to_records()
                    dset = folder.create_dataset(variable, data = rec_arr)

    
        
    def copy_models(self, model_directory):
        pass

    def save_element_in_folder(self):
        pass
    def save_pid_in_hdf5(self):
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
    def save_PID_code(self):
        pass

    def save_plots(self, plots):
        pass
    def save_PID_plots():
        pass

    def pid_generator_default(self, type):
        from datetime import datetime
        now = datetime.now()
        date = now.strftime('%y%m%d')
        signature_number = now.strftime('%H%M%S')
        
        return f'{type}_{date}_{signature_number}'

