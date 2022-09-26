import shutil
from pathlib import Path

import h5py
import pytest

from sofirpy import Project


@pytest.fixture()
def project() -> Project:
    test_hdf5_path = Path(__file__).parent / "test_hdf5.hdf5"
    directory = Path(__file__).parent / "test_project_dir"
    return Project(test_hdf5_path, directory)


def _copy_standard_project(project: Project, test_name: str) -> Project:
    copy_dir = project.project_dir.project_directory.parent / f"{test_name}_project"
    shutil.copytree(project.project_dir.project_directory, copy_dir)
    copy_path_hdf5 = project.hdf5.hdf5_path.parent / f"{test_name}.hdf5"
    shutil.copy(project.hdf5.hdf5_path, copy_path_hdf5)
    return Project(copy_path_hdf5, copy_dir)


def test_create_folder(project: Project) -> None:
    try:
        _project = _copy_standard_project(project, "test_create_folder")
        folder_name = "test_create_folder"
        _project.create_folder(folder_name)
        folder_path = _project.project_dir.project_directory / folder_name
        assert folder_path.exists()
        with h5py.File(str(_project.hdf5.hdf5_path), "a") as hdf5_file:
            assert folder_name in hdf5_file
    finally:
        shutil.rmtree(_project.project_dir.project_directory, ignore_errors=True)
        _project.hdf5.hdf5_path.unlink()
