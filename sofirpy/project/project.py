"""This module allows to take actions on a given hdf5 file and directory simultaneously."""

from os import rename
from pathlib import Path
from typing import Optional, Union
from sofirpy.project.hdf5 import HDF5
from sofirpy.project.project_dir import ProjectDir


class Project:
    """Object representing a project."""

    def __init__(
        self, hdf5_path: Union[Path, str], project_dir_path: Union[Path, str]
    ) -> None:
        """Initialize the Project object.

        Args:
            hdf5_path (Union[Path, str]): Path to the hdf5.
            project_dir_path (Union[Path, str]): Path to the project directory.
        """
        self.hdf5 = HDF5(hdf5_path)
        self.project_dir = ProjectDir(project_dir_path)

    def create_folder(self, folder_name: str) -> None:
        """Create a folder in the hdf5 and in the project directory.

        Args:
            folder_name (str): Name of the folder. Subfolders can be created by
                separating the folder names with '/'.

        Raises:
            error: If error occurs while creating the folder in the project directory.
        """
        self.hdf5.create_group(folder_name)
        try:
            self.project_dir.create_folder(folder_name)
        except Exception as error:
            self.hdf5.delete_group(folder_name)
            raise error

    def delete_folder(self, folder_name: str) -> None:
        """Delete a folder in the hdf5 and in the project directory.

        Args:
            folder_name (str): Name of the folder. Subfolders can be deleted by
                separating the folder names with '/'.
        """
        self.hdf5.delete_group(folder_name)
        self.project_dir.delete_folder(folder_name)

    def store_file(
        self,
        source_path: Union[str, Path],
        folder_name: str,
        copy: bool = True,
        new_file_name: Optional[str] = None,
    ) -> None:
        """Store a file in the project directory and a reference this file in the hdf5.

        Args:
            source_path (Union[str, Path]): Path to the file.
            folder_name (str): Name of the folder the file should be stored in.
            copy (bool, optional): If true the file will be copied
                from it's source path else it will be moved. Defaults to True.
            new_file_name (Optional[str], optional): If specified
                the file will be renamed accordingly. Defaults to None.
        """

        file_name = new_file_name if new_file_name else source_path.stem

        if copy:
            target_path = self.project_dir.copy_and_rename_file(
                source_path,
                self.project_dir.project_directory / folder_name,
                file_name
            )
        else:
            target_path = self.project_dir.move_and_rename_file(
                source_path,
                self.project_dir.project_directory / folder_name,
                file_name
            )

        self.hdf5.store_data(target_path.name, str(target_path), folder_name)

    def __repr__(self) -> str:
        return f"Project with project directory '{str(self.project_dir.project_directory)}' and hdf5 path '{str(self.hdf5.hdf5_path)}'"
