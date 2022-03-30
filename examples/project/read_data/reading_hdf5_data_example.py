# The hdf5 module makes is easy to browse a hdf5 file by providing 
# methodes to read the content of entire hdf5 groups.
# Start by importing the HDF5 class from fair_sim.

from pathlib import Path
import numpy as np
from sofirpy import HDF5

hdf5_path = Path(__file__).parent / "example.hdf5"

hdf5 = HDF5(hdf5_path)

# to read data we first need to store data inside the hdf5. 
data1 = np.random.randint((4,3))
data1_name = "matrix_random"
data1_group_name = "matrices/random"

hdf5.store_data(data1_name, data1, data1_group_name)

data2 = [
    [15, 8, 1, 24, 17],
    [16, 14, 7, 5, 23],
    [22, 20, 13, 6, 4],
    [3, 21, 19, 12, 10],
    [9, 2, 25, 18, 11],
]
data2_name = "matrix_magic"
data2_group_name = "matrices/magic"

hdf5.store_data(data2_name, data2, data2_group_name)

data3 = 3.14
data3_name = "pi"
data2_group_name = "constants"

hdf5.store_data(data3_name, data3, data2_group_name)

# get the file structure
file_structure = hdf5.read_hdf5_structure()
print(file_structure)

# get the entire hdf5 data content
entire_data = hdf5.read_entire_group_data()
print(entire_data)

# get the entire hdf5 content of the specified group
group_content = hdf5.read_entire_group_data("matrices")
print(group_content)
