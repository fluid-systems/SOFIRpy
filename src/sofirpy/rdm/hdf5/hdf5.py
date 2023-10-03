"""This module allows to easily store and read data from a hdf5 file."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, Union

import h5py
from typing_extensions import Self

from sofirpy import utils


class HDF5:
    """Object representing a HDF5 file."""

    def __init__(self, hdf5_path: Union[Path, str]) -> None:
        """Initialize the HDF5 object.

        Args:
            hdf5_path (Union[Path, str]): Path to a hdf5 file. If it doesn't
                exists it will be created.
        """
        self.hdf5_path = hdf5_path  # type: ignore[assignment]

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
        _hdf5_path = utils.convert_str_to_path(hdf5_path, "hdf5_path")

        hdf_suffixes = [".hdf", ".h4", ".hdf4", ".he2", ".h5", ".hdf5", ".he5"]

        if _hdf5_path.suffix not in hdf_suffixes:
            raise ValueError(
                "Invalid path name, expected one of the following file extensions: "
                f"{', '.join(hdf_suffixes)}"
            )
        if not _hdf5_path.exists():
            # create_new = utils.get_user_input_for_creating_path(_hdf5_path)
            # if not create_new:
            #     raise FileNotFoundError(f"{_hdf5_path} doesn't exist.")
            _hdf5_path.touch()
            logging.info(f"hdf5 file at {_hdf5_path} created.")

        self._hdf5_path = _hdf5_path

    def create_group(
        self, group_path: str, attributes: Optional[dict[str, Any]] = None
    ) -> None:
        """Creates a group in the hdf5 file.

        Args:
            group_path (str): The name of the group. Subgroups can be
                created by separating the group names with '/'. Example:

                >>> # create a group at the top level with the name "group1"
                >>> group_path = "group1"
                >>> # create a group with the name "subgroup1" in "group1"
                >>> group_path = "group1/subgroup1"

                The parent groups does not need to exist to create a subgroup.
                They will be created automatically. Example:

                >>> group_path = "group2/subgroup1/subsubgroup1"

        Raises:
            ValueError: If the group already exists.
        """
        with h5py.File(str(self.hdf5_path), "a") as hdf5:
            if group_path in hdf5:
                raise ValueError(f"Group '{group_path}' already exists in hdf5.")
            group = hdf5.create_group(group_path)
            if attributes is not None:
                for name, attr in attributes.items():
                    group.attrs[name] = attr

    def store_data(
        self,
        data: Any,
        data_name: str,
        group_path: Optional[str] = None,
        attributes: Optional[dict[str, Any]] = None,
    ) -> None:
        """Stores data in a hdf5 group. If the group doesn't exist it will be created.

        Args:
            data (Any): Data that should be stored.
            data_name (str): Name of the data.
            group_path (Optional[str], optional): Path to the hdf5 group.
            attributes (Optional[dict[str, Any]], optional): Data attributes dictionary
                with attribute names as keys and the attributes as values.
                Defaults to None.

        Raises:
            ValueError: If data path already exists.
        """
        with h5py.File(str(self.hdf5_path), "a") as hdf5:
            if (
                not group_path
            ):  # if group path is empty, the data will be stored at the top level
                group = hdf5
                data_path = data_name
            else:
                if group_path not in hdf5:
                    group = hdf5.create_group(group_path)
                else:
                    group = hdf5[group_path]
                data_path = f"{group_path}/{data_name}"
            if data_path in hdf5:
                overwrite = utils.get_user_input_for_overwriting(
                    data_path, "hdf5 dataset at"
                )
                if not overwrite:
                    raise ValueError(
                        "Unable to create dataset, "
                        f"dataset at {data_path} already exists."
                    )
                del hdf5[data_path]
            dset = group.create_dataset(data_name, data=data)
            if attributes:
                for name, attr in attributes.items():
                    dset.attrs[name] = attr

    def append_attributes(
        self, attributes: dict[str, Any], path: Optional[str] = None
    ) -> None:
        """Append attributes to a hdf5 Dataset or Group.

        Args:
            attributes (dict[str, Any]): Attributes dictionary with attribute
                names as keys and the attributes as values
            path (Optional[str], optional): hdf5 path to the dataset or group.
        """
        with h5py.File(str(self.hdf5_path), "a") as hdf5:
            hdf5_object: Union[h5py.Group, h5py.Dataset] = hdf5[path] if path else hdf5
            for name, attr in attributes.items():
                hdf5_object.attrs[name] = attr

    def delete_attribute(self, attribute_name: str, path: Optional[str] = None) -> None:
        """Deletes a attribute of a hdf5 Dataset or Group.

        Args:
            path (Optional[str], optional): hdf5 path to the dataset or group.
            attribute_name (str): Name of the attribute.

        Raises:
            KeyError: If the attribute does not exist.
        """
        with h5py.File(str(self.hdf5_path), "a") as hdf5:
            hdf5_object: Union[h5py.Group, h5py.Dataset] = hdf5[path] if path else hdf5
            if attribute_name not in hdf5_object.attrs.keys():
                raise KeyError(
                    f"Attribute with name '{attribute_name}' "
                    f"is not a attribute at '{path}'."
                )
            del hdf5_object.attrs[attribute_name]

    def read_attributes(self, path: Optional[str] = None) -> dict[str, Any]:
        """Reads the attributes of a dataset or group.

        Args:
            path (Optional[str]): Path to a hdf5 group or dataset. If None or empty
                string the attributes of the root will be returned.

        Returns:
            dict[str, Any]: Attributes of the given hdf5 group or dataset.
        """
        with h5py.File(str(self.hdf5_path), "a") as hdf5:
            hdf5_object: Union[h5py.Group, h5py.Dataset] = hdf5[path] if path else hdf5
            return dict(hdf5_object.attrs)

    def read_data(
        self,
        data_name: str,
        group_path: Optional[str] = None,
        get_attributes: bool = False,
    ) -> Union[Any, tuple[Any, dict[str, Any]]]:
        """Reads the data of at a given data path.

        Args:
            data_name (str): Name of the data.
            group_path (Optional[str], optional): Path to the hdf5 group.
            get_attributes (bool, optional): If True attributes will
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

            if not isinstance(dataset, h5py.Dataset):
                raise ValueError(f"'{data_path}' does not lead to a Dataset.")

            data = dataset[()]

            if get_attributes:
                attr = dict(dataset.attrs)
                return data, attr

        return data

    def delete_group(self, group_path: str) -> None:
        """Deletes hdf5 group.

        Args:
            group_path (str): Path to the hdf5 group.

        Raises:
            KeyError: If the hdf5 path doesn't exists.
            ValueError: If the group_path does not lead to hdf5 Group.
        """
        with h5py.File(str(self.hdf5_path), "a") as hdf5:
            group: h5py.Group = hdf5[group_path] if group_path else hdf5
            if not isinstance(group, h5py.Group):
                raise ValueError(f"'{group_path}' does not lead to a hdf5 Group.")
            del hdf5[group_path]

    def delete_data(self, data_name: str, group_path: Optional[str] = None) -> None:
        """Deletes a hdf5 Dataset.

        Args:
            group_path (Optional[str], optional): Path to the hdf5 group the data is in.
            data_name (str): Name of the data.

        Raises:
            KeyError: If the hdf5 path to the data doesn't exists.
            ValueError: If the hdf5 path to the data does not lead to hdf5
                Dataset.
        """
        with h5py.File(str(self.hdf5_path), "a") as hdf5:
            if group_path:
                data_path = f"{group_path}/{data_name}"
            else:
                data_path = data_name
            data_object: h5py.Dataset = hdf5[data_path]
            if not isinstance(data_object, h5py.Dataset):
                raise ValueError(f"'{data_path}' does not lead to a dataset.")
            del hdf5[data_path]

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
            group: h5py.Dataset = hdf5[group_path] if group_path else hdf5
            if not isinstance(group, h5py.Group):
                raise ValueError(f"'{group_path}' does not lead to a hdf5 Group.")
            group.visititems(append_dataset)

        return datasets

    def read_hdf5_structure(
        self, group_path: Optional[str] = None
    ) -> Optional[dict[str, Any]]:
        """Reads the structure of a hdf5 group.

        The file structure is represented by a nested dictionary. If group_path
        is not given the structure of the whole hdf5 will be returned.

        Args:
            group_path (Optional[str], optional): Path to the hdf5 group which
                file structure should be returned. Defaults to None.

        Returns:
            Optional[dict[str, Any]]: Returns a dictionary with the
            structure corresponding to the structure of the hdf5 group.
        """
        file_structure: dict[str, Any] = {}

        def append_name(
            name: str, hdf5_object: Union[h5py.Group, h5py.Dataset]
        ) -> None:
            self._place(name, file_structure, hdf5_object, mode="short")

        with h5py.File(str(self.hdf5_path), "a") as hdf5:
            if group_path:
                group = hdf5.get(group_path)
                if not isinstance(group, h5py.Group):
                    return None
            else:
                group = hdf5

            group.visititems(append_name)

            return file_structure

    def __contains__(self, path: str) -> bool:
        """Check if a given group or dataset exists in the hdf5.

        Args:
            path (str): Path to a group or dataset.

        Returns:
            bool: True if the path exists else False.
        """
        with h5py.File(str(self.hdf5_path), "a") as hdf5:
            if hdf5.get(path) is None:
                return False
        return True

    def _get_group_or_dataset_names(
        self,
        group_path: Optional[str],
        obj: Union[h5py.Group, h5py.Dataset],
        filter_func: Optional[Callable[[str], bool]] = None,
    ) -> list[str]:
        with h5py.File(str(self.hdf5_path), "a") as hdf5:
            group: h5py.Group = hdf5[group_path] if group_path else hdf5
            if not isinstance(group, h5py.Group):
                raise ValueError(f"'{group_path}' does not lead to a hdf5 Group.")
            if filter_func is None:
                return [name for name in group.keys() if isinstance(group[name], obj)]
            return [
                name
                for name in group.keys()
                if isinstance(group[name], obj) and filter_func(group[name])
            ]

    def get_group_names(
        self,
        group_path: Optional[str] = None,
        filter_func: Optional[Callable[[str], bool]] = None,
    ) -> list[str]:
        """Get all group names inside a group:

        Args:
            group_path (Optional[str], optional): Path to a hdf5 group.
                Defaults to None.

        Returns:
            list[str]: List group names inside the given hdf5 group.
        """
        return self._get_group_or_dataset_names(group_path, h5py.Group, filter_func)

    def get_dataset_names(
        self,
        group_path: Optional[str] = None,
        filter_func: Optional[Callable[[str], bool]] = None,
    ) -> list[str]:
        """Get all dataset names inside a group:

        Args:
            group_path (Optional[str], optional): Path to a hdf5 group.
                Defaults to None.

        Returns:
            list[str]: List dataset names inside the given hdf5 group.
        """
        return self._get_group_or_dataset_names(group_path, h5py.Dataset, filter_func)

    def _place(
        self,
        name: str,
        _dict: dict[str, Any],
        hdf5_object: Union[h5py.Group, h5py.Dataset],
        mode: Optional[str] = None,
    ) -> dict[str, Any]:
        """Function that calls itself recursively to achieve the following.
        If the path to a dataset is "group1/subgroup1/data" it will convert this path
        into a structured dictionary --> {"group1": {"subgroup1": {"data": <data>}}}.
        If mode is set to "full", the whole dataset is stored at <data>, if it
        is set to "short" only a description of the data is stored.
        """
        if "/" in name:
            split_name = name.split("/", 1)
            base_name, ext_name = split_name
            _dict[base_name]["content"] = self._place(
                ext_name, _dict[base_name]["content"], hdf5_object, mode
            )
        else:
            if name not in _dict:
                value: Union[None, str, dict[str, Any]] = {}
                if isinstance(hdf5_object, h5py.Group):
                    _dict[name] = {
                        "type": "group",
                        "attributes": dict(hdf5_object.attrs),
                        "content": {},
                    }
                else:
                    if mode == "full":
                        value = hdf5_object[()]
                    elif mode == "short":
                        value = str(hdf5_object)
                    else:
                        value = None
                    _dict[name] = {
                        "type": "dataset",
                        "attributes": dict(hdf5_object.attrs),
                        "content": value,
                    }
        return _dict


