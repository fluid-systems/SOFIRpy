"""This module allows to export a OpenModelica model as a fmu."""
from __future__ import annotations

from pathlib import Path
from types import TracebackType
from typing import Optional, Type, Union

from OMPython import ModelicaSystem

from sofirpy import utils
from sofirpy.fmu_export.fmu_export import FmuExport, FmuExportError


class OpenModelicaFmuExport(FmuExport):
    """Object that performs the OpenModelica fmu export"""

    files_to_delete = [
        ".c",
        ".exe",
        ".libs",
        ".log",
        ".makefile",
        ".o",
        "_01exo.c",
        "_01exo.o",
        "_02nls.c",
        "_02nls.o",
        "_03lsy.c",
        "_03lsy.o",
        "_04set.c",
        "_04set.o",
        "_05evt.c",
        "_05evt.o",
        "_06inz.c",
        "_06inz.o",
        "_07dly.c",
        "_07dly.o",
        "_08bnd.c",
        "_08bnd.o",
        "_09alg.c",
        "_09alg.o",
        "_10asr.c",
        "_10asr.o",
        "_11mix.c",
        "_11mix.h",
        "_11mix.o",
        "_12jac.c",
        "_12jac.h",
        "_12jac.o",
        "_13opt.c",
        "_13opt.h",
        "_13opt.o",
        "_14lnz.c",
        "_14lnz.o",
        "_15syn.c",
        "_15syn.o",
        "_16dae.c",
        "_16dae.h",
        "_16dae.o",
        "_17inl.c",
        "_17inl.o",
        "_functions.c",
        "_functions.h",
        "_functions.o",
        "_includes.h",
        "_info.json",
        "_init.xml",
        "_literals.h",
        "_model.h",
        "_records.c",
        "_records.o",
        "_FMU.libs",
        "_FMU.log",
        "_FMU.makefile",
    ]

    def __init__(
        self, model_path: Path, model_name: str, output_directory: Optional[Path] = None
    ) -> None:
        """Initialize the OpenModelicaFmuExport object.

        Args:
            model_path (Path): Path to the modelica model that should
                be exported
            model_name (str): Name of the model.
            output_directory (Optional[Path], optional): Output directory for the fmu.
        """

        self._dump_directory = Path.cwd()
        fmu_path = self._dump_directory / f"{model_path.stem}.fmu"
        super().__init__(model_path, fmu_path, output_directory)
        self.model_name = model_name

        files_to_delete = [
            f"{self.model_name}{file_name}" for file_name in self.files_to_delete
        ]
        self._paths_to_delete = [
            self._dump_directory / file_name for file_name in files_to_delete
        ]

    def export_fmu(self) -> bool:
        """Exports the model as an fmu.

        Returns:
            bool: True if export is successful else False
        """
        open_modelica = ModelicaSystem(
            str(self.model_path).replace("\\", "//"), self.model_name
        )
        open_modelica.convertMo2Fmu()

        if self.fmu_path.exists():
            return True
        return False

    def __enter__(self) -> OpenModelicaFmuExport:
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        utils.delete_paths(self._paths_to_delete)


def export_open_modelica_model(
    model_path: Union[Path, str], model_name: str, output_directory: Union[Path, str]
) -> Path:
    """Exports a modelica model as an fmu and moves the fmu to the output directory

    Args:
        model_path (Union[Path, str]): Path to the modelica model that should be
            exported.
        model_name (str): Name of the model.
        output_directory (Union[Path, str]): Output directory for the fmu.

    Returns:
        Path: Path to the exported FMU.
    """
    _model_path = utils.convert_str_to_path(model_path, "model_path")
    _output_directory = utils.convert_str_to_path(output_directory, "output_directory")

    with OpenModelicaFmuExport(
        _model_path, model_name, _output_directory
    ) as om_exporter:
        successful = om_exporter.export_fmu()
        if not successful:
            raise FmuExportError("FMU export was not successful.")
        om_exporter.move_fmu()
        return om_exporter.fmu_path
