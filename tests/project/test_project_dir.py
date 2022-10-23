import shutil
import tempfile
from pathlib import Path

import pytest

from sofirpy import ProjectDir


@pytest.fixture
def tmp_dir() -> tempfile.TemporaryDirectory:
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def project_dir() -> ProjectDir:

    directory = Path(__file__).parent / "test_project_dir"
    _project_dir = ProjectDir(directory)
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield _copy_standard_project_dir(
            _project_dir, "test_project_dir", Path(tmp_dir)
        )


def _copy_standard_project_dir(
    project_dir: ProjectDir, test_name: str, dir_path: Path
) -> ProjectDir:
    copy_path = dir_path / f"{test_name}_project_dir"
    shutil.copytree(project_dir.project_directory, copy_path)
    return ProjectDir(copy_path)


def test_init(project_dir: ProjectDir) -> None:
    assert project_dir.current_folder_path == project_dir.project_directory


def test_dir_setter_exception() -> None:
    path = Path(__file__)
    with pytest.raises(NotADirectoryError):
        ProjectDir(path)


def test_set_current_folder_exception(project_dir: ProjectDir) -> None:

    with pytest.raises(TypeError):
        project_dir.current_folder = None


def test_create_folder(project_dir: ProjectDir) -> None:

    folder_name = "test_create_folder"
    project_dir.create_folder(folder_name)
    folder_path = project_dir.project_directory / folder_name
    assert folder_path.exists()
    assert project_dir.current_folder_path == folder_path
    assert project_dir.current_folder == folder_name


def test_create_folder_exception(project_dir: ProjectDir) -> None:

    with pytest.raises(FileExistsError):
        project_dir.create_folder("test_create_folder_exception")


def test_delete_element(project_dir: ProjectDir) -> None:

    file_rel_path = "test_delete_element/test.txt"
    project_dir.delete_element(file_rel_path)
    assert not (project_dir.project_directory / file_rel_path).exists()
    folder_rel_path = "test_delete_element"
    project_dir.delete_element(folder_rel_path)
    assert not (project_dir.project_directory / folder_rel_path).exists()


def test_delete_folder(project_dir: ProjectDir) -> None:

    project_dir.current_folder = "test_delete_folder"
    project_dir.delete_folder("test_delete_folder")
    folder_path = project_dir.project_directory / "test_delete_folder"
    assert not folder_path.exists()
    assert project_dir.current_folder == "."


def test_delete_files(project_dir: ProjectDir) -> None:

    project_dir.current_folder = "test_delete_files"
    project_dir.delete_files(["test1.txt", "test2.txt"])
    assert not (project_dir.current_folder_path / "test1.txt").exists()
    assert not (project_dir.current_folder_path / "test2.txt").exists()


def test_rename_file(project_dir: ProjectDir) -> None:

    file_path = project_dir.project_directory / "test_rename_file.txt"
    new_name = "new_name"
    new_file_path = project_dir.rename_file(file_path, new_name)
    assert new_file_path.exists()
    assert new_file_path == project_dir.project_directory / "new_name.txt"
    assert not file_path.exists()


def test_move_file(project_dir: ProjectDir) -> None:

    source_path = project_dir.project_directory / "test_move_file.txt"
    target_directory = project_dir.project_directory / "test_move_file"
    target_path = project_dir.move_file(source_path, target_directory)
    assert target_path.exists()
    assert target_path == target_directory / "test_move_file.txt"
    assert not source_path.exists()


def test_move_files(project_dir: ProjectDir) -> None:

    source_directory = project_dir.project_directory / "test_move_files"
    source_paths = [source_directory / f"file{i}.txt" for i in range(1, 4)]
    target_directory = project_dir.project_directory
    target_paths = project_dir.move_files(source_paths, target_directory)
    for i, path in enumerate(target_paths, start=1):
        assert path.exists()
        assert path == target_directory / f"file{i}.txt"
    for path in source_paths:
        assert not path.exists()


def test_move_and_rename_file(project_dir: ProjectDir) -> None:

    source_path = project_dir.project_directory / "test_move_and_rename_file.txt"
    target_directory = project_dir.project_directory / "test_move_and_rename_file"
    new_name = "new_name"
    target_path = project_dir.move_and_rename_file(
        source_path, target_directory, new_name
    )
    assert target_path.exists()
    assert target_path == target_directory / "new_name.txt"
    assert not source_path.exists()


def test_copy_file(project_dir: ProjectDir) -> None:

    source_path = project_dir.project_directory / "test_copy_file.txt"
    target_directory = project_dir.project_directory / "test_copy_file"
    target_path = project_dir.copy_file(source_path, target_directory)
    assert target_path.exists()
    assert target_path == target_directory / "test_copy_file.txt"
    assert source_path.exists()


def test_copy_and_rename_file(project_dir: ProjectDir) -> None:

    source_path = project_dir.project_directory / "test_copy_and_rename_file.txt"
    target_directory = project_dir.project_directory / "test_copy_and_rename_file"
    new_name = "new_name"
    target_path = project_dir.copy_and_rename_file(
        source_path, target_directory, new_name
    )
    assert target_path.exists()
    assert target_path == target_directory / "new_name.txt"
    assert source_path.exists()