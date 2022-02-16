#%%
from pathlib import Path
from typing import Optional, Union
from hdf5 import HDF5
from project_dir import ProjectDir

class Project:

    def __init__(self, hdf5_path: Union[Path, str], project_dir_path: Union[Path, str]) -> None:
        
        self.hdf5 = HDF5(hdf5_path)
        self.project_dir = ProjectDir(project_dir_path)

    def create_folder(self, folder_name: str) -> None:

        self.hdf5.create_folder(folder_name)
        try:
            self.project_dir.create_folder(folder_name)
        except Exception as e:
            self.hdf5.delete_folder(folder_name)
            raise e

    def delete_folder(self, folder_name: str) -> None:

        self.hdf5.delete_folder(folder_name)
        self.project_dir.delete_folder(folder_name)

    def store_file(self, source_path: Union[str, Path], folder_name: str, copy: Optional[bool] = True, new_file_name: Optional[Union[str, None]] = None) -> None:

        if copy:
            target_path = self.project_dir.copy_file(source_path, self.project_dir.project_directory / folder_name)
        else:
            target_path = self.project_dir.move_file(source_path, self.project_dir.project_directory / folder_name)
        if new_file_name:
            target_path = self.project_dir.rename_file(target_path, new_file_name)            

        self.hdf5.store_data(target_path.stem, str(target_path), folder_name)

    def __repr__(self) -> str:
        return f"Project with project directory '{str(self.project_dir.project_directory)}' and hdf5 path '{str(self.hdf5.hdf5_path)}'"

if __name__ == "__main__":

    project = Project("C:/Users/Daniele/Desktop/test/hdf5_210901_222842.hdf5", "C:/Users/Daniele/Desktop/test")
    # file = Path(r"C:\Users\Daniele\Desktop\test\simulator_DC_Motor.log") 
    # folder_name = "Run_1/datasheets2"
    # new_file_name = "simlog"
    # project.store_file(file, folder_name,copy=False ,new_file_name= new_file_name)
    #project.create_folder("Run_15/data1/data1")
# %%