@dataclass
class HDF5Object:
    name: str
    parent: Group | None = field(repr=False, default_factory=lambda: None)
    attribute: Attribute | None = None

    @property
    def path(self) -> str:
        if self.parent is None:
            return self.name
        return f"{self.directory}/{self.name}"

    @property
    def directory(self) -> str:
        if self.parent is None:
            return ""
        return self.parent.path

    def _attribute_to_hdf5(self, hdf5: HDF5) -> None:
        if self.attribute is None:
            return
        self.attribute.to_hdf5(hdf5)

    def append_attribute(self, attribute: Attribute) -> Self:
        if attribute.parent is None:
            attribute.parent = self
        self.attribute = attribute
        return self


@dataclass
class Attribute:
    parent: HDF5Object | None = field(repr=False, default_factory=lambda: None)
    attributes: dict[str, Any] | None = None

    @property
    def path(self) -> str:
        if self.parent is None:
            return ""
        return self.parent.path

    @classmethod
    def from_hdf5(cls, hdf5: HDF5, parent: HDF5Object) -> Self | None:
        attributes = hdf5.read_attributes(parent.path)
        if not attributes:
            return None
        return cls(parent, attributes)

    def to_hdf5(self, hdf5: HDF5) -> None:
        hdf5.append_attributes(self.attributes or {}, self.path)


