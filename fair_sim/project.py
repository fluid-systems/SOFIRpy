import os
import h5py
import shutil
from datetime import datetime
from typing import Callable, Optional
from fair_sim.read_hdf5_data import read_data
import numpy

class InitiateProject:
    def __init__(
        self,
        working_directory: str,
        hdf5_file_name: Optional[str] = None,
        pid_generator: Optional[Callable[[str], str]] = None,
    ) -> None:

        self.working_directory = working_directory
        self.pid_generator = pid_generator if pid_generator else generate_default_pid
        self.hdf5_file_name = hdf5_file_name
        self.hdf5_path = os.path.normpath(
            os.path.join(self.working_directory, self.hdf5_file_name)
        )

    @property
    def working_directory(self) -> str:
        return self._working_directory

    @working_directory.setter
    def working_directory(self, working_directory: str) -> None:

        if not os.path.exists(working_directory):
            os.makedirs(working_directory)

        self._working_directory = working_directory

    @property
    def hdf5_file_name(self) -> str:
        return self._hdf5_file_name

    @hdf5_file_name.setter
    def hdf5_file_name(self, hdf5_file_name: str) -> None:

        files = os.listdir(self.working_directory)
        hdf5s = list(filter(lambda file: file.endswith(".hdf5"), files))
        if len(hdf5s) > 1:
            raise MoreThenOneHdf5Error(
                f"'{self.working_directory}' should only have one hdf5 inside."
            )

        if hdf5_file_name:
            name = (
                hdf5_file_name
                if hdf5_file_name.endswith(".hdf5")
                else hdf5_file_name + ".hdf5"
            )
            if not hdf5s:
                self.create_hdf5(os.path.join(self.working_directory, name))
                self._hdf5_file_name = name
            else:
                if hdf5s[0] == name:
                    self._hdf5_file_name = name
                    print(f"Using existing hdf5 '{self._hdf5_file_name}'")
                else:
                    raise MoreThenOneHdf5Error(
                        f"In '{self.working_directory}' already exists a hdf5 file with the name '{hdf5s[0]}'. Can't create a second one with the name '{name}'."
                    )
        else:
            if hdf5s:
                self._hdf5_file_name = hdf5s[0]
                print(f"Using existing hdf5 '{self._hdf5_file_name}'")
            else:
                name = self.pid_generator("hdf5") + ".hdf5"
                self.create_hdf5(os.path.join(self.working_directory, name))
                self._hdf5_file_name = name

    def create_hdf5(self, hdf5_path: str) -> None:
        hdf5 = h5py.File(f"{hdf5_path}", "a")
        hdf5.attrs["creation date"] = datetime.now().strftime(
                "%A, %d. %B %Y, %H:%M:%S"
            )
        print(f"File '{hdf5_path}' created")
        hdf5.close()


