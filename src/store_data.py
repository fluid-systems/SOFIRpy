import os
import h5py
import shutil
from datetime import datetime
from typing import Callable, Optional


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
        self, hdf5_sub_groups, run_name=None, attr=None, create_run_folder=True
    ):

        number_of_runs = self.get_number_of_runs()
        self.current_run_name = self.run_name_generator(number_of_runs, run_name)
        self.check_run_exists()
        self.create_hdf5_run(hdf5_sub_groups, attr)
        if create_run_folder:
            self.create_run_folder()

    def create_hdf5_run(self, hdf5_sub_groups, attr=None) -> None:

        with h5py.File(f"{self.hdf5_path}", "a") as hdf5:

            group = hdf5.create_group(self.current_run_name)
            group.attrs["creation date"] = datetime.now().strftime(
                "%A, %d. %B %Y, %H:%M:%S"
            )

            x = lambda sub: "/" + sub if not sub.startswith("/") else sub
            hdf5_sub_groups = list(map(x, hdf5_sub_groups))

            for sub in hdf5_sub_groups:
                group = hdf5.create_group(self.current_run_name + sub)
                name = sub[1:]
                if attr and attr.get(name):
                    for k, v in attr[name].items():
                        group.attrs[k] = v

            print(f"{self.current_run_name} created")

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

    def delete_run_folder(self, run_name: str) -> None:

        try:
            shutil.rmtree(os.path.join(self.working_directory, run_name))
        except FileNotFoundError as err:
            print(err)

    def delete_hdf5_run(self, run_name: str) -> None:

        with h5py.File(self.hdf5_path, "a") as hdf5:
            try:
                del hdf5[run_name]
            except KeyError as err:
                print(err, f". '{run_name}' doesn't exists.")

    def delete_run(self, run_name: str) -> None:

        self.delete_run_folder(run_name)
        self.delete_hdf5_run(run_name)

    def generate_default_run_name(
        self, number_of_runs: int, run_name: str = None
    ) -> str:

        if run_name:
            return f"Run_{number_of_runs + 1}_" + run_name
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


def store_data(hdf5_path, data, data_name, folder, attributes: dict = None):

    with h5py.File(hdf5_path, "a") as hdf5:
        folder = hdf5[folder]
        dset = folder.create_dataset(data_name, data=data)
        if attributes:
            for name, attr in attributes.items():
                dset.attrs[name] = attr


def read_data(hdf5_path, data_name, get_attribute=False):

    with h5py.File(hdf5_path, "a") as hdf5:
        _data = hdf5.get(data_name)
        if isinstance(_data, h5py.Dataset):
            data = _data[()]

        elif isinstance(_data, h5py.Group):
            data = list(_data.keys())

        else:
            data = None

        if get_attribute:
            attr = dict(_data.attrs)
            return data, attr
    return data


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
