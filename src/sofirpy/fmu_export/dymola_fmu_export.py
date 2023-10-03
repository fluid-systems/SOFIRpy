"""This module allows to export a Dymola model as a fmu."""
from __future__ import annotations

import re
import subprocess
import tempfile
from html import unescape
from pathlib import Path
from types import TracebackType
from typing import Literal, Optional, Type, Union

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
        model_path: Path,
        model_name: str,
        fmu_name: Optional[str] = None,
        parameters: Optional[dict[str, ParameterValue]] = None,
        model_modifiers: Optional[list[str]] = None,
        packages: Optional[list[Union[str, Path]]] = None,
        output_directory: Optional[Path] = None,
        fmi_version: Literal[1, 2] = 2,
        fmi_type: Literal["me", "cs", "all", "csSolver"] = "all",
        include_source: bool = False,
        include_image: Literal[0, 1, 2] = 2,
    ) -> None:
        """Initialize the DymolaFmuExport object.

        Args:
            model_path (Path): Path to the modelica model that
                should be exported.
            model_name (str): Name of the model that should be exported. If the
                model that should be exported is inside a package, separate the
                package name and the model name with a '.'.
            fmu_name (Optional[str], optional): Name the exported fmu should have. If
                not specified the fmu will have the same name as the model.
                Defaults to None.
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
                need to be loaded as dependencies for the model. Defaults to None.
            output_directory (Optional[Path], optional): Output directory for the fmu,
                the log and the mos script. Defaults to None.
            fmi_version (Literal[1, 2], optional): FMI version, 1 or 2. Defaults to 2.
            fmi_type (Literal["me", "cs", "all", "csSolver"], optional): FMI type,
                me (model exchange), cs (co-simulation), all or csSolver (using Dymola
                solver). Defaults to "all".
            include_source (bool, optional): Whether to include source code in FMU.
                Defaults to False.
            include_image (Literal[0, 1, 2], optional): Whether to include the model
                image (0 - no image, 1 icon, 2 diagram). Defaults to 2.
        """
        self.model_name = model_name
        if fmu_name is None:
            fmu_name = self.model_name
        self.fmu_name = fmu_name
        self._dump_directory = Path(tempfile.mkdtemp())
        fmu_path = model_path.parent / f"{self.fmu_name}.fmu"

        super().__init__(model_path, fmu_path, output_directory)

        self.mos_file_path = (
            self._dump_directory / f"export_script_{self.model_name}.mos"
        )
        self.simulator_log_path = self._dump_directory / f"log_{self.model_name}.txt"
        self.error_log_path = self._dump_directory / f"errors_{self.model_name}.txt"

        if parameters is None:
            parameters = {}
        self.parameters = parameters

        if model_modifiers is None:
            model_modifiers = []
        self.model_modifiers = model_modifiers

        if packages is None:
            packages = []

        # converts strings to path if paths are given as a string
        self.packages = [
            utils.convert_str_to_path(path, "package_path") for path in packages
        ]

        self._paths_to_delete = [
            self.model_directory / name for name in self.files_to_delete
        ]

        self.fmi_version = fmi_version
        self.fmi_type = fmi_type
        self.include_source = "true" if include_source else "false"
        self.include_image = include_image

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

        self._model_modifiers = [
            re.sub(" +", " ", elm.strip()) for elm in model_modifiers
        ]

    def export_fmu(
        self,
        dymola_exe_path: Path,
    ) -> bool:
        """Execute commands to export a fmu.

        Args:
            dymola_exe_path (Path): Path to the dymola executable.
            export_simulator_log (bool, optional): If True a simulator log file
                will be generated. Defaults to True.
            export_error_log (bool, optional): If True a error log file will be
                generated. Defaults to True.

        Returns:
            bool: True if export is successful else False
        """
        if not dymola_exe_path.exists():
            raise FileNotFoundError(f"{dymola_exe_path} does not exit")

        if not self.mos_file_path.exists():
            raise FileNotFoundError(f"{self.mos_file_path} does not exit")

        cmd = [str(dymola_exe_path), str(self.mos_file_path), "/nowindow"]

        with subprocess.Popen(cmd) as process:
            process.wait()

        if self.fmu_path.exists():
            return True
        return False

    def write_mos_script(
        self,
        export_simulator_log: bool = True,
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
        log_path_str = str(self.simulator_log_path).replace("\\", "/")
        error_path_str = str(self.error_log_path).replace("\\", "/")

        mos_script = f'cd("{model_dir_str}");\n'

        if self.packages:
            for package in self.packages:
                package_path_str = str(package).replace("\\", "/")
                mos_script += f'openModel("{package_path_str}")\n'
        mos_script += f'openModel("{model_path_str}");\n'
        mos_script += f'modelInstance = "{self.model_name}(' + input_par + ')";\n'
        mos_script += (
            "translateModelFMU("
            "modelInstance, "
            "false, "
            f'"{self.fmu_name}", '
            f'"{self.fmi_version}", '
            f'"{self.fmi_type}", '
            f"{self.include_source}, "
            f"{self.include_image}"
            ");\n"
        )
        if export_simulator_log:
            mos_script += f'savelog("{log_path_str}");\n'

        mos_script += "errors = getLastError();\n"
        mos_script += f'Modelica.Utilities.Streams.print(errors, "{error_path_str}");\n'
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

        >>> parameter_declaration = ['Resistor.R =  1',
        ...                          'Resistor.useHeatPort = true']

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

    def move_files_to_output_directory(
        self, export_successful: bool, keep_mos: bool, keep_log: bool
    ) -> None:
        """Move the fmu, the mos script and the log to the output directory.

        Args:
            export_successful (bool): If True fmu will be moved to the output directory.
            keep_mos (bool): If True the mos script is moved to the output directory.
            keep_log (bool): If True the simulator log is moved to the output directory.
        """
        if export_successful:
            self.move_fmu()
        if keep_mos:
            self.move_mos_script()
        if keep_log:
            self.move_log_file()

    def move_mos_script(self) -> None:
        """Move the mos script to the output directory."""
        new_mos_path = self.output_directory / self.mos_file_path.name
        utils.move_file(self.mos_file_path, new_mos_path)
        self.mos_file_path = new_mos_path

    def move_log_file(self) -> None:
        """Move the log file to the output directory."""
        new_log_path = self.output_directory / self.simulator_log_path.name
        utils.move_file(self.simulator_log_path, new_log_path)
        self.simulator_log_path = new_log_path

    def read_dymola_error(self) -> str:
        """Read the Dymola error message.

        Returns:
            str: Dymola error message
        """
        with open(self.error_log_path, "r", encoding="utf-8") as error_log:
            return unescape(error_log.read())

    def __enter__(self) -> DymolaFmuExport:
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        utils.delete_paths(self._paths_to_delete)
        utils.delete_file_or_directory(self._dump_directory)


def export_dymola_model(
    dymola_exe_path: Union[Path, str],
    model_path: Union[Path, str],
    model_name: str,
    fmu_name: str | None = None,
    output_directory: Union[Path, str] | None = None,
    parameters: dict[str, ParameterValue] | None = None,
    model_modifiers: list[str] | None = None,
    packages: list[Union[str, Path]] | None = None,
    fmi_version: Literal[1, 2] = 2,
    fmi_type: Literal["me", "cs", "all", "csSolver"] = "all",
    include_source: bool = False,
    include_image: Literal[0, 1, 2] = 2,
    keep_log: bool = False,
    keep_mos: bool = False,
) -> Path:
    """Export a dymola model as a fmu.

    Args:
        dymola_exe_path (Union[Path, str]):  Path to the dymola executable.
        model_path (Union[Path, str]): Path to the dymola model that should be
            exported.
        model_name (str): Name of the model that should be exported. If the
            model that should be exported is inside a package, separate the
            package name and the model name with a '.'.
        fmu_name (Optional[str], optional): Name the exported fmu should have. If not
            specified the fmu will have the same name as the model. Defaults to None.
        output_directory (Union[Path, str]): Output directory for the fmu, the log and
            the mos script. Defaults to None.
        parameters (dict[str, ParameterValue], optional):
            Dictionary of parameter names and values.
            Example:

            >>> parameters = {"Resistor.R" : "1", "Resistor.useHeatPort": True}

            Defaults to None.
        model_modifiers (list[str]], optional): List of model modifiers.
            Example:

            >>> model_modifiers = ["redeclare package Medium ="
            ...     "Modelica.Media.Water.ConstantPropertyLiquidWater"]

            Defaults to None.
        packages (Optional[list[Union[str, Path]]], optional): List of
            model/package paths that need to be loaded as dependencies for the
            model.
        fmi_version (Literal[1, 2], optional): FMI version, 1 or 2. Defaults to 2.
        fmi_type (Literal["me", "cs", "all", "csSolver"], optional): FMI type,
            me (model exchange), cs (co-simulation), all or
            csSolver (using Dymola solver). Defaults to "all".
        include_source (bool, optional): Whether to include source code in FMU.
            Defaults to False.
        include_image (Literal[0, 1, 2], optional): Whether to include the model image
            (0 - no image, 1 icon, 2 diagram). Defaults to 2.
        keep_log (bool, optional): If True the simulator log is kept
            else it will be deleted. Defaults to False.
        keep_mos (bool, optional): If True the mos script is kept
            else it will be deleted. Defaults to False.

    Returns:
        Path: Path to the exported FMU.
    """
    dymola_exe_path = utils.convert_str_to_path(dymola_exe_path, "dymola_exe_path")
    model_path = utils.convert_str_to_path(model_path, "model_path")
    if output_directory is not None:
        output_directory = utils.convert_str_to_path(
            output_directory, "output_directory"
        )
    _validate_fmu_export_settings(fmi_version, fmi_type, include_source, include_image)

    with DymolaFmuExport(
        model_path,
        model_name,
        fmu_name,
        parameters,
        model_modifiers,
        packages,
        output_directory,
        fmi_version,
        fmi_type,
        include_source,
        include_image,
    ) as dymola_exporter:
        mos_script = dymola_exporter.write_mos_script(export_simulator_log=keep_log)
        dymola_exporter.create_mos_file(mos_script)
        successful = dymola_exporter.export_fmu(dymola_exe_path)
        dymola_exporter.move_files_to_output_directory(successful, keep_mos, keep_log)
        if not successful:
            err = dymola_exporter.read_dymola_error()
            raise FmuExportError(
                f"Fmu export was not successful.\nDymola error message:\n{err}\n"
            )
        return dymola_exporter.fmu_path


def _validate_fmu_export_settings(
    fmi_version: Literal[1, 2],
    fmi_type: Literal["me", "cs", "all", "csSolver"],
    include_source: bool,
    include_image: Literal[0, 1, 2],
) -> None:
    if fmi_version not in [1, 2]:
        raise ValueError(f"'fmi_version' is {fmi_version}; expected 1 or 2")
    if fmi_type not in ["me", "cs", "all", "csSolver"]:
        raise ValueError(
            f"'fmi_type' is {fmi_type}; expected 'me', 'cs', 'all' or 'csSolver'"
        )
    utils.check_type(include_source, "include_source", bool)
    if include_image not in [1, 2]:
        raise ValueError(f"'include_image' is {include_image}; expected 0, 1 or 2")
