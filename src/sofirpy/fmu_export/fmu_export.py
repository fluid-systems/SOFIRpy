"""This module contains the base class for a fmu export."""

from pathlib import Path

from sofirpy import utils


class FmuExport:
    """Object that sets the paths for the fmu export."""

    def __init__(self, model_path: Path, fmu_path: Path) -> None:
        """Initialize the FmuExport object.

        Args:
            model_path (Path):  Path to the modelica model that
                should be exported.
            fmu_path (Path): Path the exported fmu is going to have.
        """

        self.model_path = model_path
        self.model_directory = model_path.parent
        self.fmu_path = fmu_path

    @property
    def model_path(self) -> Path:
        """Path to the modelica model.

        Returns:
            Path: Path to the modelica model.
        """
        return self._model_path

    @model_path.setter
    def model_path(self, model_path: Path) -> None:
        """Sets the path to the modelica model.

        Args:
            model_path (Path): Path to the modelica model.

        Raises:
            TypeError: model_path type was not 'Path'
            FileNotFoundError: File at model_path doesn't exist
        """

        if not isinstance(model_path, Path):
            raise TypeError(f"'model_path' is {type(model_path)}; expected Path")

        if not model_path.exists():
            raise FileNotFoundError(model_path)

        self._model_path = model_path

    @property
    def fmu_path(self) -> Path:
        """Path the exported fmu is going to have.

        Returns:
            Path: Path the exported fmu is going to have.
        """

        return self._fmu_path

    @fmu_path.setter
    def fmu_path(self, fmu_path: Path) -> None:
        """Sets the path the fmu is going to have.

        Args:
            fmu_path (Path): Path the exported fmu is going to have.

        Raises:
            TypeError: fmu_path type was not 'Path'
            FileExistsError: Fmu at fmu_path already exists before exporting
                the new fmu.
        """

        if not isinstance(fmu_path, Path):
            raise TypeError(f"'fmu_path' is {type(fmu_path)}; expected Path")

        if fmu_path.exists():
            overwrite = utils.get_user_input_for_overwriting(fmu_path, "fmu_path")
            if not overwrite:
                raise FileExistsError(f"Fmu at '{fmu_path}' already exists")
        self._fmu_path = fmu_path

    def move_fmu(self, target_directory: Path) -> None:
        """Move the log fmu to a target directory.

        Args:
            target_directory (Path): Path to the target directory.
        """
        new_fmu_path = target_directory / self.fmu_path.name
        utils.move_file(self.fmu_path, new_fmu_path)
        self._fmu_path = new_fmu_path


class FmuExportError(Exception):
    pass
