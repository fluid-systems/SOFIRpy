"""Module containing a decorator for storing input arguments of instance method."""

from functools import wraps
from inspect import getfullargspec
from typing import Any, Callable, TypeVar

from typing_extensions import Concatenate, ParamSpec

P = ParamSpec("P")
RT = TypeVar("RT")
T = TypeVar("T", bound=Any)


def store_input_arguments(
    func: Callable[Concatenate[T, P], RT]
) -> Callable[Concatenate[T, P], RT]:
    """Decorator that lets you store the input arguments of instance methods.

    The input arguments will be stored in a nested dictionary with the
    following structure:

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

    The dictionary will be stored as a instance attribute with
    the name '__input_arguments__'.

    Args:
        func (Callable[Concatenate[T, P], RT]): Method to decorate

    Returns:
        Callable[Concatenate[T, P], RT]: Decorated Method
    """

    @wraps(func)
    def wrapper(self: T, *args: P.args, **kwargs: P.kwargs) -> RT:
        insp = getfullargspec(func)
        # add input arguments
        inputs = dict(zip(insp.args[1:], args[0:]))
        # add overwritten defaults
        inputs = {**inputs, **kwargs}
        # add defaults
        if insp.defaults:
            for name, val in zip(insp.args[::-1], insp.defaults[::-1]):
                if name not in list(inputs.keys()):
                    inputs[name] = val
        method_input_info = {func.__name__: inputs}
        if hasattr(self, "__input_arguments__"):
            self.__input_arguments__ = {**self.__input_arguments__, **method_input_info}
        else:
            self.__input_arguments__ = method_input_info
        return func(self, *args, **kwargs)

    return wrapper  # type: ignore[return-value]