class Project(InitiateProject):
    def __init__(
        self,
        working_directory,
        hdf5_file_name=None,
        pid_generator=None,
        run_name_generator: Optional[Callable[[str, int], str]] = None,
    ) -> None:

        super().__init__(working_directory, hdf5_file_name, pid_generator)
        self.run_name_generator = (
            run_name_generator if run_name_generator else self.generate_default_run_name
        )
        self.current_run_name = None

    def create_run(
        self, hdf5_sub_groups, run_name_suffix=None, attr=None, create_run_folder=True
    ):

        number_of_runs = self.get_number_of_runs()
        self.current_run_name = self.run_name_generator(number_of_runs, run_name_suffix)
        self.check_run_exists()
        self.create_hdf5_run(hdf5_sub_groups, attr)
        if create_run_folder:
            self.create_run_folder()

    def create_hdf5_run(self, hdf5_sub_groups, attr=None) -> None:

        # create run group
        group_attr = {"creation date": datetime.now().strftime("%A, %d. %B %Y, %H:%M:%S")}
        self.create_hdf5_group(self.current_run_name, group_attr)
        print(f"{self.current_run_name} created")
        
        x = lambda sub: "/" + sub if not sub.startswith("/") else sub
        hdf5_sub_groups = list(map(x, hdf5_sub_groups))
        for sub in hdf5_sub_groups:
            name = sub[1:]
            if attr:
                sub_attr = attr.get(name)
            else:
                sub_attr = None
            self.create_hdf5_group(self.current_run_name + sub, sub_attr)

    def create_hdf5_group(self, group_path, attr = None):

        with h5py.File(f"{self.hdf5_path}", "a") as hdf5:
            group = hdf5.create_group(group_path)
            if attr:
                for k, v in attr.items():
                    group.attrs[k] = v


    def create_run_folder(self) -> None:

        folder_path = os.path.join(self.working_directory, self.current_run_name)

        os.mkdir(folder_path)

    def check_run_exists(self) -> None:

        with h5py.File(self.hdf5_path, "a") as hdf5:
            runs = list(hdf5.keys())

        exists_in_hdf5 = False
        if self.current_run_name in runs:
            exists_in_hdf5 = True

        folder_path = os.path.join(self.working_directory, self.current_run_name)
        exists_as_folder = False
        if os.path.exists(folder_path):
            exists_as_folder = True

        if exists_as_folder:
            if exists_in_hdf5:
                while True:
                    overwrite = input(
                        f"The run '{self.current_run_name}' already exists in the hdf5 and as a folder in {self.working_directory}. Overwrite? [y/n]"
                    )
                    if overwrite == "y":
                        self.delete_run(self.current_run_name)
                        break
                    elif overwrite == "n":
                        raise RunAlreadyExistError("Runs already exist.")

            else:
                overwrite = input(
                    f"The run '{self.current_run_name}' exists as a folder but not in the hdf5. Overwrite? [y/n]"
                )
                while True:
                    if overwrite == "y":
                        self.delete_run_folder(self.current_run_name)
                        break
                    elif overwrite == "n":
                        raise RunAlreadyExistError("Run already exist.")

        else:
            if exists_in_hdf5:
                while True:
                    overwrite = input(
                        f"The run '{self.current_run_name}' already exists in the hdf5 but not as a folder. Overwrite = [y/n]"
                    )
                    if overwrite == "y":
                        self.delete_hdf5_run(self.current_run_name)
                        break
                    elif overwrite == "n":
                        raise RunAlreadyExistError("Run already exist.")

    def delete_run(self, run_name: str) -> None:

        self.delete_run_folder(run_name)
        self.delete_hdf5_run(run_name)

    def delete_run_folder(self, run_name: str) -> None:

        try:
            shutil.rmtree(os.path.join(self.working_directory, run_name))
            print(f"The folder '{run_name}' has been deleted.")
        except FileNotFoundError:
            print(f"Folder with the name '{run_name}' doesn't exists.")

    def delete_hdf5_run(self, name: str) -> None:

        with h5py.File(self.hdf5_path, "a") as hdf5:
            try:
                del hdf5[name]
                print(f"The hdf5 run '{name}' has been deleted.")
            except KeyError:
                print(f"hdf5 run with the name '{name}' doesn't exists.")

    def delete_data_in_run(self, run_name, data_name):

    
        hdf5_data_path, deleted_data = self.delete_data_in_hdf5_run(run_name, data_name)
        _deleted_data = deleted_data
        
        if isinstance(deleted_data, (bytes, numpy.ndarray, str)):
            if isinstance(deleted_data, numpy.ndarray):
                if deleted_data.size == 1:
                    deleted_data = deleted_data[0,0]
                else:
                    print("Corresponing file to hdf5 data at {hdf5_data_path} can not be determined.")
                    return
            if isinstance(deleted_data, bytes):
                deleted_data = deleted_data.decode('utf-8')
        
        else:
            print(f"Corresponing file to hdf5 data at {hdf5_data_path} can not be determined.")

        run_path = os.path.join(self.working_directory, run_name)
        dir = os.listdir(run_path)

        files = list(filter(lambda file: os.path.splitext(file)[0] == deleted_data, dir))

        if not files:
            print("No corresponing file found")
            return
        if len(files) > 1:
            msg = ""
            for file in files:
                if os.path.isfile(os.path.join(run_path, file)):
                    ext = os.path.splitext(file)[1]
                    msg += f"Enter {ext} to delete {file}.\n"
            while True:
                file_extension = input(msg)
                file_to_delete = deleted_data + file_extension
                path = os.path.join(run_path, file_to_delete)
                if os.path.exists(path):
                    break
                else:
                    print(f"{file_extension} is not a valid file extension")
        self.delete_data_in_folder_run(run_name, file_to_delete)

        return _deleted_data

    def delete_data_in_hdf5_run(self, run_name, data_name):
        
        with h5py.File(self.hdf5_path, "a") as hdf5:
            path = run_name + "/" + data_name
            if not hdf5.get(path):
                raise KeyError(f"{path} does not exist in hdf5.")
            if isinstance (hdf5.get(path), h5py.Dataset):
                deleted_data = read_data(self.hdf5_path, path)
            else:
                raise DataNotADatasetError(f"The hdf5 path {path} does not lead to a Dataset") 
            try:
                del hdf5[path]
                print(f"The hdf5 dataset '{path}' has been deleted.")
            except KeyError:
                print(f"The hdf5 path with the name '{path}' doesn't exists.")

        return path, deleted_data

    def delete_data_in_folder_run(self, run_name, file_name):

        path = os.path.join(self.working_directory, run_name, file_name)
        if os.path.exists(path):
            os.remove(path)
            print(f'File at {path} has been deleted.')
        else:
            print(f"Path {path} does not exist.")

    def generate_default_run_name(
        self, number_of_runs: int, run_name_suffix: str = None
    ) -> str:

        if run_name_suffix:
            return f"Run_{number_of_runs + 1}_" + run_name_suffix
        return f"Run_{number_of_runs + 1}"

    def get_number_of_runs(self) -> int:

        return len(self.get_hdf5_runs())

    def get_hdf5_runs(self):

        with h5py.File(self.hdf5_path, "a") as hdf5:
            return list(hdf5.keys())


def generate_default_pid(type: str, **kwargs) -> str:
    now = datetime.now()
    date = now.strftime("%y%m%d")
    signature_number = now.strftime("%H%M%S")

    return f"{type}_{date}_{signature_number}"


class DirectoryDoesNotExistError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


class MoreThenOneHdf5Error(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


class RunNotFoundError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


class RunAlreadyExistError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)

class DataNotADatasetError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)