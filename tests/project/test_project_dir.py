import shutil
from pathlib import Path
import pytest
from sofirpy import ProjectDir


@pytest.fixture
def project_dir() -> ProjectDir:
    directory = Path(__file__).parent / "test_project_dir"
    return ProjectDir(directory)


def test_init(project_dir: ProjectDir) -> None:
    assert project_dir.current_folder_path == project_dir.project_directory


def _copy_standard_project_dir(project_dir: ProjectDir, test_name: str) -> ProjectDir:
    copy_path = project_dir.project_directory.parent / f"{test_name}_project_dir"
    shutil.copytree(project_dir.project_directory, copy_path)
    return ProjectDir(copy_path)


def test_dir_setter_creation() -> None:
    directory = Path(__file__).parent / "test_dir_setter_creation"
    if directory.exists():
        directory.rmdir()
    project_dir = ProjectDir(directory)
    assert directory.exists()
    project_dir.project_directory.rmdir()
    project_dir.project_directory = (
        Path(__file__).parent / "test_dir_setter_creation/test"
    )
    assert directory.exists()
    shutil.rmtree(project_dir.project_directory.parent, ignore_errors=True)


def test_dir_setter_exception() -> None:
    path = Path(__file__)
    with pytest.raises(NotADirectoryError):
        ProjectDir(path)


def test_set_current_folder_exception(project_dir: ProjectDir) -> None:

    with pytest.raises(TypeError):
        project_dir.current_folder = None


def test_create_folder(project_dir: ProjectDir) -> None:

    project_dir = _copy_standard_project_dir(project_dir, "test_create_folder")
    folder_name = "test_create_folder"
    project_dir.create_folder(folder_name)
    folder_path = project_dir.project_directory / folder_name
    assert folder_path.exists()
    assert project_dir.current_folder_path == folder_path
    assert project_dir.current_folder == folder_name
    shutil.rmtree(project_dir.project_directory, ignore_errors=True)


def test_create_folder_exception(project_dir: ProjectDir) -> None:

    with pytest.raises(FileExistsError):
        project_dir.create_folder("test_create_folder_exception")


def test_delete_element(project_dir: ProjectDir) -> None:

    project_dir = _copy_standard_project_dir(project_dir, "test_delete_element")
    file_rel_path = "test_delete_element/test.txt"
    project_dir.delete_element(file_rel_path)
    assert not (project_dir.project_directory / file_rel_path).exists()
    folder_rel_path = "test_delete_element"
    project_dir.delete_element(folder_rel_path)
    assert not (project_dir.project_directory / folder_rel_path).exists()
    shutil.rmtree(project_dir.project_directory, ignore_errors=True)


def test_delete_files(project_dir: ProjectDir) -> None:

    project_dir = _copy_standard_project_dir(project_dir, "test_delete_files")
    project_dir.current_folder = "test_delete_files"
    project_dir.delete_files(["test1.txt", "test2.txt"])
    assert not (project_dir.current_folder_path / "test1.txt").exists()
    assert not (project_dir.current_folder_path / "test2.txt").exists()
    shutil.rmtree(project_dir.project_directory, ignore_errors=True)


# def test_move_file(project_dir: ProjectDir) -> None:

#     project_dir = _copy_standard_project_dir(project_dir, "test_move_file")
#     source_path = Path(__file__).parent / "test_move_file_project_dir"
#     project_dir.current_folder = "test_move_file"
#     project_dir.move_file(source_path)
#     project_dir.current_folder_path /