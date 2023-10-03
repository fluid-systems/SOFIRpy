"""Utility functions used across sofirpy."""

import shutil
from pathlib import Path
from typing import Any, Union

import pkg_resources


def delete_file_or_directory(
    path: Path, print_status: bool = False, must_exist: bool = False
) -> None:
    """Delete file ore directory.

    Args:
        path (Path): Path to be deleted.
        print_status (bool, optional): If 'True', a print to the console will
            confirm the deletion. Defaults to False.
        must_exist (bool, optional): Defines wether a file or directory has to
            exist. Defaults to False.

    Raises:
        ValueError: 'path' doesn't exist and 'must_exist' is set to True.
    """
    if not path.exists():
        if not must_exist:
            return
        raise FileNotFoundError(f"{str(path)} does not exist")

    if path.is_dir():
        shutil.rmtree(str(path), ignore_errors=True)
    else:
        path.unlink()

    if print_status:
        print(f"{str(path)} has been deleted")


def delete_files_in_directory(
    file_names: list[str], directory: Path, print_status: bool = False
) -> None:
    """Delete multiple files in a directory.

    Args:
        file_names (list[str]): Name of the files.
        directory (Path): Path to the directory.
        print_status (bool, optional): If 'True', a print to the console will
            confirm the deletion of a file. Defaults to False.
    """

    for file_name in file_names:
        path = directory / file_name
        delete_file_or_directory(path, print_status)


def delete_paths(paths: list[Path], must_exist: bool = False) -> None:
    """Delete multiple paths.

    Args:
        paths (list[Path]): Paths that should be deleted.
        must_exist (bool, optional): Defines wether a file or directory has to
            exist. Defaults to False.
    """
    for path in paths:
        delete_file_or_directory(path, must_exist=must_exist)


def move_file(source_path: Path, target_path: Path) -> None:
    """Move a file from a source to a target path.

    Args:
        source_path (Path): source path
        target_path (Path): target path

    Raises:
        FileNotFoundError: 'source_path' doesn't exist.
        FileExistsError: 'target_path' does already exist.
    """
    if source_path == target_path:
        return
    if not source_path.exists():
        raise FileNotFoundError(f"{source_path} does not exits.")
    if target_path.exists():
        overwrite = get_user_input_for_overwriting(target_path)
        if not overwrite:
            raise FileExistsError(f"{target_path} already exists")
    if not target_path.parent.exists():
        target_path.parent.mkdir(parents=True)

    source_path.replace(target_path)


def move_files(source_paths: list[Path], target_directory: Path) -> None:
    """Move multiple files to a target directory.

    Args:
        source_paths (list[Path]): Files that should be moved.
        target_directory (Path): target directory
    """
    for source_path in source_paths:
        target_path = target_directory / source_path.name
        move_file(source_path, target_path)


def copy_file(source_path: Path, target_path: Path) -> None:
    """Copy a file.

    Args:
        source_path (Path): source path
        target_path (Path): target path

    Raises:
        FileNotFoundError: 'source_path' doesn't exist.
        IsADirectoryError: 'source_path' is a directory.
        FileExistsError: 'target_path' does already exist.
    """
    if not source_path.exists():
        raise FileNotFoundError(f"{source_path} does not exits.")
    if not source_path.is_file():
        raise IsADirectoryError(f"{source_path} is a directory; expected file")
    if source_path == target_path:
        return
    if target_path.exists():
        overwrite = get_user_input_for_overwriting(target_path)
        if not overwrite:
            raise FileExistsError(f"{target_path} already exists")
    if not target_path.parent.exists():
        target_path.parent.mkdir(parents=True)

    shutil.copy(source_path, target_path)


def get_user_input_for_overwriting(
    target_path: Union[Path, str], typ: str = "path"
) -> bool:
    """Get user input for overwriting a path.

    Args:
        target_path (Union[Path, str]): Path that should be overwritten.
        typ (str, optional): Name of the path. Defaults to "path".

    Returns:
        bool: True if path should be overwritten, else False
    """
    while True:
        overwrite = input(f"The {typ} {target_path} already exists. Overwrite? [y/n]")
        if overwrite == "y":
            return True
        if overwrite == "n":
            return False
        print("Enter 'y' or 'n'.")


def rename_file(file_path: Path, new_name: str) -> Path:
    """Rename a file.

    Args:
        file_path (Path): Path of the file to be renamed.
        new_name (str): New file name.

    Raises:
        FileNotFoundError: 'file_path' doesn't exist.
        IsADirectoryError: 'file_path' is a directory.
        FileExistsError: The new path does already exist.

    Returns:
        Path: path to the renamed file
    """
    if not file_path.exists():
        raise FileNotFoundError(f"{file_path} does not exist")
    if file_path.is_dir():
        raise IsADirectoryError(f"{file_path} is a directory; expected file")
    target_path = file_path.parent / f"{new_name}{file_path.suffix}"
    if target_path.exists():
        overwrite = get_user_input_for_overwriting(target_path)
        if not overwrite:
            raise FileExistsError(f"{target_path} already exists")
        target_path.unlink()

    return file_path.rename(target_path)


def convert_str_to_path(path: Union[str, Path], variable_name: str) -> Path:
    """Convert a str to a Path object.

    Args:
        path (Union[str, Path]): Path.
        variable_name (str): Name of the variable.

    Raises:
        TypeError: path type was invalid

    Returns:
        Path: Path object
    """
    check_type(path, variable_name, (Path, str))
    return path if isinstance(path, Path) else Path(path)


def check_type(var: Any, var_name: str, expected_type: Any) -> None:
    """Check the type of a given variable.

    Args:
        var (Any): variable to be checked
        var_name (str): Name of the variable
        expected_type (Any): expected type

    Raises:
        TypeError: type variable of was not expected type
    """
    if not isinstance(var, expected_type):
        msg = f"'{var_name}' has type {type(var).__name__}; expected "
        if isinstance(expected_type, tuple):
            msg += ", ".join([typ.__name__ for typ in expected_type])
        else:
            msg += expected_type.__name__
        raise TypeError(msg)


def get_dependencies_of_current_env() -> dict[str, str]:
    """Get the dependencies of the current python environment.

    Returns:
        dict[str, str]: key -> name of the package; value -> version
    """
    installed_packages = pkg_resources.working_set
    return {package.project_name: package.version for package in installed_packages}
