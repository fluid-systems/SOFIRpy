import os
import h5py
from datetime import datetime

class FAIR():
    def __init__(self, project_directory, pid_generator  = None):
        self.project_directory = project_directory
        self.pid_generator = pid_generator

    def create_HDF5_file(self, hdf5_file_name = None):
        
        def create_HDF5(hdf5_file_name):
            hdf5 = h5py.File(f'{self.project_directory}\\{hdf5_file_name}', 'a')
            print(f"File '{hdf5_file_name}' created")
            hdf5.close()

        for fname in os.listdir(self.project_directory):
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


    def create_new_run_hdf5(self,run_name = None):
        with h5py.File(f'{self.project_directory}\\{self.hdf5_file_name}', 'a') as hdf5:
            number_of_runs = len(list(hdf5.keys()))
            if not run_name:
                # Find next run number
                
                #run_numbers = [int(run.split('_')[1]) for run in existing_runs]
                #highest_num = max(run_numbers, default= 0) #TODO wenn unterschieldiche namen verwendet werden, wie nummer vergeben?

                self.run_name = f'Run_{number_of_runs + 1}' 
            else:
                self.run_name = f'Run_{number_of_runs + 1}_' + run_name 
            
            hdf5.create_group(self.run_name)
            hdf5.create_group(self.run_name +"/time_series")
            

    def create_new_run_folder(self):
        pass
    def delete_run(self):
        pass
    def copy_models(self, model_directory):
        pass
    def save_datasheets(self, datasheets_directory):
        pass
    def save_fmu_pid(self):
        pass
    def copy_code(self):
        pass
    def save_PID_code(self):
        pass
    def save_results_in_hdf5(self):
        pass
    def save_plots(self, plots):
        pass
    def save_PID_plots():
        pass

    def pid_generator_default(self, type):
        now = datetime.now()
        date = now.strftime('%y%m%d')
        signature_number = now.strftime('%H%M%S')
        if type == "hdf5":
            return f'{type}_{date}_{signature_number}'