@dataclass
class Dataset(HDF5Object):
    data: Any = None

    @classmethod
    def from_hdf5(
        cls, hdf5: HDF5, name: str, parent: Group, read_data: bool = True
    ) -> Self:
        data = None
        if read_data:
            data = hdf5.read_data(name, parent.path)
        self = cls(name=name, parent=parent, data=data)
        self.attribute = Attribute.from_hdf5(hdf5, self)
        return self

    def read_data(self, hdf5: HDF5) -> None:
        self.data = hdf5.read_data(self.name, self.directory)

    def to_hdf5(self, hdf5: HDF5, overwrite: bool = False) -> None:
        if self.path in hdf5 and not overwrite:
            return
        hdf5.store_data(self.data, self.name, self.directory)
        self._attribute_to_hdf5(hdf5)

    def to_dict(self, read_data: bool = False) -> dict[str, Any]:
        return {
            "attributes": self.attribute.attributes if self.attribute else {},
            "data": self.data if read_data else None,
        }

    def delete(self, hdf5: HDF5) -> None:
        hdf5.delete_data(self.name, self.directory)


@dataclass
class Group(HDF5Object):
    groups: Groups = field(default_factory=lambda: Groups())
    datasets: Datasets = field(default_factory=lambda: Datasets())

    @classmethod
    def from_hdf5(
        cls, hdf5: HDF5, name: str, parent: Group | None = None, read_data: bool = True
    ) -> Self:
        self = cls(name=name, parent=parent)
        for group_name in hdf5.get_group_names(self.path):
            self.groups._groups[group_name] = Group.from_hdf5(
                hdf5, group_name, self, read_data
            )
        for dataset_name in hdf5.get_dataset_names(self.path):
            self.datasets._datasets[dataset_name] = Dataset.from_hdf5(
                hdf5, dataset_name, self, read_data
            )
        self.attribute = Attribute.from_hdf5(hdf5, self) if read_data else None
        return self

    def to_hdf5(self, hdf5: HDF5, overwrite: bool = False) -> None:
        if not self.path in hdf5:
            hdf5.create_group(self.path)
        self._attribute_to_hdf5(hdf5)
        self._groups_to_hdf5(hdf5)
        self._datasets_to_hdf5(hdf5)

    def _groups_to_hdf5(self, hdf5: HDF5) -> None:
        if self.groups is None:
            return
        for group in self.groups._groups.values():
            group.to_hdf5(hdf5)

    def _datasets_to_hdf5(self, hdf5: HDF5) -> None:
        if self.datasets is None:
            return
        for dataset in self.datasets._datasets.values():
            dataset.to_hdf5(hdf5)

    def append_hdf5_object(self, hdf5_object: HDF5Object) -> None:
        if isinstance(hdf5_object, Dataset):
            self.append_dataset(hdf5_object)
        if isinstance(hdf5_object, Group):
            self.append_group(hdf5_object)

    def append_group(self, group: Group) -> Self:
        if group.parent is None:
            group.parent = self
        self.groups._groups[group.name] = group
        return self

    def append_dataset(self, dataset: Dataset) -> Self:
        if dataset.parent is None:
            dataset.parent = self
        self.datasets._datasets[dataset.name] = dataset
        return self

    def insert_group(self, group: Group, path: str) -> None:
        parent_group = self.get_group(path)
        parent_group.append_group(group)

    def get_group(self, path: str) -> Group:
        elements = path.split("/")
        group = self
        for name in elements:
            group = group.groups._groups[name]
        return group

    def get_dataset(self, path: str) -> Dataset:
        elements = path.split("/")
        group = self
        for name in elements[:-1]:
            group = group.groups._groups[name]
        return group.datasets._datasets[elements[-1]]

    def to_dict(self, read_data: bool = False) -> dict[str, Any]:
        group_structure: dict[str, Any] = {
            "attributes": self.attribute.attributes if self.attribute else {},
            "datasets": {},
            "groups": {},
        }
        for dataset_name, dataset in self.datasets._datasets.items():
            group_structure["datasets"][dataset_name] = dataset.to_dict(read_data)
        for group_name, group in self.groups._groups.items():
            group_structure["groups"][group_name] = group.to_dict(read_data)
        return group_structure

    def delete(self, hdf5: HDF5) -> None:
        hdf5.delete_group(self.path)


@dataclass
class Groups:
    _groups: dict[str, Group] = field(default_factory=dict)

    def __getattr__(self, __name: str) -> Any:
        if __name in self._groups:
            return self._groups[__name]
        raise AttributeError(f"No group with name '{__name}'")

    def list(self) -> list[str]:
        return list(self._groups.keys())


@dataclass
class Datasets:
    _datasets: dict[str, Dataset] = field(default_factory=dict)

    def __getattr__(self, __name: str) -> Any:
        if __name in self._datasets:
            return self._datasets[__name]
        raise AttributeError(f"No dataset with name '{__name}'")

    def list(self) -> list[str]:
        return list(self._datasets.keys())
