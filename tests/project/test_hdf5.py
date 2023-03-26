import shutil
import tempfile
from pathlib import Path

import numpy as np
import pytest

from sofirpy import HDF5


@pytest.fixture
def hdf5() -> HDF5:
    test_hdf5_path = Path(__file__).parent / "test_hdf5.hdf5"
    _hdf5 = HDF5(test_hdf5_path)
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield copy_standard_hdf5(_hdf5, "hdf5_testing", Path(tmp_dir))


def copy_standard_hdf5(hdf5: HDF5, test_name: str, dir_path: Path) -> HDF5:
    copy_path = dir_path / f"{test_name}.hdf5"
    shutil.copy(hdf5.hdf5_path, copy_path)
    return HDF5(copy_path)


@pytest.mark.parametrize(
    "file_suffix", [".hdf", ".h4", ".hdf4", ".he2", ".h5", ".hdf5", ".he5"]
)
def test_create_new_hdf5(file_suffix: str) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_path = Path(tmp_dir) / f"test_new_hdf5.{file_suffix}"
        HDF5(temp_path)
        assert temp_path.exists() == True


@pytest.mark.parametrize("file_suffix", [".txt", ".hdf6", ".h7"])
def test_create_new_hdf5_exception(file_suffix: str) -> None:
    temp_path = Path(__file__).parent / f"test_new_hdf5.{file_suffix}"
    with pytest.raises(ValueError):
        HDF5(temp_path)


@pytest.mark.parametrize(
    "path",
    [
        "test_create_group_exception/group1",
        "test_create_group_exception/group2/subgroup1",
    ],
)
def test_contains(hdf5: HDF5, path: str) -> None:
    assert path in hdf5


@pytest.mark.parametrize(
    "group",
    [
        "group1",
        "group1/subgroup1",
        "group2/subgroup1",
    ],
)
def test_create_group(hdf5: HDF5, group: str) -> None:

    hdf5.create_group(group)
    assert group in hdf5


@pytest.mark.parametrize(
    "group",
    [
        "test_create_group_exception/group1",
        "test_create_group_exception/group2/subgroup1",
    ],
)
def test_create_group_exception(hdf5: HDF5, group: str) -> None:

    with pytest.raises(ValueError):
        hdf5.create_group(group)


@pytest.mark.parametrize(
    "group",
    [
        "test_delete_group/group1",
        "test_delete_group/group2/subgroup1",
        "test_delete_group/group2",
    ],
)
def test_delete_group(hdf5: HDF5, group: str) -> None:

    hdf5.delete_group(group)
    assert group not in hdf5


def test_read_attributes(hdf5: HDF5) -> None:

    attr = {"attr1": 1, "attr4": "foo"}
    assert attr == hdf5.read_attributes("test_read_attributes")
    assert attr == hdf5.read_attributes("test_read_attributes/dataset1")


def test_delete_attribute(hdf5: HDF5) -> None:

    hdf5.delete_attribute(attribute_name="attr1", path="test_delete_attribute")
    assert not hdf5.read_attributes("test_delete_attribute")


def test_delete_attribute_exception(hdf5: HDF5) -> None:

    with pytest.raises(KeyError):
        hdf5.delete_attribute("i_do_not_exist", "test_delete_attribute_exception")


def test_append_attributes(hdf5: HDF5) -> None:

    attr = {"attr1": 1, "attr4": "foo"}
    hdf5.append_attributes(attr, "test_append_attributes")
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


def test_read_entire_group_data(hdf5: HDF5) -> None:
    print(hdf5.read_entire_group_data("test_delete_group"))
    assert hdf5.read_entire_group_data("test_delete_group") == {
        "group1": {"type": "group", "attributes": {}, "content": {}},
        "group2": {
            "type": "group",
            "attributes": {},
            "content": {
                "subgroup1": {"type": "group", "attributes": {}, "content": {}}
            },
        },
    }


def test_read_hdf5_structure(hdf5: HDF5) -> None:
    assert hdf5.read_hdf5_structure("test_read_data") == {
        "subgroup1": {"attributes": {}, "content": {}, "type": "group"},
        "test_data": {
            "attributes": {"test": 1},
            "content": '<HDF5 dataset "test_data": shape (10, 10), type "<f8">',
            "type": "dataset",
        },
    }


def test_store_data(hdf5: HDF5) -> None:

    data = np.zeros((10, 10))
    attr = {"test": 1}
    # test with already existing group "test_store_data"
    hdf5.store_data(data, "test_data", "test_store_data", attributes=attr)
    _data, _attr = hdf5.read_data("test_data", "test_store_data", get_attributes=True)
    assert (_data == data).all()
    assert _attr == attr
    # test with not existing group
    hdf5.store_data(data, "test_data", "test_store_data/subgroup1", attributes=attr)
    _data = hdf5.read_data("test_data", "test_store_data/subgroup1")
    assert (_data == data).all()


def test_store_data_with_already_existing_data_set(hdf5: HDF5) -> None:
    pass


def test_delete_data(hdf5: HDF5) -> None:

    hdf5.delete_data("delete_data", "test_delete_data")
    assert "test_delete_data/delete_data" not in hdf5


def test_delete_data_exception(hdf5: HDF5) -> None:

    with pytest.raises(KeyError):
        hdf5.delete_data("test_read_data", "non_existing_path")

    with pytest.raises(ValueError):
        hdf5.delete_data("test_delete_data", None)
