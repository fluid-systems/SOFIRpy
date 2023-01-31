from pathlib import Path
from typing import Union

import pytest

import sofirpy.utils as utils


@pytest.mark.parametrize(
    "str_or_path, expected",
    [("/sofirpy", Path("/sofirpy")), (Path("/sofirpy"), Path("/sofirpy"))],
)
def test_convert_str_to_path_function(
    str_or_path: Union[str, Path], expected: Path
) -> None:
    assert utils.convert_str_to_path(str_or_path, "test_path") == expected


@pytest.mark.parametrize("test_input", [1, None, [1, 2, 3], {"sofirpy": 1}])
def test_convert_str_to_path_error(test_input):
    with pytest.raises(TypeError):
        utils.convert_str_to_path(test_input, "test_input")
