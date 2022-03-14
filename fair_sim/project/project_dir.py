"""This module allows to apply different actions within a directory."""

from pathlib import Path
from typing import Optional, Union
import fair_sim.utils as utils


class ProjectDir:
    """Object representing the Project Directory."""

    def __init__(self, project_directory: Union[Path, str]) -> None:
        """Initialize the ProjectDir object.

        Args:
            project_directory (Union[Path, str]): Path to the project directory.
        """
        self.project_directory = project_directory
        self.current_folder = None

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
    def current_folder(self) -> Path:
        """Path to the current folder.

        Returns:
            Path: Path to the current folder.
        """
        return self._current_folder

    @current_folder.setter
    def current_folder(self, folder_path: Union[Path, str]) -> None:
        """Path to the current folder.

        Args:
            folder_path (Union[Path, str]): Path to the current folder.
        """
        if folder_path is not None:
            folder_path = self._dir_setter(folder_path, "folder_path")

        self._current_folder = folder_path

    def _dir_setter(self, dir_path: Union[Path, str], name: str) -> Path:
        """Set the path to a directory. If it doesn't exit, create it.

        Args:
            dir_path (Union[Path, str]): Path to the directory.
            name (str): Name for what kind of directory 'dir_path' is.

        Raises:
            TypeError: 'dir_path' type was not 'Path', 'str'
            ValueError: 'dir_path' leads to a file

        Returns:
            Path: Path to the directory.
        """
        if not isinstance(dir_path, (Path, str)):
            raise TypeError(f"'{name}' is {type(dir_path)}; expected Path, str")

        if isinstance(dir_path, str):
            dir_path = Path(dir_path)

        if not dir_path.exists():
            dir_path.mkdir(parents=True)
        else:
            if not dir_path.is_dir():
                raise ValueError(f"{dir_path} is a file; expected directory")

        return dir_path

    def create_folder(self, folder_name: str) -> None:
        """Create a folder in the project directory.

        Args:
            folder_name (str): Name of the folder. Subfolders can be created by
                seperating the folder names with '/'.
        """
        folder_path = self.project_directory / folder_name
        if folder_path.exists():
            print(f"Folder at {folder_path} already exists.")
        self.current_folder = folder_path

    def set_current_folder(self, folder_name: str) -> None:
        """Set the current folder.

        Args:
            folder_name (str): Name of the folder.
        """
        folder_path = self.project_directory / folder_name
        if not folder_path.exists():
            print(f"Folder at {folder_path} doesn't exist.")
            return
        if not folder_path.is_dir():
            print(f"{folder_path} does not lead to a directory.")
            return
        self.current_folder = folder_path

    def delete_element(self, name: str) -> None:
        """Delete file or directory in the current folder.

        Args:
            name (str): Name of the file/directory that should be deleted.
        """
        if self.current_folder is not None:
            path = self.current_folder / name
            utils.delete_file_or_directory(path, print_status=True)
        else:
            print("'current_folder' is not set")

    def delete_files(self, file_names: list[str]) -> None:
        """Delete multiple files in the current folder.

        Args:
            file_names (list[str]): List with file names.
        """
        if self.current_folder is not None:
            utils.delete_files_in_directory(
                file_names, self.current_folder, print_status=True
            )
        else:
            print("'current_folder' is not set")

    def move_file(
        self, source_path: Union[Path, str], target_directory: Union[Path, str] = None
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
        if isinstance(source_path, str):
            source_path = Path(source_path)

        if target_directory is None:
            if self.current_folder is None:
                print("'current_folder' is not set")
                return
            target_directory = self.current_folder

        target_directory = self._dir_setter(target_directory, "target directroy")
        target_path = target_directory / source_path.name
        utils.move_file(source_path, target_path, print_status=True)

        return target_path

    def move_files(
        self,
        source_paths: list[Union[Path, str]],
        target_directory: Optional[Union[Path, str]] = None,
    ) -> None:
        """Move multiple files to a target directory.

        Args:
            source_paths (list[Union[Path, str]]): List of file paths that
                should be moved.
            target_directory (Optional[Union[Path, str]], optional):
                Target Directory the file should be moved to. If not specified
                the file is moved to the current folder. Defaults to None.
        """
        source_paths = list(
            map(
                lambda path: Path(path) if isinstance(path, str) else path, source_paths
            )
        )

        if target_directory is None:
            if self.current_folder is None:
                print("'current_folder' is not set")
                return
            target_directory = self.current_folder
        target_directory = self._dir_setter(target_directory, "target directroy")

        utils.move_files(source_paths, target_directory, print_status=True)

    def copy_file(
        self,
        source_path: Union[Path, str],
        target_directory: Optional[Union[Path, str]] = None,
    ) -> Path:
        """Copy a file from a source path to a target directory while keeping the file name.

        Args:
            source_path (Union[Path, str]): Source path of the file that should
                be copied.
            target_directory (Optional[Union[Path, str]], optional): Target
                Directory the file should be moved to. If not specified the
                file is moved to the current folder. Defaults to None.

        Returns:
            Path: Path to the copied file.
        """
        if isinstance(source_path, str):
            source_path = Path(source_path)

        if target_directory is None:
            if self.current_folder is None:
                print("'current_folder' is not set")
                return
            target_directory = self.current_folder

        target_directory = self._dir_setter(target_directory, "target directroy")
        target_path = target_directory / source_path.name

        utils.copy_file(source_path, target_path)

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
        if isinstance(file_path, str):
            file_path = Path(file_path)

        return utils.rename_file(file_path, new_name)

    def delete_folder(self, folder_name: str) -> None:
        """Delete a folder in the project directory.

        Args:
            folder_name (str): Name of the folder that should be deleted.
                Subfolders can be deleted by seperating the folder names
                with '/'.
        """
        folder_path = self.project_directory / folder_name
        utils.delete_file_or_directory(folder_path, print_status=True)