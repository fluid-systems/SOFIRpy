"""This module allows to export a OpenModelica model as a fmu."""

from pathlib import Path
from typing import Union
from OMPython import ModelicaSystem
from sofirpy.fmu_export.fmu_export import FmuExport
from sofirpy import utils


class OpenModelicaFmuExport(FmuExport):
    """Object that performs the OpenModelica fmu export"""

    def __init__(self, model_path: Path, model_name: str) -> None:
        """Initialize the OpenModelicaFmuExport object.

        Args:
            model_path (Path): Path to the modelica model that should
                be exported
            model_name (str): Name of the model.
        """

        self.dump_directory = Path.cwd()
        fmu_path = self.dump_directory / f"{model_path.stem}.fmu"
        super().__init__(model_path, fmu_path)
        self.model_name = model_name

        files_to_delete = [
            f"{self.model_name}.c",
            f"{self.model_name}.exe",
            f"{self.model_name}.libs",
            f"{self.model_name}.log",
            f"{self.model_name}.makefile",
            f"{self.model_name}.o",
            f"{self.model_name}_01exo.c",
            f"{self.model_name}_01exo.o",
            f"{self.model_name}_02nls.c",
            f"{self.model_name}_02nls.o",
            f"{self.model_name}_03lsy.c",
            f"{self.model_name}_03lsy.o",
            f"{self.model_name}_04set.c",
            f"{self.model_name}_04set.o",
            f"{self.model_name}_05evt.c",
            f"{self.model_name}_05evt.o",
            f"{self.model_name}_06inz.c",
            f"{self.model_name}_06inz.o",
            f"{self.model_name}_07dly.c",
            f"{self.model_name}_07dly.o",
            f"{self.model_name}_08bnd.c",
            f"{self.model_name}_08bnd.o",
            f"{self.model_name}_09alg.c",
            f"{self.model_name}_09alg.o",
            f"{self.model_name}_10asr.c",
            f"{self.model_name}_10asr.o",
            f"{self.model_name}_11mix.c",
            f"{self.model_name}_11mix.h",
            f"{self.model_name}_11mix.o",
            f"{self.model_name}_12jac.c",
            f"{self.model_name}_12jac.h",
            f"{self.model_name}_12jac.o",
            f"{self.model_name}_13opt.c",
            f"{self.model_name}_13opt.h",
            f"{self.model_name}_13opt.o",
            f"{self.model_name}_14lnz.c",
            f"{self.model_name}_14lnz.o",
            f"{self.model_name}_15syn.c",
            f"{self.model_name}_15syn.o",
            f"{self.model_name}_16dae.c",
            f"{self.model_name}_16dae.h",
            f"{self.model_name}_16dae.o",
            f"{self.model_name}_17inl.c",
            f"{self.model_name}_17inl.o",
            f"{self.model_name}_functions.c",
            f"{self.model_name}_functions.h",
            f"{self.model_name}_functions.o",
            f"{self.model_name}_includes.h",
            f"{self.model_name}_info.json",
            f"{self.model_name}_init.xml",
            f"{self.model_name}_literals.h",
            f"{self.model_name}_model.h",
            f"{self.model_name}_records.c",
            f"{self.model_name}_records.o",
            f"{self.model_name}_FMU.libs",
            f"{self.model_name}_FMU.log",
            f"{self.model_name}_FMU.makefile",
        ]

        self.paths_to_delete = map(
            lambda file_name: self.dump_directory / file_name, files_to_delete
        )

    def export_fmu(self):
        """Exports the model as an fmu."""

        open_modelica = ModelicaSystem(
            str(self.model_path).replace("\\", "//"), self.model_name
        )
        open_modelica.convertMo2Fmu()


def export_open_modelica_model(
    model_path: Union[Path, str], model_name: str, output_directory: Union[Path, str]
) -> Union[OpenModelicaFmuExport, None]:
    """Exports a modelica model as an fmu and moves the fmu to the output directory

    Args:
        model_path (Union[Path, str]): Path to the modelica model that should be exported
        model_name (str): Name of the model.
        output_directory (Union[Path, str]): Path to the output directory.

    Returns:
        OpenModelicaFmuExport: OpenModelicaFmuExport object
    """

    model_path = utils.convert_str_to_path(model_path, "model_path")

    om_fmu_export = OpenModelicaFmuExport(model_path, model_name)
    om_fmu_export.export_fmu()

    # delete unnecessary files
    utils.delete_paths(om_fmu_export.paths_to_delete)

    if om_fmu_export.fmu_path.exists():
        print("The FMU Export was successful.")
        om_fmu_export.move_fmu(output_directory)
        return OpenModelicaFmuExport
    else:
        print("The FMU Export was not successful")
