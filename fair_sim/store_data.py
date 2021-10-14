import h5py

def store_data(hdf5_path, data, data_name, folder, attributes: dict = None):

    with h5py.File(hdf5_path, "a") as hdf5:
        folder = hdf5[folder]
        dset = folder.create_dataset(data_name, data=data)
        if attributes:
            for name, attr in attributes.items():
                dset.attrs[name] = attr