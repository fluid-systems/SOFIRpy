"""This module allows to export a Dymola model as a fmu."""

import re
import subprocess
from datetime import datetime
from html import unescape
from pathlib import Path
from typing import Optional, Union

from sofirpy import utils
from sofirpy.fmu_export.fmu_export import FmuExport, FmuExportError

ParameterValue = Union[str, int, float, list[Union[int, float, str, bool]], bool]


class DymolaFmuExport(FmuExport):
    """Object that performs the Dymola fmu export."""

    files_to_delete = [
        "dslog.txt",
        "fmiModelIdentifier.h",
        "dsmodel.c",
        "buildlog.txt",
        "dsmodel_fmuconf.h",
        "~FMUOutput",
        "dsin.txt",
    ]

    def __init__(
        self,
        dymola_exe_path: Path,
        model_path: Path,
        model_name: str,
        parameters: Optional[dict[str, ParameterValue]] = None,
        model_modifiers: Optional[list[str]] = None,
        packages: Optional[list[Union[str, Path]]] = None,
    ) -> None:
        """Initialize the DymolaFmuExport object.

        Args:
            dymola_exe_path (Path): Path to the dymola executable.
            model_path (Path): Path to the modelica model that
                should be exported.
            model_name (str): Name of the model that should be exported. If the
                model that should be exported is inside a package, separate the
                package name and the model name with a '.'.
            parameters (dict[str, ParameterValue], optional):
                Dictionary of parameter names and values.
                Example:

                >>> parameters = {"Resistor.R" : "1",
                ...     "Resistor.useHeatPort": True}

                Defaults to None.
            model_modifiers (list[str]], optional): List of model modifiers.
                Example:

                >>> model_modifiers = [
                ...     "redeclare package Medium = "
                ...     "Modelica.Media.Water.ConstantPropertyLiquidWater"
                ... ]

                Defaults to None.
            packages (list[str], optional): List of model/package paths that
                need to be loaded as dependencies for the model.
        """

        self.model_name = model_name
        self._dump_directory = model_path.parent
        fmu_name = self.model_name.replace("_", "_0").replace(".", "_")
        fmu_path = self._dump_directory / f"{fmu_name}.fmu"

        super().__init__(model_path, fmu_path)

        self._dymola_exe_path = dymola_exe_path

        # add a time stamp to the mos file and log files
        time_stamp = datetime.now().strftime("%y%m%d%H%M%S")
        self.mos_file_path = (
            self.model_directory / f"export_script_{self.model_name}_{time_stamp}.mos"
        )
        self._simulator_log_path = (
            self.model_directory / f"log_{self.model_name}_{time_stamp}.txt"
        )
        self.error_log_path = (
            self.model_directory / f"errors_{self.model_name}_{time_stamp}.txt"
        )

        if parameters is None:
            parameters = {}
        self.parameters = parameters

        if model_modifiers is None:
            model_modifiers = []
        self.model_modifiers = model_modifiers

        if packages is None:
            packages = []

        # converts paths to strings if paths are given as Path object
        self._packages = [
            utils.convert_str_to_path(path, "package_path") for path in packages
        ]

        self.paths_to_delete = [
            self.model_directory / name for name in self.files_to_delete
        ]

    @property
    def dymola_exe_path(self) -> Path:
        """Path to the dymola executable.

        Returns:
            Path: Path to the dymola executable
        """
        return self._dymola_exe_path

    @dymola_exe_path.setter
    def dymola_exe_path(self, dymola_exe_path: Path) -> None:
        """Set the Path to the dymola executable.

        Args:
            dymola_exe_path (Path): Path to the dymola executable.

        Raises:
            TypeError: dymola_exe_path type was not 'Path'
            ValueError: File at dymola_exe_path doesn't exist
        """
        _dymola_exe_path = utils.convert_str_to_path(dymola_exe_path, "dymola_exe_path")

        if not _dymola_exe_path.exists():
            raise ValueError(f"{_dymola_exe_path} does not exit")
        self._dymola_exe_path = dymola_exe_path

    @property
    def model_name(self) -> str:
        """Name of the model.

        Returns:
            str: Name of the model.
        """
        return self._model_name

    @model_name.setter
    def model_name(self, model_name: str) -> None:
        """Name of the model.

        Args:
            model_name (str): Name of the model.

        Raises:
            TypeError: type of model_name was invalid
        """
        utils.check_type(model_name, "model_name", str)
        self._model_name = model_name

    @property
    def parameters(self) -> dict[str, ParameterValue]:
        """Dictionary of parameter names and values.

        Returns:
            dict[str, ParameterValue]: Dictionary of
            parameter names and values
        """
        return self._parameters

    @parameters.setter
    def parameters(self, parameters: dict[str, ParameterValue]) -> None:
        """Set dictionary of parameter names and values.

        Args:
            parameters (dict[str, ParameterValue]):
                Dictionary of parameter names and values

        Raises:
            TypeError: 'parameters' type was not 'dict'
            TypeError: type of key in dictionary was not 'str'
            TypeError: type of value in dictionary was not
                'str', 'int', 'bool', 'float', 'list'
        """
        utils.check_type(parameters, "parameters", dict)

        self._parameters = {}
        for com_sym, value in parameters.items():
            utils.check_type(com_sym, "key of parameters", str)
            utils.check_type(
                value, "value of parameters", (str, int, bool, float, list)
            )
            self._parameters[com_sym] = value

    @property
    def model_modifiers(self) -> list[str]:
        """List of model modifiers.

        Returns:
            list[str]: List of model modifiers.
        """
        return self._model_modifiers

    @model_modifiers.setter
    def model_modifiers(self, model_modifiers: list[str]) -> None:
        """Set list of model modifiers.

        Args:
            model_modifiers (list[str]): List of model modifiers.

        Raises:
            TypeError: 'model_modifiers' type was not 'list'
            TypeError: type of element in 'model_modifiers' was not 'str'
        """
        utils.check_type(model_modifiers, "model_modifier", list)
        for modifier in model_modifiers:
            utils.check_type(modifier, "element in 'model_modifier'", str)

        self._model_modifiers = list(
            map(lambda elm: re.sub(" +", " ", elm.strip()), model_modifiers)
        )

    def export_fmu(
        self,
        export_simulator_log: bool = True,
        export_error_log: bool = True,
    ) -> None:
        """Execute commands to export a fmu.

        Args:
            export_simulator_log (bool, optional): If True a simulator log file
                will be generated. Defaults to True.
            export_error_log (bool, optional): If True a error log file will be
                generated. Defaults to True.
        """
        mos_script = self.write_mos_script(export_simulator_log, export_error_log)
        self.create_mos_file(mos_script)

        cmd = [str(self._dymola_exe_path), str(self.mos_file_path), "/nowindow"]

        with subprocess.Popen(cmd) as process:
            process.wait()

    def write_mos_script(
        self,
        export_simulator_log: bool = True,
        export_error_log: bool = True,
    ) -> str:
        """Write the content for the mos file/script.

        The script contains the necessary instructions to import the specified
        parameters and model modifiers and export the model as a fmu.

        Args:
            export_simulator_log (bool, optional): If True a simulator log file
                will be generated. Defaults to True.
            export_error_log (bool, optional): If True a error log file will be
                generated. Defaults to True.

        Returns:
            str: content for the mos script
        """
        parameters = self.format_parameters()
        input_par = ", ".join(parameters + self.model_modifiers)

        model_dir_str = str(self.model_directory).replace("\\", "/")
        model_path_str = str(self.model_path).replace("\\", "/")
        log_path_str = str(self._simulator_log_path).replace("\\", "/")

        mos_script = f'cd("{model_dir_str}");\n'

        if self._packages:
            for package in self._packages:
                package_path_str = str(package).replace("\\", "/")
                mos_script += f'openModel("{package_path_str}")\n'
        mos_script += f'openModel("{model_path_str}");\n'
        mos_script += f'modelInstance = "{self.model_name}(' + input_par + ')";\n'
        mos_script += (
            'translateModelFMU(modelInstance, false, "", "2", "all", false, 2);\n'
        )
        if export_simulator_log:
            mos_script += f'savelog("{log_path_str}");\n'
        if export_error_log:
            mos_script += "errors = getLastError();\n"
            mos_script += (
                f'Modelica.Utilities.Files.removeFile("{self.error_log_path.name}");\n'
            )
            mos_script += "Modelica.Utilities.Streams.print"
            mos_script += f'(errors, "{self.error_log_path.name}");\n'
        mos_script += "Modelica.Utilities.System.exit();"

        return mos_script

    def create_mos_file(self, mos_script: str) -> None:
        """Create the mos file with the specified content.

        Args:
            mos_script (str): The content for the mos file.
        """
        with open(str(self.mos_file_path), mode="w", encoding="utf-8") as mos_file:
            mos_file.write(mos_script)

    def format_parameters(self) -> list[str]:
        """Format parameter values.

        Format parameter values to adjust to dymola scripting syntax and
        stores the parameter names and values in a list in the following format.

        >>> parameter_declaration = ['"Resistor.R" =  "1"',
        ...                          '"Resistor.useHeatPort" = "true"']

        Returns:
            list[str]: List of parameters.
        """

        def convert_to_modelica_value(value: ParameterValue) -> str:
            if isinstance(value, str):
                return value
            if isinstance(value, bool):
                return "true" if value else "false"
            if isinstance(value, (int, float)):
                return str(value)
            if isinstance(value, list):
                return (
                    "{"
                    + ", ".join(convert_to_modelica_value(element) for element in value)
                    + "}"
                )
            raise TypeError(
                f"value is {type(value)}; expected str, bool, float, int, list"
            )

        parameter_declaration = []
        for parameter_name, parameter_value in self.parameters.items():
            parameter_value = convert_to_modelica_value(parameter_value)
            parameter_declaration.append(f"{parameter_name} = {parameter_value}")

        return parameter_declaration

    def move_mos_script(self, target_directory: Path) -> None:
        """Move the mos script to a target directory.

        Args:
            target_directory (Path): Path to the target directory.
        """
        new_mos_path = target_directory / self.mos_file_path.name
        utils.move_file(self.mos_file_path, new_mos_path)
        self.mos_file_path = new_mos_path

    def move_log_file(self, target_directory: Path) -> None:
        """Move the log file to a target directory.

        Args:
            target_directory (Path): Path to the target directory.
        """
        new_log_path = target_directory / self._simulator_log_path.name
        utils.move_file(self._simulator_log_path, new_log_path)
        self._simulator_log_path = new_log_path


