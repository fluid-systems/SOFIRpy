from pathlib import Path
from typing import Optional, Union
import fair_sim.utils as utils


class ProjectDir:

    def __init__(self, project_directory: Union[Path, str]) -> None:
        
        self.project_directory = project_directory
        self.current_folder = None

    @property
    def project_directory(self) -> Path:
        return self._project_directory

    @project_directory.setter
    def project_directory(self, project_directory: Union[Path, str]) -> None:

        self._project_directory = self._dir_setter(project_directory, 'project_directory')
    
    @property
    def current_folder(self) -> Union[Path, None]:
        return self._current_folder

    @current_folder.setter
    def current_folder(self, folder_path: Union[Path, str, None]) -> None:

        if folder_path is not None:
            folder_path = self._dir_setter(folder_path, 'folder_path')

        self._current_folder = folder_path                    
        
    def _dir_setter(self, dir_path: Union[Path, str], name: str) -> Path:

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

        folder_path = self.project_directory / folder_name
        if folder_path.exists():
            raise ValueError(f"{folder_path} already exists")
        self.current_folder = folder_path

    def set_current_folder(self, name: str) -> None:

        self.current_folder = self.project_directory / name

    def delete_element(self, name: str) -> None:
        
        if self.current_folder is not None:
            path = self.current_folder / name
            utils.delete_file_or_directory(path)
        else:
            print("'current_folder' is not set")

    def delete_files(self, file_names: list[str]) -> None:

        if self.current_folder is not None:
            utils.delete_files_in_directory(file_names, self.current_folder)
        else:
            print("'current_folder' is not set")

    def move_file(self, source_path: Path, target_directory: Union[Path, None] = None) -> Path:

        if target_directory is None:
            if self.current_folder is None:
                print("'current_folder' is not set")
                return
            target_directory = self.current_folder
        
        target_path = target_directory / source_path.name
        utils.move_file(source_path, target_path)

        return target_path

    def move_files(self, source_paths: list[Path], target_directory: Optional[Union[Path, None]] = None) -> None:

        if target_directory is None:
            if self.current_folder is None:
                print("'current_folder' is not set")
                return
            target_directory = self.current_folder
        self._dir_setter(target_directory, 'target directroy')

        utils.move_files(source_paths, target_directory)
        

    def copy_file(self, source_path: Path, target_directory: Optional[Union[Path, None]] = None) -> Path:
        
        if target_directory is None:
            if self.current_folder is None:
                print("'current_folder' is not set")
                return
            target_directory = self.current_folder

        self._dir_setter(target_directory, 'target directroy')
        target_path = target_directory / source_path.name

        utils.copy_file(source_path, target_path)

        return target_path

    def rename_file(self, file_path: Path, new_name: str) -> Path:

        return utils.rename_file(file_path, new_name)

    def delete_folder(self, folder_name: str) -> None:

        folder_path = self.project_directory / folder_name
        utils.delete_file_or_directory(folder_path)