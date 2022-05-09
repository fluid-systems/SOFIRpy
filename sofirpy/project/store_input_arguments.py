from inspect import getfullargspec
from functools import wraps
from typing import Callable

from attr import has

def store_input_arguments(func: Callable):
    """Decorator that lets you store the input arguments of class methods.

    The input arguments will be stored in a nested dictrionay with the following structure:
    
    >>> {"<methode_name1>": 
    ...     {
    ...         "<input_name1>": <input_value1>,
    ...         "<input_name2>": <input_value2>
    ...     },
    ...  "<methode_name2>": 
    ...     {
    ...         "<input_name1>": <input_value1>,
    ...         "<input_name2>": <input_value2>
    ... }
    ... }
    
    The dictrionay will be stored as a class attribute with the name '__input_arguments__'.

    Args:
        func (Callable): Methode to decorate

    Returns:
        Callable: Decorated Methode
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
        func(*args, **kwargs)
        methode_input_info = {func.__name__: inputs}
        if hasattr(args[0], "__input_arguments__"):
            args[0].__input_arguments__ = {**args[0].__input_arguments__, **methode_input_info}
        else:
            args[0].__input_arguments__ = methode_input_info
    return wrapper