def export_dymola_model(
    dymola_exe_path: Union[Path, str],
    model_path: Union[Path, str],
    model_name: str,
    output_directory: Union[Path, str],
    parameters: Optional[dict[str, ParameterValue]] = None,
    model_modifiers: Optional[list[str]] = None,
    packages: Optional[list[Union[str, Path]]] = None,
    keep_log: bool = True,
    keep_mos: bool = True,
) -> Path:
    """Export a dymola model as a fmu.

    Args:
        dymola_exe_path (Union[Path, str]):  Path to the dymola executable.
        model_path (Union[Path, str]): Path to the dymola model that should be
            exported.
        model_name (str): Name of the model that should be exported. If the
            model that should be exported is inside a package, separate the
            package name and the model name with a '.'.
        output_directory (Union[Path, str]): Path to the output directory.
        parameters (dict[str, ParameterValue], optional):
            Dictionary of parameter names and values.
            Example:

            >>> parameters = {"Resistor.R" : "1", "Resistor.useHeatPort": True}

                                Defaults to None.
        model_modifiers (list[str]], optional): List of model modifiers.
            Example

            >>> model_modifiers = ["redeclare package Medium ="
            ...     "Modelica.Media.Water.ConstantPropertyLiquidWater"]

            Defaults to None.
        packages (Optional[list[Union[str, Path]]], optional): List of
            model/package paths that need to be loaded as dependencies for the
            model.
        keep_log (bool, optional): If True the simulator log is kept
            else it will be deleted. Defaults to True.
        keep_mos (bool, optional): If True the mos script is kept
            else it will be deleted. Defaults to True.

    Returns:
        Path: Path to the exported FMU.
    """

    _dymola_exe_path = utils.convert_str_to_path(dymola_exe_path, "dymola_exe_path")
    _model_path = utils.convert_str_to_path(model_path, "model_path")

    dymola_fmu_export = DymolaFmuExport(
        _dymola_exe_path, _model_path, model_name, parameters, model_modifiers, packages
    )

    _output_directory = utils.convert_str_to_path(output_directory, "output_directory")

    dymola_fmu_export.export_fmu(keep_log)

    # delete unnecessary files
    utils.delete_paths(dymola_fmu_export.paths_to_delete)

    if not keep_mos:
        dymola_fmu_export.mos_file_path.unlink()

    if not dymola_fmu_export.fmu_path.exists():
        with open(dymola_fmu_export.error_log_path, "r", encoding="utf-8") as error_log:
            err = unescape(error_log.read())
        dymola_fmu_export.error_log_path.unlink()
        raise FmuExportError(
            f"Fmu export was not successful. \nDymola error message: {err} \n"
        )

    dymola_fmu_export.error_log_path.unlink()
    dymola_fmu_export.move_fmu(_output_directory)
    if keep_mos:
        dymola_fmu_export.move_mos_script(_output_directory)
    if keep_log:
        dymola_fmu_export.move_log_file(_output_directory)
    return dymola_fmu_export.fmu_path
