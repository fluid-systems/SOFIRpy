from __future__ import annotations

from pathlib import Path

import pytest

import sofirpy.utils as utils


@pytest.mark.parametrize(
    "str_or_path, expected",
    [("/sofirpy", Path("/sofirpy")), (Path("/sofirpy"), Path("/sofirpy"))],
)
def test_convert_str_to_path_function(str_or_path: str | Path, expected: Path) -> None:
    assert utils.convert_str_to_path(str_or_path, "test_path") == expected


@pytest.mark.parametrize("test_input", [1, None, [1, 2, 3], {"sofirpy": 1}])
def test_convert_str_to_path_error(test_input):
    with pytest.raises(TypeError):
        utils.convert_str_to_path(test_input, "test_input")


def test_delete_file_or_directory(tmp_path: Path) -> None:
    file_path = tmp_path / "test_file.txt"
    file_path.touch()
    utils.delete_file_or_directory(file_path)
    utils.delete_file_or_directory(tmp_path)


def test_delete_file_or_directory_if_directory_does_not_exist(tmp_path: Path) -> None:
    file_path = tmp_path / "test_file.txt"
    utils.delete_file_or_directory(file_path, must_exist=False)
    with pytest.raises(FileNotFoundError):
        utils.delete_file_or_directory(file_path, must_exist=True)
