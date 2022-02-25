from inspect import getfullargspec
from functools import wraps

def store_input_arguments(func):

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