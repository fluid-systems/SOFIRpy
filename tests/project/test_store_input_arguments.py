import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__),'../../'))
from sofirpy import store_input_arguments


class TestClass:

    @store_input_arguments
    def __init__(self, a, b, c = 1, d = 2) -> None:...

    @store_input_arguments
    def methode1(self) -> None:...

    @store_input_arguments
    def methode2(self, a = 1) -> None:...

    @store_input_arguments
    def methode3(self, a) -> None:...


def test_store_input_arguments() -> None:

    test_class = TestClass(1, b = 5, c = 4)
    test_class.methode1()
    test_class.methode2(a = None)
    test_class.methode3(list())
    test_class.methode3(dict())

    assert test_class.__input_arguments__ == {
        "__init__": {
            "a": 1,
            "b": 5,
            "c": 4,
            "d": 2
        },
        "methode1": {},
        "methode2": {
            "a": None
        },
        "methode3": {
            "a": {}
        }
    }
