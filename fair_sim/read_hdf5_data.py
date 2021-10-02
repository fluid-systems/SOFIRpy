import h5py
import pandas as pd
import numpy

def read_data(hdf5_path: str, data_name: str, get_attribute: bool=False):

    with h5py.File(hdf5_path, "a") as hdf5:
        _data = hdf5.get(data_name)
        
        if isinstance(_data, h5py.Dataset):
            data = _data[()]

        elif isinstance(_data, h5py.Group):
            data = list(_data.keys())

        else:
            data = None

        if get_attribute:
            attr = dict(_data.attrs)
            return data, attr
    return data

def read_entire_group_content(hdf5_path: str, group_name: str, merge_into_dataframe: bool = False, merge_on: str = "time"):

    with h5py.File(hdf5_path, "a") as hdf5:
        group = hdf5.get(group_name)
        if not isinstance(group, h5py.Group):
            raise TypeError(f"The path {group_name} does not lead to a hdf5 Group.")
        elements = list(group.keys())
        data = {}
        for elm in elements:
            data_set = hdf5.get(group_name + "/" + elm)
            if isinstance(data_set, h5py.Dataset):
                _data = data_set[()]
                data[elm] = _data
    
    if not merge_into_dataframe:
        return data

    else:
        for i, dt in enumerate(list(data.values())):
            if isinstance(dt, numpy.ndarray):
                data_frame = pd.DataFrame(dt)
                start = i+1
                break
      
        for dt in list(data.values())[start:]:
            if isinstance(dt,numpy.ndarray):
                data_set = pd.DataFrame(dt[()]) 
                data_frame = pd.merge(data_frame, data_set, on = merge_on)
    return data_frame
