from typing import Any
import h5py

def store_data(hdf5_path: str, data: Any, data_name: str, folder_path: str, attributes: dict = None):

    with h5py.File(hdf5_path, "a") as hdf5:
        folder = hdf5[folder_path]
        dset = folder.create_dataset(data_name, data=data)

        if attributes:
            for name, attr in attributes.items():
                dset.attrs[name] = attr

def append_attributes(hdf5_path: str, data_path: str, attributs: dict):

    with h5py.File(hdf5_path, "a") as hdf5:
        dset = hdf5[data_path]
        for name, attr in attributs.items():
            dset.attrs[name] = attr