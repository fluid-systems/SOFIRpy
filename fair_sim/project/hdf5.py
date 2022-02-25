from pathlib import Path
import h5py
from typing import Any, Optional, Union
import fair_sim.utils as utils

class HDF5:

    def __init__(self, hdf5_path: Union[Path, str]) -> None:
        
        self.hdf5_path = hdf5_path

    @property
    def hdf5_path(self) -> Path:
        return self._hdf5_path

    @hdf5_path.setter
    def hdf5_path(self, hdf5_path: Union[Path, str]) -> None:

        if not isinstance(hdf5_path, (Path, str)):
            raise TypeError(f"'hdf5_path' is {type(hdf5_path)}; expected Path")
        if isinstance(hdf5_path, str):
            hdf5_path = Path(hdf5_path)
            
        self._hdf5_path = hdf5_path
        
    def create_folder(self, folder_name: str) -> None:

        with h5py.File(str(self.hdf5_path), "a") as hdf5:
            hdf5.create_group(folder_name)

    def store_data(self, data_name: str, data: Any, folder_path: str, attributes: Optional[dict[str, Any]] = None) -> None:

        with h5py.File(str(self.hdf5_path), "a") as hdf5:
            if folder_path not in hdf5:
                folder = hdf5.create_group(folder_path)
            else:
                folder = hdf5[folder_path]
            data_path = f"{folder_path}/{data_name}"
            if data_path in hdf5:
                overwrite = utils._get_user_input(data_path, "hdf5_path")
                if not overwrite:
                    raise ValueError(f"Unable to create dataset, {data_path} already exists)")
                del hdf5[data_path]
            dset = folder.create_dataset(data_name, data=data)
            if attributes:
                for name, attr in attributes.items():
                    dset.attrs[name] = attr

    def append_attributes(self, path: str, attributes: dict[str, Any]) -> None:

        with h5py.File(str(self.hdf5_path), "a") as hdf5:
            dataset = hdf5[path]
            for name, attr in attributes.items():
                dataset.attrs[name] = attr

    def read_data(self, folder_name: str, data_name: str, get_attributes: Optional[bool] = False) -> Union[Any, tuple[Any, dict[str, Any]]]:

        with h5py.File(str(self.hdf5_path), "a") as hdf5:
            data_path = f"{folder_name}/{data_name}"
            dataset = hdf5.get(data_path)
            
            if isinstance(dataset, h5py.Dataset):
                data = dataset[()]
            else:
                print(f"'{data_path}' does not lead to a Dataset.")
                return 

            if get_attributes:
                attr = dict(dataset.attrs)
                return data, attr

        return data

    def read_entire_group_data(self, group_path: Optional[str] = None) -> dict[str, Any]:

        datasets: dict[str, Any] = {}

        def append_dataset(name: str, hdf5_object: Union[h5py.Group, h5py.Dataset]) -> None:
            self._place(name, datasets, hdf5_object, mode= 'full')

        with h5py.File(str(self.hdf5_path), "a") as hdf5:
            if group_path is None:
                group = hdf5
            else:
                group = hdf5.get(group_path)
            if not isinstance(group, h5py.Group):
                raise TypeError(f"'{group_path}' does not lead to a hdf5 Group.")
            group.visititems(append_dataset)

        return datasets
        
    def delete_folder(self, folder_path: str) -> None:

        with h5py.File(str(self.hdf5_path), "a") as hdf5:
            try:
                del hdf5[folder_path]
                print(f"The hdf5 folder '{folder_path}' has been deleted.")
            except KeyError:
                print(f"The hdf5 folder '{folder_path}' doesn't exists.")

    def delete_data(self, folder_path: str, data_name: str) -> None:

        with h5py.File(str(self.hdf5_path), "a") as hdf5:
            path = folder_path + "/" + data_name
            if not hdf5.get(path):
                raise KeyError(f"Data '{data_name}' in '{folder_path}' does not exist in hdf5.")
            if isinstance (hdf5.get(path), h5py.Dataset):
                del hdf5[path]
                print(f"Data '{data_name}' in '{folder_path}' has been deleted.")
            else:
                print(f"'{path}' does not lead to a dataset.")

    def get_hdf5_structure(self, start_path: Optional[str] = None) -> Union[None, dict[str, Any]]:
        
        file_structure: dict[str, Any] = {}

        def append_name(name: str, hdf5_object: Union[h5py.Group, h5py.Dataset]):
            self._place(name, file_structure, hdf5_object, mode = 'short')

        with h5py.File(str(self.hdf5_path), "a") as hdf5:
            if start_path:
                group = hdf5.get(start_path)
                if not isinstance(group, h5py.Group):
                    return
            else:
                group = hdf5

            group.visititems(append_name)

            return file_structure

    def _place(self, name: str, _dict: dict, hdf5_object: Union[h5py.Group, h5py.Dataset], mode: Optional[str] = None) -> dict[str, Any]:
            
            #TODO test '/' in name
            if "/" in name:
                split_name = name.split("/", 1)
                base_name = split_name[0]
                ext_name = split_name[1]
                _dict[base_name] = self._place(ext_name, _dict[base_name], hdf5_object, mode)
            else:
                if name not in _dict:
                    value = {}
                    if isinstance(hdf5_object, h5py.Dataset):
                        if mode == 'full':
                            value = hdf5_object[()]
                        elif mode == 'short':
                            value = str(hdf5_object)
                        else:
                            value = None
                    _dict[name] = value
            return _dict

if __name__ == "__main__":
    
    hdf5 = HDF5(Path(r"C:\Users\Daniele\Desktop\test\hdf5_210901_222843.hdf5"))
    _hdf5 = HDF5(Path(r"C:\Users\Daniele\Desktop\Motor_Control1\hdf5_211218_153013.hdf5"))

    #hdf5.store_data([[1,2,3],[2,3,5]], "daten", "test1")
    import json
    #print(hdf5.get_hdf5_structure())
    #print(hdf5.get_hdf5_structure())
    print(json.dumps(hdf5.get_hdf5_structure("test1")))
    # with h5py.File(str(Path(r"C:\Users\Daniele\Desktop\test\hdf5_210901_222843.hdf5")), "a") as hdf5:
    #     print(hdf5.get("/test1/a/d/e/f"))
    #print(_hdf5.read_entire_group_data_content("Run_1"))
    