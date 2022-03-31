from inspect import getfullargspec
from functools import wraps
from typing import Callable

def store_input_arguments(func: Callable):
    """Decorator that lets you store the input arguments of the __init__ class methode.

    The input arguments will be stored as a dictrionay with the variable names
    as keys and the value of the variables as values. The dictrionay will be
    stored as a class attribute with the name '__input_arguments__'.

    Args:
        func (Callable): Function to decorate

    Returns:
        Callable: Decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        insp = getfullargspec(func)
        # add input arguments
        inputs = {name: value for name, value in zip(insp.args[1:], args[1:])}
        # add overwritten defaults
        inputs = {**inputs, **kwargs}
        # add defaults
        for name, val in zip(insp.args[::-1], insp.defaults[::-1]):
            if name not in list(inputs.keys()):
                inputs[name] = val
        func(*args, **kwargs)
        args[0].__input_arguments__ = inputs

    return wrapper