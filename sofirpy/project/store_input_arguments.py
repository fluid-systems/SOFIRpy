from inspect import getfullargspec
from functools import wraps
from typing import Callable


def store_input_arguments(func: Callable):
    """Decorator that lets you store the input arguments of class methods.

    The input arguments will be stored in a nested dictionary with the following structure:

    >>> {"<method_name1>":
    ...     {
    ...         "<input_name1>": <input_value1>,
    ...         "<input_name2>": <input_value2>
    ...     },
    ...  "<method_name2>":
    ...     {
    ...         "<input_name1>": <input_value1>,
    ...         "<input_name2>": <input_value2>
    ... }
    ... }

    The dictionary will be stored as a class attribute with the name '__input_arguments__'.

    Args:
        func (Callable): Method to decorate

    Returns:
        Callable: Decorated Method
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        insp = getfullargspec(func)
        # add input arguments
        inputs = {name: value for name, value in zip(insp.args[1:], args[1:])}
        # add overwritten defaults
        inputs = {**inputs, **kwargs}
        # add defaults
        if insp.defaults:
            for name, val in zip(insp.args[::-1], insp.defaults[::-1]):
                if name not in list(inputs.keys()):
                    inputs[name] = val
        return_value = func(*args, **kwargs)
        method_input_info = {func.__name__: inputs}
        if hasattr(args[0], "__input_arguments__"):
            args[0].__input_arguments__ = {
                **args[0].__input_arguments__,
                **method_input_info,
            }
        else:
            args[0].__input_arguments__ = method_input_info
        return return_value

    return wrapper
