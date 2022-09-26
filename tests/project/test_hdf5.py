import sys
from pathlib import Path

import h5py
import numpy as np
import pytest

from sofirpy import HDF5

sys.path.append(str(Path(__file__).parent))

from project_testing_utils import hdf5_clean_up


@pytest.fixture
def hdf5() -> HDF5:
    test_hdf5_path = Path(__file__).parent / "test_hdf5.hdf5"
    return HDF5(test_hdf5_path)


@pytest.mark.parametrize(
    "file_suffix", [".hdf", ".h4", ".hdf4", ".he2", ".h5", ".hdf5", ".he5"]
)
def test_create_new_hdf5(file_suffix: str) -> None:
    try:
        temp_path = Path(__file__).parent / f"test_new_hdf5.{file_suffix}"
        HDF5(temp_path)
        assert temp_path.exists() == True
    finally:
        temp_path.unlink()


@pytest.mark.parametrize("file_suffix", [".txt", ".hdf6", ".h7"])
def test_create_new_hdf5_exception(file_suffix: str) -> None:
    temp_path = Path(__file__).parent / f"test_new_hdf5.{file_suffix}"
    with pytest.raises(ValueError):
        HDF5(temp_path)


def test_init_of_already_existing_hdf5(hdf5: HDF5) -> None:
    assert hdf5.hdf5_path.exists() == True


@hdf5_clean_up
def test_create_group(hdf5: HDF5) -> None:

    groups = ["group1", "group1/subgroup1", "group2/subgroup1"]

    for group in groups:
        hdf5.create_group(group)

    for group in groups:
        with h5py.File(str(hdf5.hdf5_path), "a") as hdf5_file:
            assert group in hdf5_file


def test_create_group_exception(hdf5: HDF5) -> None:

    groups = [
        "test_create_group_exception/group1",
        "test_create_group_exception/group2/subgroup1",
    ]

    for group in groups:
        with pytest.raises(ValueError):
            hdf5.create_group(group)


@hdf5_clean_up
def test_delete_group(hdf5: HDF5) -> None:

    groups = [
        "test_delete_group/group1",
        "test_delete_group/group2/subgroup1",
        "test_delete_group/group2",
    ]

    for group in groups:
        hdf5.delete_group(group)

        with h5py.File(str(hdf5.hdf5_path), "a") as hdf5_file:
            assert group not in hdf5_file


def test_read_attributes(hdf5: HDF5) -> None:

    attr = {"attr1": 1, "attr4": "foo"}
    assert attr == hdf5.read_attributes("test_read_attributes")
    assert attr == hdf5.read_attributes("test_read_attributes/dataset1")


@hdf5_clean_up
def test_delete_attribute(hdf5: HDF5) -> None:

    hdf5.delete_attribute("test_delete_attribute", attribute_name="attr1")
    assert not hdf5.read_attributes("test_delete_attribute")


def test_delete_attribute_exception(hdf5: HDF5) -> None:

    with pytest.raises(KeyError):
        hdf5.delete_attribute("test_delete_attribute_exception", "i_do_not_exist")


@hdf5_clean_up
def test_append_attributes(hdf5: HDF5) -> None:

    attr = {"attr1": 1, "attr4": "foo"}
    hdf5.append_attributes("test_append_attributes", attr)
    assert attr == hdf5.read_attributes("test_append_attributes")


def test_read_data(hdf5: HDF5) -> None:

    data, attr = hdf5.read_data("test_data", "test_read_data", get_attributes=True)
    assert (data == np.zeros((10, 10))).all()
    assert attr == {"test": 1}
    data = hdf5.read_data("test_data", "test_read_data")
    assert (data == np.zeros((10, 10))).all()


def test_read_data_exception(hdf5: HDF5) -> None:

    with pytest.raises(ValueError):
        hdf5.read_data("subgroup1", "test_read_data")


@hdf5_clean_up
def test_read_entire_group_data(hdf5: HDF5) -> None:

    assert hdf5.read_entire_group_data("test_delete_group") == {
        "group1": {},
        "group2": {"subgroup1": {}},
    }


@hdf5_clean_up
def test_read_hdf5_structure(hdf5: HDF5) -> None:
    assert hdf5.read_hdf5_structure("test_read_data") == {
        "subgroup1": {},
        "test_data": '<HDF5 dataset "test_data": shape (10, 10), type "<f8">',
    }


def test_check_path_exists(hdf5: HDF5) -> None:

    assert hdf5.check_path_exists("test_check_path_exists")
    assert hdf5.check_path_exists("test_check_path_exists/test_data")
    assert not hdf5.check_path_exists("test_check_path_exists/non_existing_path")


@hdf5_clean_up
def test_store_data(hdf5: HDF5) -> None:

    data = np.zeros((10, 10))
    attr = {"test": 1}
    # test with already existing group "test_store_data"
    hdf5.store_data("test_data", data, "test_store_data", attributes=attr)
    _data, _attr = hdf5.read_data("test_data", "test_store_data", get_attributes=True)
    assert (_data == data).all()
    assert _attr == attr
    # test with not existing group
    hdf5.store_data("test_data", data, "test_store_data/subgroup1", attributes=attr)
    _data = hdf5.read_data("test_data", "test_store_data/subgroup1")
    assert (_data == data).all()


def test_store_data_with_already_existing_data_set(hdf5: HDF5) -> None:
    pass


@hdf5_clean_up
def test_delete_data(hdf5: HDF5) -> None:

    hdf5.delete_data("test_delete_data", "delete_data")
    assert not hdf5.check_path_exists("test_delete_data/delete_data")


def test_delete_data_exception(hdf5: HDF5) -> None:

    with pytest.raises(KeyError):
        hdf5.delete_data("test_read_data", "non_existing_path")

    with pytest.raises(ValueError):
        hdf5.delete_data(None, "test_delete_data")
