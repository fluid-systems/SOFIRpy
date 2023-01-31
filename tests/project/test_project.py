import shutil
import tempfile
from pathlib import Path

import pytest

from sofirpy import Project


@pytest.fixture()
def project() -> Project:
    _hdf5 = Path(__file__).parent / "test_hdf5.hdf5"
    directory = Path(__file__).parent / "test_project_dir"
    _project = Project(_hdf5, directory)
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield _copy_standard_project(_project, "test_project", Path(tmp_dir))


def _copy_standard_project(project: Project, test_name: str, tmp_dir: Path) -> Project:
    copy_dir = tmp_dir / f"{test_name}_project"
    shutil.copytree(project.project_dir.project_directory, copy_dir)
    copy_path_hdf5 = tmp_dir / f"{test_name}.hdf5"
    shutil.copy(project.hdf5.hdf5_path, copy_path_hdf5)
    return Project(copy_path_hdf5, copy_dir)


def test_create_folder(project: Project) -> None:
    folder_name = "test_create_folder"
    project.create_folder(folder_name)
    folder_path = project.project_dir.project_directory / folder_name
    assert folder_path.exists()
    assert folder_name in project.hdf5
