from pathlib import Path
import shutil
from typing import Union


def delete_file_or_directory(path: Path, print_status: bool = False, must_exist: bool = False) -> None:

    if not path.exists():
        if not must_exist:
            return
        raise ValueError(f"{str(path)} does not exist")

    if path.is_dir():
        shutil.rmtree(str(path), ignore_errors=True)
    else:
        path.unlink()

    if print_status:
        print(f"{str(path)} has been deleted")


def delete_files_in_directory(
    file_names: list[str], directory: Path, print_status: bool = False
) -> None:

    for file_name in file_names:
        path = directory / file_name
        delete_file_or_directory(path, print_status)


def delete_paths(paths: list[Path], must_exist: bool = False) -> None:

    for path in paths:
        delete_file_or_directory(path, must_exist=must_exist)


def move_file(source_path: Path, target_path: Path) -> None:

    if source_path == target_path:
        return
    if not source_path.exists():
        raise FileNotFoundError(f"{source_path} does not exits.")
    if target_path.exists():
        overwrite = _get_user_input_for_overwriting(target_path)
        if not overwrite:
            raise FileExistsError(f"{target_path} already exists")
    if not target_path.parent.exists():
        target_path.parent.mkdir(parents=True)

    source_path.replace(target_path)


def move_files(source_paths: list[Path], target_directory: Path) -> None:

    for source_path in source_paths:
        target_path = target_directory / source_path.name
        move_file(source_path, target_path)


def copy_file(source_path: Path, target_path: Path) -> None:

    if not source_path.exists():
        raise FileNotFoundError(f"{source_path} does not exits.")
    if not source_path.is_file():
        raise ValueError(f"{source_path} is a directory; expected file")
    if source_path == target_path:
        return
    if target_path.exists():
        overwrite = _get_user_input_for_overwriting(target_path)
        if not overwrite:
            raise FileExistsError(f"{target_path} already exists")
    if not target_path.parent.exists():
        target_path.parent.mkdir(parents=True)

    shutil.copy(source_path, target_path)


def _get_user_input_for_overwriting(target_path: Union[Path, str], typ: str = "path") -> bool:

    while True:
        overwrite = input(f"The {typ} {target_path} already exists. Overwrite? [y/n]")
        if overwrite == "y":
            return True
        if overwrite == "n":
            return False
        print("Enter 'y' or 'n'.")


def _get_user_input_for_creating_path(path: Path) -> bool:

    while True:
        while True:
            create = input(f"Path {path} doesn't exist. Create? [y/n]")
            if create == "y":
                return True
            if create == "n":
                return False
            print("Enter 'y' or 'n'.")

def rename_file(file_path: Path, new_name: str) -> Path:

    if not file_path.exists():
        raise FileNotFoundError(f"{file_path} does not exist")
    if file_path.is_dir():
        raise ValueError(f"{file_path} is a directory; expected file")
    target_path = file_path.parent / f"{new_name}{file_path.suffix}"
    if target_path.exists():
        overwrite = _get_user_input_for_overwriting(target_path)
        if not overwrite:
            raise FileExistsError(f"{target_path} already exists")
        target_path.unlink()

    return file_path.rename(target_path)


def convert_str_to_path(path: Union[str, Path], variable_name: str) -> Path:

    if not isinstance(path, (Path, str)):
        raise TypeError(f"'{variable_name}' is {type(path)};  expected Path, str")

    return path if isinstance(path, Path) else Path(path)
