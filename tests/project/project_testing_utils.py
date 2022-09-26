import shutil
from functools import wraps

from sofirpy import HDF5, ProjectDir


def hdf5_clean_up(func):
    @wraps(func)
    def wrapper(hdf5: HDF5):

        _hdf5 = _copy_standard_hdf5(hdf5, func.__name__)

        try:
            func(_hdf5)
        finally:
            _hdf5.hdf5_path.unlink()

    return wrapper


def _copy_standard_hdf5(hdf5: HDF5, test_name: str) -> HDF5:
    copy_path = hdf5.hdf5_path.parent / f"{test_name}.hdf5"
    shutil.copy(hdf5.hdf5_path, copy_path)
    return HDF5(copy_path)


def project_dir_clean_up(func):
    @wraps(func)
    def wrapper(project_dir: ProjectDir):

        _project_dir = _copy_standard_project_dir(project_dir, "test_create_folder")

        try:
            func(_project_dir)
        finally:
            shutil.rmtree(_project_dir.project_directory, ignore_errors=True)

    return wrapper


def _copy_standard_project_dir(project_dir: ProjectDir, test_name: str) -> ProjectDir:
    copy_path = project_dir.project_directory.parent / f"{test_name}_project_dir"
    shutil.copytree(project_dir.project_directory, copy_path)
    return ProjectDir(copy_path)
