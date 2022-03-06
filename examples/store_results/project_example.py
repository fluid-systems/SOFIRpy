from fair_sim import Project
from pathlib import Path

# Initialize a project by giving it the path to a project directory and the
# path to a hdf5. If the given pathts do not exist, they will be created. 

project_dir = Path(__file__).parent
hdf5_name = "example_project"
hdf5_path = Path(project_dir) / f"{hdf5_name}.hdf5" 
project = Project(hdf5_path, project_dir)

# actions can be taken only on the hdf5, only on the project directory and 
# simultaneously on both the hdf5 and the project directory.

# storing data in the hdf5
data =  [   [15, 8,  1,  24, 17],
            [16, 14, 7, 5, 23],
            [22, 20, 13, 6, 4],
            [3 , 21, 19, 12, 10],
            [9 , 2 , 25, 18, 11],
        ]
data_name = "magic"
data_attributes = {"created on": "01.01.01"}

# specify in which folder the matrix should be stored, if the data should be
# stored at the top level, folder_name must be set to None.

folder_name = "magic_matrices"
project.hdf5.store_data(data_name, data, folder_path = folder_name, attributes=data_attributes)

# reading data
data, attr = project.hdf5.read_data(data_name, folder_name, get_attributes=True)

# create a folder in the project directory
folder_name = "magic_matrices"
project.project_dir.create_folder(folder_name)

# create a folder in the project directory and the hdf5 simultaneously
folder_name = "magic_matrices/examples"
project.create_folder(folder_name)
