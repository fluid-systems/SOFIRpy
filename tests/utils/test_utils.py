import sys
import os
from typing import Union
import pytest
from pathlib import Path

sys.path.append(os.path.join(os.path.dirname(__file__),'../../'))

import sofirpy.utils as utils


@pytest.mark.parametrize("str_or_path, expected",
[("C:/sofirpy", Path("C:/sofirpy")), 
(Path("C:/sofirpy"), Path("C:/sofirpy"))]) 
def test_convert_str_to_path_function(
    str_or_path: Union[str, Path],
    expected: Path
) -> None:
    assert utils.convert_str_to_path(str_or_path, "test_path") == expected

@pytest.mark.parametrize("test_input", [1, None, [1,2,3], {"sofirpy": 1}])
def test_convert_str_to_path_error(test_input):
    with pytest.raises(TypeError):
        utils.convert_str_to_path(test_input, "test_input")