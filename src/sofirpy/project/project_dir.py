"""This module allows to apply different actions within a directory."""

from pathlib import Path
from typing import Optional, Union

from sofirpy import utils


class ProjectDir:
    """Object representing the Project Directory."""

    def __init__(self, project_directory: Union[Path, str]) -> None:
        """Initialize the ProjectDir object.

        Args:
            project_directory (Union[Path, str]): Path to the project directory.
        """
        self.project_directory = project_directory  # type: ignore[assignment]
        self.current_folder: str = "."

    @property
    def project_directory(self) -> Path:
        """Path to the project directory.

        Returns:
            Path: Path to the project directory.
        """
        return self._project_directory

    @project_directory.setter
    def project_directory(self, project_directory: Union[Path, str]) -> None:
        """Set the path to the project directory.

        Args:
            project_directory (Union[Path, str]): Path to the project directory.
        """
        self._project_directory = self._dir_setter(
            project_directory, "project_directory"
        )

    @property
    def current_folder_path(self) -> Path:
        """Path to the current folder.

        Returns:
            Path: Path to the current folder.
        """
        return self._current_folder_path

    @property
    def _current_folder_path(self) -> Path:
        """Path to the current folder.

        Returns:
            Path: Path to the current folder.
        """
        return self.__current_folder_path

    @_current_folder_path.setter
    def _current_folder_path(self, folder_path: Union[Path, str]) -> None:
        """Path to the current folder.

        Args:
            folder_path (Union[Path, str]): Path to the current folder.
        """
        folder_path = self._dir_setter(folder_path, "folder_path")
        self.__current_folder_path = folder_path
        self._current_folder = str(folder_path.relative_to(self.project_directory))

    @property
    def current_folder(self) -> str:
        """Name of the current folder relative to the project directory.

        Returns:
            str: Name of the current folder relative to the project directory.
        """
        return self._current_folder

    @current_folder.setter
    def current_folder(self, folder_name: str) -> None:
        """Name of the current folder relative to the project directory.

        Args:
            folder_name (str): Name of the current folder relative to the
                project directory.

        Raises:
            TypeError: 'folder_name' type was not 'str'
        """
        if not isinstance(folder_name, str):
            raise TypeError(f"'folder_name' is {type(folder_name)}; expected str")
        self._current_folder_path = self.project_directory / folder_name

    def _dir_setter(self, dir_path: Union[Path, str], name: str) -> Path:
        """Check if the given path is a directory and create it if it doesn't exist.

        Args:
            dir_path (Union[Path, str]): Path to the directory.
            name (str): Name for what kind of directory 'dir_path' is.

        Raises:
            TypeError: 'dir_path' type was not 'Path', 'str'
            NotADirectoryError: 'dir_path' doest not lead to a directory

        Returns:
            Path: Path to the directory.
        """
        _dir_path = utils.convert_str_to_path(dir_path, name)

        if not _dir_path.exists():
            _dir_path.mkdir(parents=True)
            # raise FileNotFoundError(f"Directory '{dir_path}' doesn't exist.")
        if not _dir_path.is_dir():
            raise NotADirectoryError(
                f"Path at '{_dir_path}' is a file; expected directory"
            )

        return _dir_path

    def create_folder(self, folder_name: str) -> None:
        """Create a folder in the project directory.

        Args:
            folder_name (str): Name of the folder. Subfolders can be created by
                separating the folder names with '/'.

        Raises:
            FileExistsError: Folder already exists
        """
        folder_path = self.project_directory / folder_name
        if folder_path.exists():
            raise FileExistsError(f"Folder at {folder_path} already exists.")
        self.current_folder = folder_name

    def delete_element(self, name: str) -> None:
        """Delete file or directory in the current folder.

        Args:
            name (str): Name of the file/directory that should be deleted.
        """
        path = self._current_folder_path / name
        utils.delete_file_or_directory(path, print_status=True)

    def delete_files(self, file_names: list[str]) -> None:
        """Delete multiple files in the current folder.

        Args:
            file_names (list[str]): List with file names.
        """
        utils.delete_files_in_directory(
            file_names, self._current_folder_path, print_status=True
        )

    def move_file(
        self,
        source_path: Union[Path, str],
        target_directory: Optional[Union[Path, str]] = None,
    ) -> Path:
        """Move a file from a source path to a target directory.

        Args:
            source_path (Union[Path, str]): Source path of the file that should
                be moved.
            target_directory (Union[Path, str], optional): Target Directory
                the file should be moved to. If not specified the file is moved
                to the current folder. Defaults to None.

        Returns:
            Path: Path to the moved file.
        """

        _source_path = utils.convert_str_to_path(source_path, "source_path")

        if target_directory is None:
            target_directory = self._current_folder_path

        target_directory = self._dir_setter(target_directory, "target_directory")
        target_path = target_directory / _source_path.name
        utils.move_file(_source_path, target_path)

        return target_path

    def move_files(
        self,
        source_paths: list[Union[Path, str]],
        target_directory: Optional[Union[Path, str]] = None,
    ) -> list[Path]:
        """Move multiple files to a target directory.

        Args:
            source_paths (list[Union[Path, str]]): List of file paths that
                should be moved.
            target_directory (Optional[Union[Path, str]], optional):
                Target Directory the file should be moved to. If not specified
                the file is moved to the current folder. Defaults to None.

        Returns:
            Path: List of target paths.
        """
        return [
            self.move_file(source_path, target_directory)
            for source_path in source_paths
        ]

    def copy_file(
        self,
        source_path: Union[Path, str],
        target_directory: Optional[Union[Path, str]] = None,
    ) -> Path:
        """Copy a file from a source path to a target directory.

        Args:
            source_path (Union[Path, str]): Source path of the file that should
                be copied.
            target_directory (Optional[Union[Path, str]], optional): Target
                directory the file should be moved to. If not specified the
                file is moved to the current folder. Defaults to None.

        Returns:
            Path: Path to the copied file.
        """
        _source_path = utils.convert_str_to_path(source_path, "source_path")

        if target_directory is None:
            target_directory = self._current_folder_path

        target_directory = self._dir_setter(target_directory, "target directory")
        target_path = target_directory / _source_path.name

        utils.copy_file(_source_path, target_path)

        return target_path

    def rename_file(self, file_path: Union[Path, str], new_name: str) -> Path:
        """Rename a file.

        Args:
            file_path (Union[Path, str]): Path to the filed that should be renamed.
            new_name (str): New file name without the suffix. The suffix of the
                file will stay the same.

        Returns:
            Path: Path to the renamed file.
        """
        file_path = utils.convert_str_to_path(file_path, "file_path")

        return utils.rename_file(file_path, new_name)

    def delete_folder(self, folder_name: str) -> None:
        """Delete a folder in the project directory.

        Args:
            folder_name (str): Name of the folder that should be deleted.
                Subfolders can be deleted by separating the folder names
                with '/'.
        """
        folder_path = self.project_directory / folder_name
        utils.delete_file_or_directory(folder_path, print_status=True)
        if folder_path == self.current_folder_path:
            self.current_folder = "."

    def copy_and_rename_file(
        self, source_path: Union[Path, str], target_dir: Union[Path, str], new_name: str
    ) -> Path:
        """Copy and rename a file.

        Args:
            source_path (Union[Path, str]): Source path of the file that should
                be copied and renamed.
            target_dir (Union[Path, str]): Target directory the file should be
                copied to.
            new_name (str): New file name.

        Returns:
            Path: Path to the copied file.
        """
        _source_path = utils.convert_str_to_path(source_path, "source_path")
        _target_dir = utils.convert_str_to_path(target_dir, "target_dir")
        target_path = _target_dir / f"{new_name}{_source_path.suffix}"
        utils.copy_file(_source_path, target_path)

        return target_path

    def move_and_rename_file(
        self, source_path: Union[Path, str], target_dir: Union[Path, str], new_name: str
    ) -> Path:
        """Move and rename a file.s

        Args:
            source_path (Union[Path, str]): Source path of the file that should
                be moved and renamed.
            target_dir (Union[Path, str]): Target directory the file should be
                moved to.
            new_name (str): New file name.

        Returns:
            Path: Path to the moved file.
        """
        _source_path = utils.convert_str_to_path(source_path, "source_path")
        _target_dir = utils.convert_str_to_path(target_dir, "target_dir")
        target_path = _target_dir / f"{new_name}{_source_path.suffix}"
        utils.move_file(_source_path, target_path)

        return target_path

    def __repr__(self) -> str:
        return f"Project directory at '{str(self.project_directory)}'"
