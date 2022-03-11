"""This module allows to easily store and read data from a hdf5 file."""

from pathlib import Path
from typing import Any, Optional, Union
import h5py
from fair_sim import utils


class HDF5:
    """Object representing a HDF5."""

    def __init__(self, hdf5_path: Union[Path, str]) -> None:
        """Initialize the HDF5 object.

        Args:
            hdf5_path (Union[Path, str]): Path to a hdf5 file. If it doesn't
                exists it will be created.
        """
        self.hdf5_path = hdf5_path

    @property
    def hdf5_path(self) -> Path:
        """Path to a hdf5 file.

        Returns:
            Path: Path to a hdf5 file.
        """
        return self._hdf5_path

    @hdf5_path.setter
    def hdf5_path(self, hdf5_path: Union[Path, str]) -> None:
        """Set the path to a hdf5 file. If the path doesn't exist, the file is created.

        Args:
            hdf5_path (Union[Path, str]): Path to a hdf5 file.

        Raises:
            TypeError: hdf5_path type was not 'Path'
            ValueError: suffix of hdf5_path was invalid
        """
        if not isinstance(hdf5_path, (Path, str)):
            raise TypeError(f"'hdf5_path' is {type(hdf5_path)}; expected Path")
        if isinstance(hdf5_path, str):
            hdf5_path = Path(hdf5_path)

        hdf_suffixes = [".hdf", ".h4", ".hdf4", ".he2", ".h5", ".hdf5", ".he5"]

        if hdf5_path.suffix not in hdf_suffixes:
            raise ValueError(
                f'Invalid path name, expected one of the following file extensions: {", ".join(hdf_suffixes)}'
            )
        if not hdf5_path.exists():
            hdf5_path.touch()
            print(f"hdf5 file at {str(hdf5_path)} created.")

        self._hdf5_path = hdf5_path

    def create_group(self, group_path: str) -> None:
        """Creates a group in the hdf5 file.

        Args:
            group_path (str): The name of the group. Subgroups can be
                created by seperating the group names with '/'. Example:

                >>> # create a group at the top level with the name "group1"
                ... group_path = "group1"
                ... # create a group with the name "subgroup1" in "group1"
                ... group_path = "group1/subgroup1"

                The parant groups does not need to exist to create a subgroup.
                They will be created automatically. Example:

                >>> group_path = "group2/subgroup1/subsubgroup1"
        """
        with h5py.File(str(self.hdf5_path), "a") as hdf5:
            if group_path in hdf5:
                print(f"Group {group_path} already exists in hdf5.")
                return
            hdf5.create_group(group_path)

    def store_data(
        self,
        data_name: str,
        data: Any,
        group_path: str,
        attributes: Optional[dict] = None,
    ) -> None:
        """Stores data in a hdf5 group. If the group doesn't exist it will be created.

        Args:
            data_name (str): Name of the data.
            data (Any): Data that should be stored.
            group_path (str): Path to the hdf5 group.
            attributes (Optional[dict], optional): Data attributes dictionary
                with attribute names as keys and the attributes as values.
                Defaults to None.

        Raises:
            ValueError: If data path already exists.
        """
        with h5py.File(str(self.hdf5_path), "a") as hdf5:
            if group_path:
                if group_path not in hdf5:
                    group = hdf5.create_group(group_path)
                else:
                    group = hdf5[group_path]
                data_path = f"{group_path}/{data_name}"
            else:  # if group path is empty, the data will be stored in the top level
                group = hdf5
                data_path = data_name
            if data_path in hdf5:
                overwrite = utils._get_user_input(data_path, "hdf5 dataset at")
                if not overwrite:
                    raise ValueError(
                        f"Unable to create dataset, dataset at {data_path} already exists)"
                    )
                del hdf5[data_path]
            dset = group.create_dataset(data_name, data=data)
            if attributes:
                for name, attr in attributes.items():
                    dset.attrs[name] = attr

    def append_attributes(self, path: str, attributes: dict[str, Any]) -> None:
        """Append attributes to a hdf5 Dataset or a Group.

        Args:
            path (str): hdf5 path to the dataset or group.
            attributes (dict[str, Any]): Attributes dictionary with attribute
                names as keys and the attributes as values
        """
        with h5py.File(str(self.hdf5_path), "a") as hdf5:
            dataset = hdf5[path]
            for name, attr in attributes.items():
                dataset.attrs[name] = attr

    def read_data(
        self, data_name: str, group_path: str, get_attributes: Optional[bool] = False
    ) -> Union[Any, tuple[Any, dict[str, Any]]]:
        """Reads the data of at a given data path.

        Args:
            data_name (str): Name of the data.
            group_path (str): Path to the hdf5 group.
            get_attributes (Optional[bool], optional): If True attributes will
                be returned as well. Defaults to False.

        Raises:
            ValueError: If data path does not lead to a hdf5 Dataset.

        Returns:
            Union[Any, tuple[Any, dict[str, Any]]]: Data and/or attributes of
            the Dataset.
        """
        with h5py.File(str(self.hdf5_path), "a") as hdf5:
            if group_path:
                data_path = f"{group_path}/{data_name}"
            else:
                data_path = data_name
            dataset = hdf5.get(data_path)

            if isinstance(dataset, h5py.Dataset):
                data = dataset[()]
            else:
                raise ValueError(f"'{data_path}' does not lead to a Dataset.")

            if get_attributes:
                attr = dict(dataset.attrs)
                return data, attr

        return data

    def read_entire_group_data(
        self, group_path: Optional[str] = None
    ) -> dict[str, Any]:
        """Reads all data inside a hdf5 group.

        The data will be returned in a nested dictionary representing the file
        structure. If no path to a group is given all the data in the hdf5 will
        returned.

        Args:
            group_path (Optional[str], optional): Path to a hdf5 group.
                Defaults to None.

        Raises:
            ValueError: If the group_path does not lead to a hdf5 group.

        Returns:
            dict[str, Any]: Dictionary with the data of the given group.
        """
        datasets: dict[str, Any] = {}

        def append_dataset(
            name: str, hdf5_object: Union[h5py.Group, h5py.Dataset]
        ) -> None:
            self._place(name, datasets, hdf5_object, mode="full")

        with h5py.File(str(self.hdf5_path), "a") as hdf5:
            if group_path is None:
                group = hdf5
            else:
                group = hdf5.get(group_path)
            if not isinstance(group, h5py.Group):
                raise ValueError(f"'{group_path}' does not lead to a hdf5 Group.")
            group.visititems(append_dataset)

        return datasets

    def delete_group(self, group_path: str) -> None:
        """Deletes hdf5 group.

        Args:
            group_path (str): Path to the hdf5 group.

        Raises:
            KeyError: If the hdf5 path doesn't exists.
            ValueError: If the group_path does not lead to hdf5 Group.
        """
        with h5py.File(str(self.hdf5_path), "a") as hdf5:
            group = hdf5.get(group_path)
            if not group:
                raise KeyError(f"'{group_path}' does not exist in hdf5.")
            if not isinstance(group, h5py.Group):
                raise ValueError(f"'{group_path}' does not lead to a hdf5 Group.")
            del hdf5[group_path]

    def delete_data(self, group_path: str, data_name: str) -> None:
        """Deletes a hdf5 Dataset.

        Args:
            group_path (str): Path to the hdf5 group the data is in.
            data_name (str): Name of the data.

        Raises:
            KeyError: If the hdf5 path to the data doesn't exists.
            ValueError: If the hdf5 path to the data does not lead to hdf5
                Dataset.
        """
        with h5py.File(str(self.hdf5_path), "a") as hdf5:
            path = group_path + "/" + data_name
            if not hdf5.get(path):
                raise KeyError(f"'{path}' does not exist in hdf5.")
            if not isinstance(hdf5.get(path), h5py.Dataset):
                raise ValueError(f"'{path}' does not lead to a dataset.")
            del hdf5[path]

    def get_hdf5_structure(
        self, group_path: Optional[str] = None
    ) -> Union[None, dict[str, Any]]:
        """Reads the structure of a hdf5 group.

        The file structure is represented by a nested dictionary. If group_path
        is not given the structure of the wholen hdf5 will be returned.

        Args:
            group_path (Optional[str], optional): Path to the hdf5 group which
                file structure should be returned. Defaults to None.

        Returns:
            Union[None, dict[str, Any]]: Returns a dictionary with the
            structure corresponding to the structure of the hdf5 group.
        """
        file_structure: dict[str, Any] = {}

        def append_name(name: str, hdf5_object: Union[h5py.Group, h5py.Dataset]):
            self._place(name, file_structure, hdf5_object, mode="short")

        with h5py.File(str(self.hdf5_path), "a") as hdf5:
            if group_path:
                group = hdf5.get(group_path)
                if not isinstance(group, h5py.Group):
                    return
            else:
                group = hdf5

            group.visititems(append_name)

            return file_structure

    def _place(
        self,
        name: str,
        _dict: dict,
        hdf5_object: Union[h5py.Group, h5py.Dataset],
        mode: Optional[str] = None,
    ) -> dict[str, Any]:
        """Recursive function to achieve the following. If the path to a
        dataset is "group1/subgroup1/data" it will convert this path into a
        structured dictionary --> {"group1": {"subgroup1": {"data": <data>}}}.
        If mode is set to "full", the whole dataset is stored at <data>, if it
        is set to "short" only a description of the data is stored.
        """
        # TODO test '/' in name
        if "/" in name:
            split_name = name.split("/", 1)
            base_name = split_name[0]
            ext_name = split_name[1]
            _dict[base_name] = self._place(
                ext_name, _dict[base_name], hdf5_object, mode
            )
        else:
            if name not in _dict:
                value = {}
                if isinstance(hdf5_object, h5py.Dataset):
                    if mode == "full":
                        value = hdf5_object[()]
                    elif mode == "short":
                        value = str(hdf5_object)
                    else:
                        value = None
                _dict[name] = value
        return _dict
