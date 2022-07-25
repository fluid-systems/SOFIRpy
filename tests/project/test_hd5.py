import shutil
from pathlib import Path
import pytest
import numpy as np
import h5py
from sofirpy import HDF5


@pytest.fixture
def hdf5() -> HDF5:
    test_hdf5_path = Path(__file__).parent / "test_hdf5.hdf5"
    return HDF5(test_hdf5_path)


@pytest.mark.parametrize(
    "file_suffix", [".hdf", ".h4", ".hdf4", ".he2", ".h5", ".hdf5", ".he5"]
)
def test_create_new_hdf5(file_suffix: str) -> None:
    temp_path = Path(__file__).parent / f"test_new_hdf5.{file_suffix}"
    HDF5(temp_path)
    assert temp_path.exists() == True
    temp_path.unlink()


def _copy_standard_hdf5(hdf5: HDF5, test_name: str) -> HDF5:
    copy_path = hdf5.hdf5_path.parent / f"{test_name}.hdf5"
    shutil.copy(hdf5.hdf5_path, copy_path)
    return HDF5(copy_path)


@pytest.mark.parametrize("file_suffix", [".txt", ".hdf6", ".h7"])
def test_create_new_hdf5_exception(file_suffix: str) -> None:
    temp_path = Path(__file__).parent / f"test_new_hdf5.{file_suffix}"
    with pytest.raises(ValueError):
        HDF5(temp_path)


def test_init_of_already_existing_hdf5(hdf5: HDF5) -> None:
    assert hdf5.hdf5_path.exists() == True


def test_create_group(hdf5: HDF5) -> None:

    hdf5 = _copy_standard_hdf5(hdf5, "test_create_group")

    groups = ["group1", "group1/subgroup1", "group2/subgroup1"]

    for group in groups:
        hdf5.create_group(group)

    for group in groups:
        with h5py.File(str(hdf5.hdf5_path), "a") as hdf5_file:
            assert group in hdf5_file

    hdf5.hdf5_path.unlink()


def test_create_group_exception(hdf5: HDF5) -> None:

    groups = [
        "test_create_group_exception/group1",
        "test_create_group_exception/group2/subgroup1",
    ]

    for group in groups:
        with pytest.raises(ValueError):
            hdf5.create_group(group)


def test_delete_group(hdf5: HDF5) -> None:

    hdf5 = _copy_standard_hdf5(hdf5, "test_delete_group")

    groups = [
        "test_delete_group/group1",
        "test_delete_group/group2/subgroup1",
        "test_delete_group/group2",
    ]

    for group in groups:
        hdf5.delete_group(group)

        with h5py.File(str(hdf5.hdf5_path), "a") as hdf5_file:
            assert group not in hdf5_file

    hdf5.hdf5_path.unlink()


def test_read_attributes(hdf5: HDF5) -> None:

    attr = {"attr1": 1, "attr4": "foo"}
    assert attr == hdf5.read_attributes("test_read_attributes")
    assert attr == hdf5.read_attributes("test_read_attributes/dataset1")


def test_delete_attribute(hdf5: HDF5) -> None:

    hdf5 = _copy_standard_hdf5(hdf5, "test_delete_attribute")

    hdf5.delete_attribute("test_delete_attribute", attribute_name="attr1")
    assert not hdf5.read_attributes("test_delete_attribute")
    hdf5.hdf5_path.unlink()


def test_delete_attribute_exception(hdf5: HDF5) -> None:

    with pytest.raises(KeyError):
        hdf5.delete_attribute("test_delete_attribute_exception", "i_do_not_exist")


def test_append_attributes(hdf5: HDF5) -> None:

    hdf5 = _copy_standard_hdf5(hdf5, "test_append_attributes")
    attr = {"attr1": 1, "attr4": "foo"}
    hdf5.append_attributes("test_append_attributes", attr)
    assert attr == hdf5.read_attributes("test_append_attributes")
    hdf5.hdf5_path.unlink()


def test_read_data(hdf5: HDF5) -> None:

    data, attr = hdf5.read_data("test_data", "test_read_data", get_attributes=True)
    assert (data == np.zeros((10, 10))).all()
    assert attr == {"test": 1}
    data = hdf5.read_data("test_data", "test_read_data")
    assert (data == np.zeros((10, 10))).all()


def test_read_data_exception(hdf5: HDF5) -> None:

    with pytest.raises(ValueError):
        hdf5.read_data("subgroup1", "test_read_data")


def test_check_path_exists(hdf5: HDF5) -> None:

    assert hdf5.check_path_exists("test_check_path_exists")
    assert hdf5.check_path_exists("test_check_path_exists/test_data")
    assert not hdf5.check_path_exists("test_check_path_exists/non_existing_path")


def test_store_data(hdf5: HDF5) -> None:

    hdf5 = _copy_standard_hdf5(hdf5, "test_store_data")

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
    hdf5.hdf5_path.unlink()


def test_store_data_with_already_existing_data_set(hdf5: HDF5) -> None:
    pass


def test_delete_data(hdf5: HDF5) -> None:

    hdf5 = _copy_standard_hdf5(hdf5, "test_delete_data")
    hdf5.delete_data("test_delete_data", "delete_data")
    assert not hdf5.check_path_exists("test_delete_data/delete_data")
    hdf5.hdf5_path.unlink()


def test_delete_data_exception(hdf5: HDF5) -> None:

    with pytest.raises(KeyError):
        hdf5.delete_data("test_read_data", "non_existing_path")

    with pytest.raises(ValueError):
        hdf5.delete_data(None, "test_delete_data")
